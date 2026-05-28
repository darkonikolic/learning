# 05 — Debugging u Kubernetes (kind lokalno)

## Zašto debuggovat u K8s, a ne samo u Compose

Docker Compose reprodukuje aplikacijski kod ali ne i K8s specifičnosti koje mogu uzrokovati bug-ove:

- **Network policies**: Service A može communickati sa B u Compose, ali K8s NetworkPolicy to može blokirati
- **Resource limits**: `memory: 256Mi` limit uzrokuje OOMKill koji se ne pojavljuje lokalno bez limita
- **Health checks**: Readiness probe failuje u K8s ali ne u Compose (drugačiji timing)
- **Service mesh**: Istio/Linkerd mijenja mrežni stack (mTLS, retries, timeouts)
- **ConfigMap/Secret mounting**: Različiti mount paths i permissions od Docker volumes

Pravilo: ako bug "radi lokalno ali ne u K8s" — debug u K8s klasteru.

---

## Setup: kind lokalni Kubernetes klaster

```bash
# Instaliraj kind
brew install kind  # MacOS
# ili
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.22.0/kind-linux-amd64
chmod +x ./kind && mv ./kind /usr/local/bin/kind

# Kreiraj klaster
kind create cluster --name project-a-dev

# Provjeri
kubectl cluster-info --context kind-project-a-dev
kubectl get nodes
```

---

## PHP Xdebug u Kubernetes

### Problem: `host.docker.internal` ne radi u K8s

U Docker Compose, `host.docker.internal` resolv-uje na IP host mašine. U K8s podu, ovaj hostname ne postoji — Xdebug ne može naći IDE.

### Rješenje 1: kubectl port-forward (preporučeno)

Umjesto da Xdebug šalje konekciju prema hostu, koristimo obrnuti tunel: `kubectl port-forward` prosljeđuje lokalni port 9003 DO pod-a. Ali Xdebug je klijent (on se konektuje prema IDE-u), ne server — ovaj pristup ne radi direktno.

**Ispravno rješenje**: Xdebug treba IP koji je routabilan iz pod-a prema host mašini.

### Rješenje 2: Host IP u K8s node mreži

```bash
# Pronađi IP host mašine na K8s node mreži
# Na Mac sa kind:
docker inspect kind-control-plane | grep -A2 '"IPAddress"'
# Ili:
kubectl get node kind-control-plane -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}'
# Npr: 172.18.0.2

# IP host mašine na docker bridge:
ip addr show docker0 | grep "inet " | awk '{print $2}' | cut -d/ -f1
# Npr: 172.17.0.1
```

Konfiguriraj Xdebug da koristi ovaj IP:

```ini
; docker/php/xdebug-k8s.ini
[xdebug]
xdebug.mode=debug
xdebug.start_with_request=yes
xdebug.client_host=172.18.0.1   ; IP host mašine routabilan iz kind node-a
xdebug.client_port=9003
xdebug.idekey=VSCODE
```

### Rješenje 3: K8s ConfigMap override

```yaml
# k8s/debug/php-xdebug-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: php-xdebug-config
  namespace: project-a-dev
data:
  xdebug.ini: |
    [xdebug]
    xdebug.mode=debug
    xdebug.start_with_request=yes
    xdebug.client_host=172.18.0.1
    xdebug.client_port=9003
    xdebug.idekey=VSCODE
    xdebug.log=/tmp/xdebug.log
    xdebug.log_level=3
```

```yaml
# k8s/debug/php-deployment-patch.yaml
# Kustomize patch za dodavanje debug ConfigMap
apiVersion: apps/v1
kind: Deployment
metadata:
  name: php-service
spec:
  template:
    spec:
      containers:
      - name: php-service
        volumeMounts:
        - name: xdebug-config
          mountPath: /usr/local/etc/php/conf.d/xdebug.ini
          subPath: xdebug.ini
      volumes:
      - name: xdebug-config
        configMap:
          name: php-xdebug-configmap
```

```yaml
# k8s/debug/kustomization.yaml
resources:
  - ../base
patches:
  - path: php-deployment-patch.yaml
configMapGenerator:
  - name: php-xdebug-configmap
    files:
      - xdebug.ini=php-xdebug-configmap.yaml
```

Primjena:
```bash
kubectl apply -k k8s/debug/
```

---

## PHP port-forward za Xdebug u K8s

Xdebug se konektuje iz pod-a prema hostu. Moramo osigurati da konekcija može proći:

```bash
# Terminal 1: Osiguraj da VS Code sluša na 9003 lokalno
# Pokrenuti "Listen for Xdebug (PHP)" u VS Code

# Terminal 2: Provjeri da Xdebug log vidljiv iz pod-a
kubectl exec -it php-service-xxx -n project-a-dev -- tail -f /tmp/xdebug.log

# Provjeri da li se konekcija uspostavlja
# U log-u mora biti: "Connected to debugging client"
# Ili greška: "Could not connect to host:port"
```

---

## Go Delve u Kubernetes

### Debug Deployment (Helm values override)

```yaml
# helm/values/debug.yaml
goService:
  image:
    tag: debug    # image tag za debug build (sa Delve)
    repository: registry.gitlab.com/mycompany/project-a/go-service

  ports:
    - name: http
      containerPort: 8080
    - name: delve
      containerPort: 40000

  securityContext:
    capabilities:
      add:
        - SYS_PTRACE
    seccompProfile:
      type: Unconfined

  command: ["/dlv"]
  args:
    - "exec"
    - "/app/server"
    - "--headless"
    - "--listen=:40000"
    - "--api-version=2"
    - "--accept-multiclient"
    - "--continue"
```

Primjena Helm debug overlay-a:

