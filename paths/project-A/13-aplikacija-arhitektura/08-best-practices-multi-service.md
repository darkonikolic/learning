# 08 — Best practices: multi-service produkcijski patterns

## Communication matrix

Potpuna tablica ko šalje zahtjeve kome, kojim protokolom i na koji port.

| Izvor           | Odredište       | Port | Protokol       | Napomena                            |
|-----------------|-----------------|------|----------------|-------------------------------------|
| Browser/klijent | nginx           | 443  | HTTPS          | TLS terminacija na Ingress-u        |
| nginx           | php-service     | 9000 | FastCGI (TCP)  | Samo `/api/*` lokacije              |
| nginx           | Vue.js fajlovi  | —    | Filesystem     | Statički fajlovi su unutar image-a  |
| php-service     | go-service      | 8080 | HTTP/JSON      | REST pozivi za business logic       |
| php-service     | redis           | 6379 | Redis protocol | Session read/write, rate limit      |
| go-service      | mysql-master    | 3306 | MySQL protocol | Write operacije                     |
| go-service      | mysql-replica   | 3306 | MySQL protocol | Read operacije                      |
| go-service      | redis           | 6379 | Redis protocol | Application cache                   |
| mysql-master    | mysql-replica   | 3306 | MySQL binlog   | Async replikacija                   |

Sve inter-service komunikacije unutar K8s idu po cluster mreži, nema javnog interneta. TLS za interne veze nije obavezan ako je mreža trusted (K8s cluster network) — ali u visoko-osjetljivim okruženjima koristiti mTLS (Istio service mesh).

---

## Container startup order

K8s ne garantuje redoslijed pokretanja pod-ova, čak ni sa `depends_on` ekvivalentom. Ovo se rješava na dva načina koji se koriste zajedno:

**1. Init containers** — blokira start glavnog kontejnera dok uvjet nije ispunjen:

```yaml
initContainers:
  - name: wait-for-mysql
    image: busybox:1.36
    command: ['sh', '-c',
      'until nc -z mysql-master 3306; do
        echo "$(date): waiting for mysql-master:3306";
        sleep 2;
      done;
      echo "mysql-master is accepting connections"']

  - name: wait-for-go-service
    image: curlimages/curl:8.5.0
    command: ['sh', '-c',
      'until curl -sf http://go-service:8080/health; do
        echo "$(date): waiting for go-service";
        sleep 3;
      done']
```

**2. Retry logika u aplikaciji** — Go servis ne treba pucati na prvu grešku konekcije:

```go
func connectWithRetry(dsn string, maxRetries int) (*sql.DB, error) {
    var db *sql.DB
    var err error

    for i := 0; i < maxRetries; i++ {
        db, err = sql.Open("mysql", dsn)
        if err == nil {
            if pingErr := db.Ping(); pingErr == nil {
                return db, nil
            }
        }
        log.Printf("db connect attempt %d/%d failed: %v", i+1, maxRetries, err)
        time.Sleep(time.Duration(i+1) * 2 * time.Second)  // Exponential backoff
    }
    return nil, fmt.Errorf("failed to connect after %d attempts: %w", maxRetries, err)
}
```

Init container + retry logika = defense in depth. Init container hvata očigledne startup order probleme. Retry logika hvata tranzijentne greške (MySQL restartuje za maintenance, mrežni bljesak).

---

## Graceful shutdown svaki servis

K8s šalje `SIGTERM` podu koji treba da se ugasi. Pod ima `terminationGracePeriodSeconds` (default 30s) da završi in-flight zahtjeve. Nakon toga, K8s šalje `SIGKILL`.

**Go servis** — implementacija prikazana u modulu 04:
```go
signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
<-quit
ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
srv.Shutdown(ctx)
```

**PHP-FPM** graceful shutdown: PHP-FPM reaguje na `SIGQUIT` za graceful shutdown (završi in-flight zahtjeve) i `SIGTERM` za brzi shutdown. Docker/K8s šalje SIGTERM — PHP-FPM tretira SIGTERM kao "fast shutdown" koji može prekinuti zahtjeve.

