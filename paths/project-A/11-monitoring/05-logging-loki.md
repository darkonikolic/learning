# 05 — Logging sa Loki

## Teorija

Loki je log agregacijski sistem dizajniran da radi zajedno s Grafanom,
na isti način kao Prometheus. Slogan: **"Like Prometheus, but for logs"**.
Ne indeksira sadržaj logova — indeksira samo labele. Zbog toga je jeftiniji
od Elasticsearcha, ali brz za uobičajene upite.

---

## Zašto Loki, ne samo kubectl logs

`kubectl logs` prikazuje logove jednog Poda, u realnom vremenu ili zadnjih N linija.
Problem:

- Pod se restartuje → stari logovi su izgubljeni (novi kontejner, novi logovi)
- Imaš 3 replika helloworld Poda — trebaš ručno gledat svaki
- Ne možeš pretraživati historiju starijeg od tekućeg kontejner lifetimea
- Ne možeš korelirati logs s metrics (u istom UI)

Loki sakuplja logove sa **svih Podova**, **svih namespacea**, **sve historije**
i čuva ih centralizovano. Pretraga je kroz Grafana UI.

---

## Arhitektura: Promtail + Loki + Grafana

```
K8s Node
├── Pod: nginx      → stdout/stderr
├── Pod: app        → stdout/stderr
│
DaemonSet: Promtail
    ↓ čita /var/log/pods/* (sve logove na node-u)
    ↓ dodaje labele: namespace, pod, container, node
    ↓ šalje u Loki
    ↓
Loki (StatefulSet u monitoring namespace-u)
    ↓ indeksira labele, komprimuje content, čuva na S3/PVC
    ↓
Grafana → Explore → Loki data source
```

**Promtail** je DaemonSet — jedan na svakom K8s node-u. Čita sve kontejner logove
i dodaje K8s metapodatke (koji Pod, koji namespace, koji node).

---

## LogQL: query jezik za logove

LogQL kombinuje label selector (kao Prometheus) s filter izrazima.

### Osnovna pretraga

```logql
# Svi logovi iz helloworld-prod namespacea
{namespace="helloworld-prod"}

# Nginx logovi iz svih helloworld namespacea
{namespace=~"helloworld.*", app="helloworld"}

# Filtriraj linije koje sadrže "ERROR"
{namespace="helloworld-prod"} |= "ERROR"

# Linije koje NE sadrže "health check"
{namespace="helloworld-prod"} != "health check"
```

### Regex filtriranje

```logql
# Nginx 5xx greške
{app="helloworld"} |~ "\" 5[0-9]{2} "

# Specifičan IP adresa
{app="helloworld"} |~ "192\.168\.\d+\.\d+"
```

### JSON parsing

Ako logovi su u JSON formatu:

```logql
# Parse JSON i filtriraj po polju
{app="helloworld"} | json | status >= 500

# Nginx access log u JSON formatu
{app="helloworld"} | json | method="POST" | status != 200
```

### Metrike iz logova (log-based metrics)

```logql
# Broj 5xx grešaka po minuti
sum(rate({app="helloworld"} |~ "\" 5[0-9]{2} "[5m]))

# Error rate po statusu
sum by (status) (
  rate({app="helloworld"} | json | __error__="" [5m])
)
```

---

## Grafana Explore: pretraga logova

Grafana UI → Explore → izaberi Loki data source

Explore omogućuje:
- Pisanje LogQL upita s autocomplete-om
- Prikaz log linija s timestamp-om i labelama
- Expand detalja pojedine log linije
- Zoom na vremenski period s anomalijom

**Ključna features**: u istom Explore prozoru možeš prebacivati između
Prometheus metrics i Loki logs — idealno za istraživanje incidenta.

---

## Nginx access i error logovi → Loki

Nginx kontejner po defaultu šalje logove na stdout/stderr,
što K8s automatski usmjerava na disk (`/var/log/pods/`).

Za bolju parsabilnost, konfiguriši nginx JSON log format:

```nginx
# /etc/nginx/conf.d/log-format.conf
log_format json_combined escape=json
  '{'
    '"time":"$time_iso8601",'
    '"method":"$request_method",'
    '"uri":"$request_uri",'
    '"status":$status,'
    '"bytes":$body_bytes_sent,'
    '"duration":$request_time,'
    '"remote_addr":"$remote_addr"'
  '}';

access_log /dev/stdout json_combined;
error_log  /dev/stderr warn;
```

Loki + JSON format = moćna pretraga bez regex-a:

```logql
# Svi spori zahtjevi (> 1 sekunda)
{app="helloworld"} | json | duration > 1

# 404 greške
{app="helloworld"} | json | status=404
```

---

## CloudWatch alternativa: za AWS-native stack

Umjesto Loki, možeš koristiti **AWS CloudWatch Logs** direktno iz EKS-a:

- EKS Fluent Bit DaemonSet: sakuplja K8s logove, šalje u CloudWatch Log Groups
- Nema self-hosted komponente za upravljanje
- CloudWatch Log Insights za pretragu (vlastiti query jezik)
- Skuplji za visoke volume logova

Za project-A: Loki je preporučen jer:
- Radi identično lokalno (kind) i na cloudu
- Besplatan (open source)
- Grafana integracija je besprijekorna
- Učiš prenosivo znanje (ne vendor lock-in)

---

## Veza sa project-A

Nginx u project-A servira `index.html`. Logovi su jednostavni:
GET /, GET /health, povremeni 404 ako neko traži `/favicon.ico`.

Korisne LogQL pretrage za projekt učenja:

```logql
# Provjeri da li health check radi
{app="helloworld", namespace="helloworld-dev"} |= "/health"

# Svi 404-ovi (možda broken link u Ingress konfiguraciji?)
{app="helloworld"} | json | status=404

# Logovi u zadnja 3 sata (debugging incident)
{namespace="helloworld-prod"} | json | status >= 400
```

Svaki put kad nešto ne radi: Grafana Explore → Loki → namespace filttar → traži greške.
Ovo postaje refleks: metrics kažu "nešto nije u redu", logovi kažu "ovo je zašto".