```bash
helm upgrade --install go-service ./helm/go-service \
  -f helm/values/base.yaml \
  -f helm/values/debug.yaml \
  -n project-a-dev
```

### Kustomize pristup

```yaml
# k8s/debug/go-deployment-patch.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-service
spec:
  template:
    spec:
      containers:
      - name: go-service
        image: registry.gitlab.com/mycompany/project-a/go-service:debug
        command: ["/dlv"]
        args:
          - "exec"
          - "/app/server"
          - "--headless"
          - "--listen=:40000"
          - "--api-version=2"
          - "--accept-multiclient"
          - "--continue"
        ports:
        - containerPort: 40000
          name: delve
        securityContext:
          capabilities:
            add:
              - SYS_PTRACE
          seccompProfile:
            type: Unconfined
```

### Service za Delve port

```yaml
# k8s/debug/go-delve-service.yaml
# Eksponira Delve port unutar klaster-a (port-forward će ga koristiti)
apiVersion: v1
kind: Service
metadata:
  name: go-service-delve
  namespace: project-a-dev
spec:
  selector:
    app: go-service
  ports:
  - name: delve
    port: 40000
    targetPort: 40000
```

### Port-forward Delve prema localhost-u

```bash
# Pronađi ime pod-a
kubectl get pods -n project-a-dev | grep go-service
# go-service-7d9f8b6c5-xkp9r

# Terminal 1: Port-forward Delve porta
kubectl port-forward pod/go-service-7d9f8b6c5-xkp9r 40000:40000 -n project-a-dev
# ili via Service:
kubectl port-forward service/go-service-delve 40000:40000 -n project-a-dev

# Terminal 2: VS Code attach (isti launch.json kao za Compose)
# "Attach to Go service (Delve)" → 127.0.0.1:40000
```

Dok port-forward radi, VS Code se konektuje na `127.0.0.1:40000` a kubectl preusmjerava saobraćaj u pod. Iz perspektive VS Code-a, nema razlike između Compose i K8s debuga.

---

## Provjeri da pod radi sa debug image-om

```bash
# Provjeri koji image koristi pod
kubectl describe pod go-service-xxx -n project-a-dev | grep Image:
# Mora biti: Image: registry.gitlab.com/mycompany/project-a/go-service:debug

# Provjeri da Delve process radi
kubectl exec -it go-service-xxx -n project-a-dev -- ps aux | grep dlv
# Mora pokazati: /dlv exec /app/server --headless ...

# Provjeri logs za "API server listening at"
kubectl logs go-service-xxx -n project-a-dev | head -20
```

---

## Produkcijsko debugging bez Delve

Nikad ne stavljaš Delve u produkciju. Alternativni alati:

### Go pprof (ugrađen u stdlib)

```go
// main.go — omogući pprof HTTP endpoint
import (
    "net/http"
    _ "net/http/pprof"  // import za side effect — registrira HTTP handlere
)

func main() {
    // Pokreni pprof na zasebnom portu
    go func() {
        http.ListenAndServe(":6060", nil)
    }()
    
    // ... ostatak aplikacije
}
```

```bash
# Port-forward pprof
kubectl port-forward pod/go-service-xxx 6060:6060 -n production

# CPU profil (30 sekundi)
curl -s "http://localhost:6060/debug/pprof/profile?seconds=30" > cpu.prof
go tool pprof -http=:8081 cpu.prof

# Heap profil
curl -s "http://localhost:6060/debug/pprof/heap" > heap.prof
go tool pprof -http=:8081 heap.prof

# Goroutine dump (vidi sve goroutine-e)
curl -s "http://localhost:6060/debug/pprof/goroutine?debug=2"
```

**Važno**: pprof endpoint ne smije biti dostupan na production javnom interfejsu! Koristiti zasebni port koji je dostupan samo via `kubectl port-forward`.

### SIGUSR1 za runtime diagnostiku

```go
// handlers/signals.go
import (
    "os"
    "os/signal"
    "runtime"
    "syscall"
)

func SetupSignalHandlers() {
    sigChan := make(chan os.Signal, 1)
    signal.Notify(sigChan, syscall.SIGUSR1)
    
    go func() {
        for range sigChan {
            // Dump goroutine stacktrace u stderr (vidljivo u kubectl logs)
            buf := make([]byte, 1<<20)
            n := runtime.Stack(buf, true)
            fmt.Fprintf(os.Stderr, "=== SIGUSR1 goroutine dump ===\n%s\n", buf[:n])
        }
    }()
}
```

```bash
# Pošalji SIGUSR1 u pod
kubectl exec go-service-xxx -n production -- kill -SIGUSR1 1

# Čitaj dump iz logova
kubectl logs go-service-xxx -n production | tail -100
```

### Structured logging za post-mortem analizu

```go
// Logiraj sve što je potrebno za dijagnostiku
logger.Error("login failed",
    zap.String("request_id", requestId),
    zap.String("user_email", req.Email),
    zap.String("client_ip", r.RemoteAddr),
    zap.Duration("duration", time.Since(start)),
    zap.Error(err),
)
```

```bash
# Pretraži logove u K8s
kubectl logs -l app=go-service -n production --since=1h | \
  jq 'select(.level=="error" and .msg=="login failed")'
```

---

## Namespace izolacija za debug workload-e

Nikad ne deploy-uj debug build u isti namespace kao production:

```bash
# Kreiraj izoliran namespace za debug
kubectl create namespace project-a-debug

# Deploy debug verzije tu
kubectl apply -f k8s/debug/ -n project-a-debug

# Provjeri da production namespace nema debug image-e
kubectl get deployments -n production -o yaml | grep ":debug" && \
  echo "WARNING: debug image in production!" || \
  echo "OK: no debug images in production"
```
