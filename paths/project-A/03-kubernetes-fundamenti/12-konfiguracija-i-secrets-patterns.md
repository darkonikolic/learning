# 12 — Konfiguracija i Secrets Patterns

Kompletni guide za ConfigMap, Secret i konfiguracijske pattern-e za project-A, uključujući External Secrets Operator integraciju.

---

## ConfigMap — četiri načina montiranja

### 1. Sve kao environment varijable odjednom

```yaml
spec:
  containers:
    - name: go-service
      envFrom:
        - configMapRef:
            name: app-config    # sve key-value parovi postaju env varijable
```

**Kada**: generalni app config (LOG_LEVEL, APP_ENV, FEATURE_FLAGS).
**Problem**: svaki ključ u ConfigMap-u postaje env varijabla — može biti previše. Nema granularnu kontrolu.

### 2. Selektivne env varijable

```yaml
env:
  - name: LOG_LEVEL            # ime env varijable u kontejneru
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: log_level         # specifičan ključ iz ConfigMap-a
  - name: APP_PORT
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: port
        optional: true         # ako ključ ne postoji, ne failuj
```

**Kada**: trebaš samo određene vrijednosti, ili chceš preimenovati ključ.

### 3. Kao fajl (volume mount) — za nginx.conf, php.ini, app.yaml

```yaml
spec:
  volumes:
    - name: nginx-config
      configMap:
        name: nginx-conf
        items:
          - key: default.conf       # ključ iz ConfigMap-a
            path: default.conf      # putanja unutar volume-a
  containers:
    - name: nginx
      volumeMounts:
        - name: nginx-config
          mountPath: /etc/nginx/conf.d/    # montira cijeli direktorij
          readOnly: true
```

### 4. Subpath mount — samo jedan fajl, bez zamjene direktorijuma

```yaml
volumes:
  - name: php-ini
    configMap:
      name: php-config
containers:
  - volumeMounts:
      - name: php-ini
        mountPath: /usr/local/etc/php/conf.d/custom.ini  # specifičan fajl
        subPath: custom.ini     # montiraj samo ovaj key, ne cijeli CM
        readOnly: true
```

**Kritična razlika subPath vs bez subPath:**
- Bez `subPath`: zamjeni CIJELI `/usr/local/etc/php/conf.d/` s contentom ConfigMap-a (brišu se drugi fajlovi)
- Sa `subPath`: dodaj samo `custom.ini`, ostali fajlovi u tom direktorijumu ostaju

**Mana subPath-a**: automatski update pri promjeni ConfigMap-a NE radi s subPath. Bez subPath K8s automatski ažurira montirani fajl (uz ~60s kašnjenje). Sa subPath mora restart poda.

---

## nginx ConfigMap za project-A

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-conf
  namespace: project-a-prod
