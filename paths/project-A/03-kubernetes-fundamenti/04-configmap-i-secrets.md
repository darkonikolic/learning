# 04 - ConfigMap i Secrets

## Zašto ne staviti konfiguraciju u image

Zamislite da build-ujete nginx image s konfiguracijskim fajlom unutra. Svaka promjena konfiguracije — novi build, novi push, novi deploy. Za sitne konfiguracije (promijeniti log level, dodati header) to je predugo.

Kubernetes nudi dva objekta za odvojena konfiguraciju od koda:

**ConfigMap** — za nekritičnu konfiguraciju koja se može slobodno čitati
**Secret** — za osjetljive podatke (lozinke, API ključevi, TLS certifikati)

## ConfigMap: konfiguracija bez rebuilda

ConfigMap može sadržavati key-value parove ili čitave fajlove.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
  namespace: helloworld-dev
data:
  # Key-value par
  LOG_LEVEL: "warn"
  MAX_BODY_SIZE: "10m"

  # Čitav fajl (multi-line)
  nginx.conf: |
    server {
        listen 80;
        server_name _;

        client_max_body_size 10m;

        root /usr/share/nginx/html;
        index index.html;

        location / {
            try_files $uri $uri/ =404;
        }

        location /health {
            access_log off;
            return 200 "ok\n";
            add_header Content-Type text/plain;
        }
    }
```

## Mountovanje: env varijabla vs fajl

Dva načina korištenja ConfigMap-a u Pod-u:

**Kao environment varijable:**

```yaml
spec:
  containers:
    - name: nginx
      image: registry.gitlab.com/firma/project-a:a3f9c21
      env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: nginx-config
              key: LOG_LEVEL
      # Ili sve odjednom:
      envFrom:
        - configMapRef:
            name: nginx-config
```

**Kao fajl (volume mount):**

```yaml
spec:
  volumes:
    - name: nginx-conf-volume
      configMap:
        name: nginx-config
        items:
          - key: nginx.conf
            path: default.conf   # ime fajla unutar kontejnera
  containers:
    - name: nginx
      image: registry.gitlab.com/firma/project-a:a3f9c21
      volumeMounts:
        - name: nginx-conf-volume
          mountPath: /etc/nginx/conf.d
          readOnly: true
```

Kada koristiti koji pristup:
- **Env varijable** — jednostavne string vrijednosti koje aplikacija čita kao `os.environ`
- **Volume mount** — konfiguracijski fajlovi (nginx.conf, app.yaml, .properties)

Nginx mora primiti fajl — koristimo volume mount. Node.js app koja čita `process.env.DB_URL` — env varijabla.

## Secret: osjetljivi podaci

Secret je sintaktički sličan ConfigMap-u, ali Kubernetes ga tretira posebno:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: helloworld-dev
type: Opaque
data:
  # Vrijednosti su base64 encoded
  DB_PASSWORD: cGFzc3dvcmQxMjM=   # echo -n "password123" | base64
  API_KEY: c2VrcmV0a2V5           # echo -n "secretkey" | base64
stringData:
  # Alternativa: direktni tekst, Kubernetes automatski encoduje
  DB_URL: "postgresql://user:password123@db:5432/app"
```

Generisanje base64:
```bash
echo -n "moja-lozinka" | base64
# bW9qYS1sb3ppbmth
```

Korištenje u Podu:
```yaml
env:
  - name: DB_PASSWORD
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: DB_PASSWORD
```

TLS Secret (poseban tip koji Ingress koristi):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: hello-world-tls
  namespace: helloworld-dev
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
```

## Zašto Secret NIJE dovoljno siguran

Važno razumjeti ograničenje: Secret nije enkripcija, to je samo base64 enkodiranje. Svako ko ima pristup K8s API-ju može pročitati Secret:

```bash
kubectl get secret app-secrets -n helloworld-dev -o yaml
# Vidi se base64 vrijednost, trivijalno se dekodira
```

U etcd bazi (srce K8s clustera) Secrets su po defaultu unencrypted. Na EKS-u možete uključiti encryption at rest.

**Pravi problemi:**
- Secret u git repou (čak i ako ga "obrišete" — ostaje u historiji)
- Pregledni pristup Secrets-ima za sve DevOps inženjere

## Sealed Secrets i AWS Secrets Manager

Za produkciju postoje bolji pristupi:

**Sealed Secrets** (Bitnami) — enkriptujete Secret privatnim ključem, pa ga možete commitovati u git. Kubernetes operator ga dekriptuje. Git-friendly.

```bash
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
git add sealed-secret.yaml  # bezbedno commitovati
```

**AWS Secrets Manager + External Secrets Operator** — vrijednosti žive u AWS-u, operator ih povlači u Kubernetes Secrets po potrebi. Centralizovano upravljanje, audit log, rotation.

Za project-A: počinjemo s regularnim Secrets (ne u git repou), u kasnijim modulima prelazimo na External Secrets Operator za AWS okruženje.

## Praktičan primer: nginx.conf u ConfigMap-u

```bash
# Primjena ConfigMap-a
kubectl apply -f k8s/configmap.yaml

# Provjera
kubectl get configmap nginx-config -n helloworld-dev
kubectl describe configmap nginx-config -n helloworld-dev

# Ako promijenite ConfigMap, Pod mora biti restarovan da primi promjene
# (za volume mounts, Kubernetes ažurira fajl automatski u roku ~1 minuta)
# (za env varijable, potreban restart)
kubectl rollout restart deployment/hello-world -n helloworld-dev
```

Veza sa project-A: nginx.conf živi u ConfigMap-u, ne u Docker image-u. Možete promijeniti nginx konfiguraciju (dodati novi header, promijeniti cache TTL) bez novog Docker build-a.
