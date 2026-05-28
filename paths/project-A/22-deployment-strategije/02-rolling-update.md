# 02 — Rolling Update

## Zašto razumjeti Rolling Update duboko

Rolling Update je Kubernetes default strategija. Sve ostale tehnike (Blue-Green, Canary) grade se na istim temeljima: readiness probe, surge logika, graceful shutdown. Ko ne razumije Rolling Update, ne razumije ni ove.

---

## Deployment konfiguracija

```yaml
# helm/project-a/templates/deployment.yaml
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # Dozvoli 1 extra pod iznad desired (4 ukupno tokom deploya)
      maxUnavailable: 0    # Nikad nemaj manje od 3 ready poda (zero downtime)
  minReadySeconds: 10      # Pod mora biti healthy 10s prije nego se smatra Available
  progressDeadlineSeconds: 300  # Ako deploy ne završi za 5 min → fail i automatski rollback
  
  template:
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: go-service
          image: registry.firma.com/project-a/go-service:{{ .Values.image.tag }}
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8080
            initialDelaySeconds: 15
            periodSeconds: 15
```

### Zašto `maxUnavailable: 0`

S `maxUnavailable: 0`, Kubernetes mora čekati da novi pod postane Ready prije nego ugasi stari. Ovo garantuje da uvijek postoje 3 ready poda koji primaju saobraćaj — zero downtime.

S `maxUnavailable: 1` (default), K8s bi mogao ugasiti stari pod odmah i privremeno imati samo 2 ready poda. Za high-traffic aplikacije to znači povećan load na preostale pode i potencijalne timeout-e.

---

## Rollout anatomija za 3 replike

Vizualni prikaz s `maxSurge: 1, maxUnavailable: 0`:

```
Stanje 1:  [v1] [v1] [v1]              ← početak, sve staro
Stanje 2:  [v1] [v1] [v1] [v2]        ← surge: dodaj 1 novi pod (ukupno 4)
           Čekaj: v2 readiness probe OK + 10s minReadySeconds
Stanje 3:  [v1] [v1] [v2]             ← terminate 1 stari (vrati na 3)
Stanje 4:  [v1] [v1] [v2] [v2]        ← surge: dodaj drugi novi pod
           Čekaj: drugi v2 spreman
Stanje 5:  [v1] [v2] [v2]             ← terminate drugi stari
Stanje 6:  [v1] [v2] [v2] [v2]        ← surge: treći novi pod
           Čekaj: treći v2 spreman
Stanje 7:  [v2] [v2] [v2]             ← terminate zadnji stari → done
```

Saobraćaj se postepeno prebacuje: svaki novi pod koji postane Ready počne primati saobraćaj dok stari još rade. Korisnik nikad ne dobija 0 ready podova.

Ukupno trajanje (aproks): `broj_replika × (startup_time + minReadySeconds)` = `3 × (15s + 10s)` ≈ 75s za ovaj primjer.

---

## Praćenje rollout-a

```bash
# Prati progres u real-time — blokira dok ne završi ili ne istekne timeout
kubectl rollout status deployment/go-service -n project-a-prod --timeout=5m

# Output tokom deploya:
# Waiting for deployment "go-service" rollout to finish: 1 out of 3 new replicas have been updated...
# Waiting for deployment "go-service" rollout to finish: 2 out of 3 new replicas have been updated...
# Waiting for deployment "go-service" rollout to finish: 1 old replicas are pending termination...
# deployment "go-service" successfully rolled out

# Historija revizija
kubectl rollout history deployment/go-service -n project-a-prod
# REVISION  CHANGE-CAUSE
# 1         <none>
# 2         image update v1.2.3

# Da bi CHANGE-CAUSE bio popunjen, dodaj anotaciju pri deployu:
kubectl annotate deployment/go-service kubernetes.io/change-cause="image update v1.2.3" -n project-a-prod

# Rollback na prethodnu reviziju (najbrži rollback u hitnoj situaciji)
kubectl rollout undo deployment/go-service -n project-a-prod

# Rollback na specifičnu reviziju (ako znaš koji broj treba)
kubectl rollout undo deployment/go-service -n project-a-prod --to-revision=2

# Pauziraj rollout (npr. vidio si greške na prvom novom podu, zaustavi)
kubectl rollout pause deployment/go-service -n project-a-prod

# Nastavi
kubectl rollout resume deployment/go-service -n project-a-prod
```

---

## Helm rollback

Helm ima vlastitu historiju release-a, nezavisno od `kubectl rollout history`.