data:
  default.conf: |
    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        # Vue SPA routing — sve što nije statički fajl → index.html
        location / {
            try_files $uri $uri/ /index.html;
            add_header Cache-Control "no-cache";
        }

        # Statički assets s dugim cache-om
        location ~* \.(js|css|png|jpg|ico|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Proxy prema PHP servisu
        location /api/ {
            proxy_pass http://php-service:9000/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Request-ID $request_id;
            proxy_connect_timeout 10s;
            proxy_read_timeout 30s;
        }

        # Proxy prema Go servisu (WebSocket + REST)
        location /ws/ {
            proxy_pass http://go-service:8080/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check endpoint (bez logiranja)
        location /health {
            return 200 "ok\n";
            add_header Content-Type text/plain;
            access_log off;
        }

        # Metrički endpoint (samo interni pristup)
        location /nginx-status {
            stub_status;
            allow 10.0.0.0/8;      # VPC CIDR
            deny all;
        }
    }

  # PHP-FPM upstream config
  upstream.conf: |
    upstream php-fpm {
        server php-service:9000;
        keepalive 32;
    }
```

---

## PHP ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: php-config
  namespace: project-a-prod
data:
  custom.ini: |
    ; Memorija
    memory_limit = 256M
    
    ; Execution time
    max_execution_time = 30
    max_input_time = 60
    
    ; Upload
    upload_max_filesize = 20M
    post_max_size = 22M
    
    ; Opcache — kritično za PHP performanse u K8s
    opcache.enable = 1
    opcache.memory_consumption = 128
    opcache.validate_timestamps = 0    ; ne provjeri fajlove (slike su immutable)
    opcache.max_accelerated_files = 10000
    
    ; Error handling (prod: samo log, ne prikazuj)
    display_errors = Off
    log_errors = On
    error_log = /dev/stderr
    
    ; Session (Redis)
    session.save_handler = redis
    session.save_path = "tcp://redis:6379?auth=${REDIS_PASSWORD}"
```

```yaml
  # FPM pool config
  www.conf: |
    [www]
    user = www-data
    group = www-data
    listen = 0.0.0.0:9000
    
    ; Dinamički broj workers
    pm = dynamic
    pm.max_children = 20
    pm.start_servers = 4
    pm.min_spare_servers = 2
    pm.max_spare_servers = 8
    pm.max_requests = 500       ; restart worker nakon 500 requestova (memory leak prevencija)
    
    ; Health check endpoint
    ping.path = /ping
    ping.response = pong
    
    ; Slow log
    slowlog = /dev/stderr
    request_slowlog_timeout = 5s
```

---

## Immutable ConfigMap i Secret

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-conf-v3
  namespace: project-a-prod
immutable: true   # K8s 1.21+ — ne može biti promijenjen
data:
  default.conf: |
    ...
```

**Zašto immutable u produkciji:**
- Spriječi slučajnu izmjenu konfiguracije bez deployment-a
- K8s ne mora pratiti promjene (performance)
- Jedini način promjene: kreirati novu ConfigMap s novim imenom, updateovati Deployment reference

**Pattern za immutable ConfigMap s verzioniranjem:**
```bash
# Helm automatski hasha ConfigMap content i dodaje u ime
# Ili ručno:
nginx-conf-v1  →  nginx-conf-v2  →  nginx-conf-v3
```

Helm `helm.sh/chart-checksum` anotacija automatski restartuje Deployment pri promjeni ConfigMap-a:
```yaml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

---

## Secret tipovi

```yaml
# Generički secret (naš slučaj za DB credentials, API ključeve)
type: Opaque

# Docker registry credentials (za imagePullSecrets)
type: kubernetes.io/dockerconfigjson

# TLS sertifikat (cert-manager kreira ovaj tip)
type: kubernetes.io/tls

# Basic auth
type: kubernetes.io/basic-auth

# SSH ključ
type: kubernetes.io/ssh-auth
```

### Opaque Secret — DB credentials

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
  namespace: project-a-prod
type: Opaque
# Vrijednosti su base64 encoded (NE enkriptirane — samo encoded!)
data:
  host: bXlzcWwubXlkb21haW4uY29t      # base64("mysql.mydomain.com")
  port: MzMwNg==                        # base64("3306")
  database: cHJvamVjdF9h               # base64("project_a")
  username: YXBwX3VzZXI=               # base64("app_user")
  password: c3VwZXJzZWNyZXRwYXNz       # base64("supersecretpass")
  dsn: YXBwX3VzZXI6c3VwZXJzZWNyZXRwYXNzQHRjcChtb...  # cijeli DSN string
```

```bash
# Enkodiranje
echo -n "supersecretpass" | base64
# Dekodiranje
kubectl get secret db-credentials -n project-a-prod -o jsonpath='{.data.password}' | base64 -d
```

**Važno**: `base64` nije enkripcija. Secret u etcd-u je po defaultu samo base64 encoded. Za pravu enkripciju: envelope encryption s KMS (AWS KMS na EKS).

### imagePullSecret za GitLab registry

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gitlab-registry-credentials
  namespace: project-a-dev
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: |
    {
      "auths": {
        "registry.gitlab.com": {
          "username": "deploy-token-xxx",
          "password": "glpat-xxxxxxxxxxxxxxxx",
          "auth": "<base64 of username:password>"
        }
      }
    }
```

Ovo se kreira base64 encodovanim ili:
```bash
kubectl create secret docker-registry gitlab-registry-credentials \
  --docker-server=registry.gitlab.com \
  --docker-username=deploy-token-xxx \
  --docker-password=glpat-xxxxxxxxxxxxxxxx \
  -n project-a-dev
```

```yaml
# Referenca u Deployment-u
spec:
  imagePullSecrets:
    - name: gitlab-registry-credentials
  containers:
    - name: go-service
      image: registry.gitlab.com/project-a/go-service:1.4.2
```

**Terraform kreira ovaj Secret automatski u svakom namespace-u** koristeći Kubernetes provider — nije potrebno ručno.

### TLS Secret (cert-manager)

```yaml
# cert-manager automatski kreira i rotira
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: project-a-tls
  namespace: project-a-prod
spec:
  secretName: project-a-tls-cert    # ovaj Secret se automatski kreira
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
    - api.project-a.com
    - www.project-a.com
```

---

## External Secrets Operator — tok promjene

```
AWS Secrets Manager rotira secret (svakih 30 dana)
    ↓
ExternalSecret kontroler detektuje promjenu
(refreshInterval: 1h — provjera svakih sat vremena)
    ↓
K8s Secret se ažurira s novom vrijednošću
    ↓
Stakater Reloader detektuje promjenu Secret-a
(prati annotation reloader.stakater.com/auto: "true")
    ↓
Rolling restart Deployment-a (go-service, php-service, nginx)
    ↓
Novo revizija s novim credentialima aktivna
(zero downtime: rolling restart, maxUnavailable: 0)
```

**ExternalSecret definicija:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
  namespace: project-a-prod
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secretsmanager
    kind: ClusterSecretStore
  target:
    name: db-credentials          # K8s Secret koji se kreira
    creationPolicy: Owner
  data:
    - secretKey: password         # ključ u K8s Secret-u
      remoteRef:
        key: project-a/prod/db    # putanja u AWS Secrets Manager
        property: password        # property unutar JSON-a u SM
    - secretKey: username
      remoteRef:
        key: project-a/prod/db
        property: username
    - secretKey: host
      remoteRef:
        key: project-a/prod/db
        property: host
```

**Stakater Reloader anotacija na Deployment-u:**

```yaml
metadata:
  annotations:
    reloader.stakater.com/auto: "true"
    # ILI specifično za određene Secrets/ConfigMaps:
    secret.reloader.stakater.com/reload: "db-credentials,redis-credentials"
    configmap.reloader.stakater.com/reload: "nginx-conf,php-config"
```

---

## Secrets u Helm chart-ovima

**Nikad ne commitovati plaintext secrets u values.yaml!** Helm pattern:

```yaml
# values.yaml (committed to git — NEMA secrets)
database:
  host: ""        # popunjava se iz External Secret ili CI/CD
  port: 3306
  name: project_a

# Tajne vrijednosti dolaze kroz:
# 1. values-secret.yaml (u .gitignore)
# 2. helm install --set database.password=$DB_PASS
# 3. External Secrets Operator (preferirani za produkciju)
# 4. Sealed Secrets (encrypted u gitu)
```

**Helm lookup funkcija za postojeće Secrets:**
```yaml
# templates/secret.yaml
{{- $existingSecret := lookup "v1" "Secret" .Release.Namespace "db-credentials" -}}
{{- if not $existingSecret }}
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  password: {{ .Values.database.password | b64enc }}
{{- end }}
# Kreiraj Secret samo ako ne postoji — ne prepiši ga (ESO ga možda upravlja)
```

---

## Debugging konfiguracije

```bash
# Provjeri što pod vidi kao env varijable
kubectl exec -it go-service-xxx -n project-a-prod -- env | sort

# Provjeri sadržaj mountovanog configmap fajla
kubectl exec -it nginx-xxx -n project-a-prod -- cat /etc/nginx/conf.d/default.conf

# Provjeri sadržaj Secret-a (bez pokazivanja vrijednosti)
kubectl get secret db-credentials -n project-a-prod -o jsonpath='{.data}' | python3 -c "
import sys, json, base64
d = json.load(sys.stdin)
for k, v in d.items():
    print(f'{k}: {base64.b64decode(v).decode()[:3]}***')
"

# Je li ConfigMap ažuriran? (volume mount bez subPath se ažurira automatski)
kubectl exec -it nginx-xxx -- ls -la /etc/nginx/conf.d/
# Provjerite timestamp — može biti do 60s kašnjenja

# ExternalSecret status
kubectl describe externalsecret db-credentials -n project-a-prod
# Status.Conditions pokazuje Ready/NotReady i razlog
```

---

## Sažetak: konfiguracijski pattern za project-A

| Što | Gdje | Pattern |
|-----|------|---------|
| nginx.conf | ConfigMap volume mount | Cijeli fajl, readOnly |
| php custom.ini | ConfigMap subPath | Samo jedan fajl, ne zamjeni dir |
| LOG_LEVEL, APP_ENV | ConfigMap envFrom | Sve odjednom |
| DB credentials | External Secret → K8s Secret | AWS SM → ESO → Secret |
| Redis password | External Secret → K8s Secret | AWS SM → ESO → Secret |
| GitLab registry | K8s Secret (Terraform) | docker-registry tip |
| TLS cert | cert-manager Certificate | Automatska rotacija |
| Rotation response | Stakater Reloader | Rolling restart on Secret change |
