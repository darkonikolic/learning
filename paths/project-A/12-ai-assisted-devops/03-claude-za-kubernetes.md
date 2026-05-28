# Claude za Kubernetes

## Debugging K8s problema sa AI

Kubernetes greške su često kriptične. AI je koristan jer može prevesti
`OOMKilled` u "pod je potrošio više memorije od limita, povećaj memory limit
ili smanji memory leak u aplikaciji" — i odmah ponudi sljedeći korak.

### CrashLoopBackOff debugging

Scenarijo: deployao si helloworld app na kind, pod je u CrashLoopBackOff.

**Korak 1 — Skupi kontekst**
```bash
kubectl describe pod helloworld-abc123-xyz -n helloworld-local
kubectl logs helloworld-abc123-xyz -n helloworld-local --previous
kubectl get events -n helloworld-local --sort-by='.lastTimestamp'
```

**Korak 2 — Prijepi sve u Claude**
```
Pod je u CrashLoopBackOff. Evo describe outputa:
[prijepi kubectl describe output]

Evo logova:
[prijepi kubectl logs output]

Evo eventova:
[prijepi kubectl get events output]

App je nginx koji servira statički index.html. Šta nije u redu?
```

Tipični uzroci koje Claude identifikuje:
- `exec /docker-entrypoint.sh: permission denied` → Dockerfile USER problem
- `nginx: [emerg] open() "/etc/nginx/conf.d/default.conf" failed` → ConfigMap nije mountovan
- `Liveness probe failed` → probe path ne postoji ili app sporo starta

### Kompleksan Deployment manifest od nule

```
Napiši Kubernetes Deployment manifest za nginx koji servira statički fajl:
- Image: registry.gitlab.com/moj-user/project-a:1.0.0
- Non-root user (runAsUser: 101 je nginx user)
- ReadOnlyRootFilesystem: true (potrebno montovati /tmp i /var/cache/nginx)
- Liveness probe: HTTP GET /healthz na portu 80, initialDelaySeconds 10
- Readiness probe: HTTP GET / na portu 80, initialDelaySeconds 5
- Resource requests: 50m CPU, 64Mi memory
- Resource limits: 200m CPU, 128Mi memory
- Env variable: APP_ENV iz ConfigMap "app-config", key "environment"

Objasni zašto je ReadOnlyRootFilesystem dobar i šta treba montovati.
```

### Helm + AI za values override

Kada Helm chart postoji ali trebaš prod values:

```
Imam ovaj Helm chart values.yaml:
[prijepi values.yaml]

Generiši values/prod.yaml override za production:
- 3 replike umjesto 1
- HPA: min 3, max 10, targetCPUUtilizationPercentage 70
- Strikte resource limits (nginx je statički, ne treba mu puno)
- pullPolicy IfNotPresent (ne latest)
- Ingress: host app.firma.com, TLS true, AWS ALB annotations

Ne dupliraj vrijednosti iz values.yaml — override samo ono što se razlikuje.
```

### K8s security review

```
Pregledaj ovaj Kubernetes manifest sa sigurnosnog aspekta:
[prijepi manifest]

Traži:
1. Kontejner koji radi kao root
2. Capabilities koje ne trebaju
3. Privileged kontejneri
4. HostPID/HostNetwork/HostIPC postavljeni na true
5. Nedostajući securityContext
6. Preširoke RBAC permisije (ako postoje)

Za svaki nalaz objasni rizik i predloži fix.
```

## Primjer iterativnog sessiona: od greške do rješenja

Ovo je realan primjer sa 3 Claude poruke.

**Poruka 1 — Prijavi problem**
```
Deployao sam hello-world nginx na kind klaster. Pod se startuje ali odmah
puca. Evo kubectl describe:

Events:
  Warning  BackOff    5s   kubelet  Back-off restarting failed container helloworld
  
State: Terminated
  Reason:  Error
  Exit Code: 1

Logs:
nginx: [emerg] mkdir() "/var/cache/nginx/client_temp" failed (30: Read-only file system)
```

Claude odgovori: Problem je ReadOnlyRootFilesystem + nginx koji treba da napravi
direktorije. Rješenje: mountovati emptyDir na `/var/cache/nginx` i `/tmp`.

**Poruka 2 — Primijeni i prijavi novi problem**
```
Dodao sam emptyDir mount za /var/cache/nginx i /tmp. Pod se sada startuje
ali readiness probe failuje. Evo:

Readiness probe failed: HTTP probe failed with statuscode: 404

nginx.conf koji koristim je:
server {
  listen 80;
  location / {
    root /usr/share/nginx/html;
    index index.html;
  }
}
```

Claude odgovori: Probe path `/` treba vrati 200, ali ako `index.html` ne postoji
u `/usr/share/nginx/html` u Docker image-u — nginx vraća 404. Provjeri Dockerfile.

**Poruka 3 — Finalna provjera**
```
Dockerfile je:
FROM nginx:alpine
COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf

Sada pod radi. Da li postoji još nešto što trebam popraviti za
production-readiness ovog deploya?
```

Claude daje listu: dodaj USER nginx (non-root), dodaj HEALTHCHECK u Dockerfile,
razmotre `nginx:1.25-alpine` umjesto `nginx:alpine` (pinned verzija), provjeri
da li nginx.conf ima worker_processes auto.

## Korisne K8s debugging komande za Claude kontekst

Kada debuguješ, uvijek skupi kontekst sa ovim komandama i prijepi u Claude:

```bash
# Opšti pregled
kubectl get all -n <namespace>

# Detalji o podu
kubectl describe pod <pod-name> -n <namespace>

# Logovi (trenutni i prethodni ako je crashovao)
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous

# Evente
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Ingress debug
kubectl describe ingress -n <namespace>
kubectl get ingress -n <namespace> -o yaml

# Helm release status
helm status helloworld -n helloworld-local
helm get values helloworld -n helloworld-local
```

## Veza sa project-A

Konkretni K8s debugging scenariji koji će se desiti u projektu:

1. **kind Ingress ne radi** — nginx ingress controller nije instaliran ili port
   mapping u kind-config.yaml nije tačan. Prompt: "kind ingress controller ne radi,
   evo kind-config.yaml i kubectl get pods -n ingress-nginx"

2. **EKS pod ne može pull image** — IAM permisije za ECR/GitLab registry. Prompt:
   "EKS pod ima ImagePullBackOff, image je na GitLab registry, evo describe poda"

3. **Helm upgrade ne radi** — rolling update zaglavljen jer readiness probe failuje
   na novoj verziji. Prompt: "helm upgrade --wait timeoutuje, evo kubectl rollout
   status i describe poda sa novom verzijom"

4. **HPA ne skalira** — metrics-server nije instaliran ili resource requests nisu
   postavljeni. Prompt: "HPA prikazuje unknown za CPU utilization, evo kubectl
   describe hpa output"