```bash
# Pogledaj historiju Helm release-a
helm history project-a -n project-a-prod
# REVISION  UPDATED                  STATUS     CHART            APP VERSION  DESCRIPTION
# 1         Mon Jan  6 10:00:00 2025 superseded project-a-0.1.0  1.0.0        Install complete
# 2         Mon Jan  6 12:00:00 2025 deployed   project-a-0.1.1  1.1.0        Upgrade complete

# Rollback na revision 1 (Helm kreira novu reviziju — ne briše stare)
helm rollback project-a 1 -n project-a-prod
# Rollback was a success! Happy Helming!

# Nakon rollbacka historija izgleda ovako:
helm history project-a -n project-a-prod
# REVISION  STATUS      DESCRIPTION
# 1         superseded  Install complete
# 2         superseded  Upgrade complete
# 3         deployed    Rollback to 1
```

Helm rollback radi `helm upgrade` s vrijednostima iz željene revizije — što znači da K8s opet radi Rolling Update (ali nazad na staru sliku).

---

## Graceful shutdown

Bez graceful shutdown, Rolling Update može prekinuti in-flight HTTP zahtjeve u trenutku terminacije poda.

### Go service

```go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/health/ready", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })
    mux.HandleFunc("/health/live", func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
    })
    // ... ostali handleri

    server := &http.Server{
        Addr:    ":8080",
        Handler: mux,
    }

    // Pokreni server u goroutini
    go func() {
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("ListenAndServe error: %v", err)
        }
    }()

    log.Println("Server started on :8080")

    // Čekaj SIGTERM (K8s shutdown) ili SIGINT (Ctrl+C lokalno)
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)
    sig := <-quit
    log.Printf("Received signal %s — shutting down gracefully...", sig)

    // Grace period: završi in-flight zahtjeve, max 25s
    // (terminationGracePeriodSeconds je 30s u K8s — ostaviš 5s rezerve za cleanup)
    ctx, cancel := context.WithTimeout(context.Background(), 25*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        log.Fatalf("Graceful shutdown failed: %v", err)
    }

    log.Println("Server stopped cleanly.")
}
```

### PHP-FPM

```ini
; /usr/local/etc/php-fpm.d/www.conf

; Čekaj da aktivni worker procesi završe zahtjeve na SIGTERM
; Vrijednost mora biti < terminationGracePeriodSeconds u K8s
process_control_timeout = 25s
```

Nginx pred PHP-FPM-om mora imati `worker_shutdown_timeout`:

```nginx
# nginx.conf
worker_shutdown_timeout 25s;  # Čekaj na in-flight zahtjeve pri SIGTERM
```

---

## Kada Rolling Update NIJE dovoljan

### 1. Breaking API change

Tokom rollouta, stari i novi pod rade istovremeno. Ako novi pod vraća drugačiji JSON format, klijenti koji su na load balanceru dobijaju inconsistent odgovore — ovisno o tome koji pod opslužuje request.

Rješenje: Blue-Green (instant switch, nema overlapa).

### 2. Nebackward-compatible DB migracija

Stari kod + nova schema = crash stari pod.
Nova schema + stari kod = crash novi pod.

Rješenje: Expand-contract pattern (vidi `01-deployment-strategije-pregled.md`).

### 3. Trebam instant rollback

Rolling Update rollback je još jedan Rolling Update nazad — traje 1-2 minute. Blue-Green rollback je promjena jedne ALB weight anotacije — traje < 1s.

### 4. Jedna replika

S `replicas: 1` i `maxUnavailable: 0`, Rolling Update ne može ugasiti jedini pod dok novi ne bude ready. Ali postoji kratki period kad je novi pod tek podigan i još nije primio saobraćaj. Ovo funkcionira, ali Blue-Green je čišće rješenje.

---

## Helm values za rolling update

```yaml
# helm/project-a/values/prod.yaml (relevantni dio)
replicaCount: 3

strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1
    maxUnavailable: 0

minReadySeconds: 10
progressDeadlineSeconds: 300

podDisruptionBudget:
  enabled: true
  minAvailable: 2
```

```yaml
# helm/project-a/templates/pdb.yaml
{{- if .Values.podDisruptionBudget.enabled }}
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: {{ include "project-a.fullname" . }}
  namespace: {{ .Release.Namespace }}
spec:
  minAvailable: {{ .Values.podDisruptionBudget.minAvailable }}
  selector:
    matchLabels:
      {{- include "project-a.selectorLabels" . | nindent 6 }}
{{- end }}
```