Rješenje: `preStop` hook u K8s Deployment-u da damo PHP-u vremena:

```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 10 && kill -QUIT 1"]
```

**nginx** graceful shutdown: `nginx -s quit` šalje SIGQUIT koji čeka da se zatvore otvorene konekcije. nginx:alpine image ima signal handling ugrađen — `CMD ["nginx", "-g", "daemon off;"]` reaguje ispravno na SIGTERM.

Kritičan detalj: `terminationGracePeriodSeconds` mora biti veći od vremena koje servis treba za graceful shutdown:

```yaml
# Ako PHP treba 10s preStop + 15s za zahtjeve = 25s minimum
terminationGracePeriodSeconds: 35
```

---

## Distributed tracing: X-Request-ID propagacija

Bez tracing-a, debugging multi-service grešaka je "needle in haystack" — log poruka iz Go servisa nema kontekst koji je PHP zahtjev ju je generisao.

Minimalan pristup: X-Request-ID header koji se propagira kroz sve servise.

```
Browser → nginx → PHP → Go
         zahtjev nosi header: X-Request-ID: req-7f3a8b2c-1234-5678

Logovi:
[nginx]       req-7f3a8b2c-1234-5678 GET /api/users/42 → 200 (15ms)
[php-service] req-7f3a8b2c-1234-5678 proxy → go-service GET /users/42
[go-service]  req-7f3a8b2c-1234-5678 SELECT FROM users WHERE id=42 (replica, 3ms)
```

nginx konfiguracija za generisanje UUID ako nije prisutan:
```nginx
# Generiši request ID ako klijent nije poslao
map $http_x_request_id $request_id_safe {
    default $http_x_request_id;
    ""      $request_id;  # nginx $request_id je automatski generirani hex
}

# Proslijedi downstream servisima
proxy_set_header X-Request-ID $request_id_safe;
fastcgi_param HTTP_X_REQUEST_ID $request_id_safe;

# Vrati klijentu za debugging
add_header X-Request-ID $request_id_safe;
```

PHP propagacija na Go servis:
```php
$requestId = $request->getHeaderLine('X-Request-ID');
$response = $httpClient->request('GET', $goServiceUrl . '/users/' . $id, [
    'headers' => ['X-Request-ID' => $requestId]
]);
```

Naredni korak nakon X-Request-ID: OpenTelemetry sa Jaeger ili Tempo. To je pravi distributed tracing (trace spans, parent-child relationships, timing per servis). X-Request-ID je minimum koji se implementira za jedan dan — OpenTelemetry je sedmica rada ali daje punu vidljivost.

---

## Resource limits — realni brojevi po servisu

```yaml
# nginx — statički serving je I/O bound, ne CPU/memory intenzivan
nginx:
  resources:
    requests:
      cpu: 50m       # 0.05 CPU — dovoljno za parsing i serviranje
      memory: 64Mi   # gzip buffer + worker connections
    limits:
      cpu: 200m      # burst za spike saobraćaja
      memory: 128Mi

# php-service — PHP FPM procesi troše memoriju
# pm.max_children=20, svaki proces ~10-15MB = 200-300MB peak
php-service:
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 256Mi

# go-service — niska memorija, dobar CPU utilization
go-service:
  resources:
    requests:
      cpu: 50m
      memory: 64Mi
    limits:
      cpu: 300m
      memory: 128Mi
```

`requests` = garantovani resursi (K8s scheduler postavlja pod samo na node koji ima ove resurse slobodne).
`limits` = maksimum koji kontejner smije koristiti. Prekoračenje CPU = throttling. Prekoračenje memory = OOMKilled.

Postavljanje `limits` previsoko (npr. memory: 4Gi za PHP koji nikad ne koristi više od 300Mi) znači da K8s node može biti "over-committed" — pri opterećenju, nodovi ne mogu ispuniti obećanja. Postavljanje `requests` previsoko = loša bin-packing efikasnost i veći troškovi.

---

## Liveness vs Readiness probe — razlika je kritična

**Liveness probe**: "Da li je ovaj kontejner živ?" — ako ne prođe N puta, K8s restartuje pod.
**Readiness probe**: "Da li je ovaj kontejner spreman primati saobraćaj?" — ako ne prođe, pod se uklanja iz Service load balancera, ali se NE restartuje.

```yaml
# Go servis: readiness čeka MySQL konekciju
readinessProbe:
  httpGet:
    path: /health  # Go /health endpoint provjerava MySQL i Redis
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10
  failureThreshold: 3
  # Pod neće dobijati saobraćaj dok MySQL nije dostupan

livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30  # Duže čekanje — ne restartovati pod odmah
  periodSeconds: 15
  failureThreshold: 3
  # Samo ako servis potpuno ne odgovara, restartovati

# nginx: samo liveness (statički serving ne ovisi o downstream-u)
livenessProbe:
  httpGet:
    path: /nginx-health
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 10
```

Česta greška: koristiti isti endpoint za liveness i readiness, a taj endpoint provjerava downstream zavisnosti (MySQL). Problem: MySQL restart → readiness fail (OK, nginx prestaje slati saobraćaj) ali i liveness fail → K8s restartuje pod koji je potpuno zdrav. Liveness probe treba biti "da li je process živ", readiness "da li su zavisnosti dostupne".

Rješenje: zasebni endpointi:
- `GET /health/live` → uvijek 200 dok je Go process živ
- `GET /health/ready` → 200 samo ako su MySQL i Redis dostupni

---

## Sidecar pattern za log parsing

Aplikacijski log format nije uvijek prikladan za log aggregation sistem (Loki, Elasticsearch). Umjesto mijenjanja aplikacije (Go code change = build + deploy), koristiti sidecar kontejner koji čita logove i transformiše ih.

```yaml
# K8s pod sa sidecar-om za log formatiranje
spec:
  containers:
    - name: go-service
      image: project-a/go-service:latest
      # Log na stdout — Go aplikacija ne treba znati ništa o log sistemu
      # K8s collect logove sa /var/log/pods/...
    
    - name: log-parser
      image: fluent/fluent-bit:3.0
      volumeMounts:
        - name: varlog
          mountPath: /var/log
      env:
        - name: FLUENT_BIT_CONFIG
          value: |
            [INPUT]
              Name tail
              Path /var/log/pods/*go-service*/*.log
            [FILTER]
              Name parser
              Parser json
            [OUTPUT]
              Name loki
              Host loki.monitoring.svc.cluster.local
  
  volumes:
    - name: varlog
      hostPath:
        path: /var/log
```

Sidecar prednost: log formatiranje, filtriranje, enrichment (dodaj namespace, pod name, environment) — sve bez promjene aplikacijskog koda. Tim koji upravlja infrastrukturom može mijenjati log pipeline nezavisno od development tima.

---

## Checklist za produkcijski deployment

```
[ ] Svaki servis ima liveness i readiness probe
[ ] terminationGracePeriodSeconds > maksimalno trajanje graceful shutdown
[ ] Resource requests i limits postavljeni za sve kontejnere
[ ] Secrets dolaze iz External Secrets Operator-a (ne values.yaml)
[ ] .dockerignore postoji za svaki servis (node_modules, .env, .git)
[ ] Multi-stage build za sve Dockerfile-ove (dev deps ne u runtime image)
[ ] Go service ima scratch final image sa CA certifikatima
[ ] nginx.conf ima security headers (X-Frame-Options, X-Content-Type, itd.)
[ ] Cache-Control headers ispravni (immutable za hashed assets, no-cache za index.html)
[ ] X-Request-ID propagiran kroz sve servise
[ ] Health check endpoint provjerava stvarne zavisnosti (ne samo HTTP 200)
[ ] MySQL connection pool sizing je usklađen sa max_connections
[ ] Redis session storage konfigurisan (ne filesystem sessions)
[ ] Rate limiting middleware u PHP servisu
[ ] HPA konfigurisan za Go servis sa realnim CPU target-om
[ ] PodDisruptionBudget za svaki servis (spriječi outage tokom node maintenance)
[ ] Ingress TLS konfigurisan sa cert-manager
[ ] Replication lag awareness u aplikacijskom kodu (read-your-own-writes pattern)
```
