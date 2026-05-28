# 06 - HPA i Skaliranje

## Zašto automatsko skaliranje

Ručno upravljanje brojem Podova ne skalira:
- Produkcioni trafic varira tokom dana (jutarnji spike, noćni minimum)
- Ne možete biti uvijek budni da gledate CPU metrike
- Preveliko fiksno skaliranje = trošak, premalo = degradovane performanse

Kubernetes nudi tri nivoa automatskog skaliranja:

**HPA (Horizontal Pod Autoscaler)** — mijenja broj Podova u Deployment-u
**VPA (Vertical Pod Autoscaler)** — mijenja requests/limits pojedinog Poda
**Cluster Autoscaler** — dodaje/uklanja worker node-ove iz clustera

Za project-A: koristimo HPA. VPA i Cluster Autoscaler su za naprednije EKS scenarije.

## Requests i Limits: obavezno postaviti

Bez resource requests i limits, Kubernetes scheduler ne zna koliko resursa Pod treba i može prenatrpati node. HPA ne može raditi bez postavljenih CPU requests.

```yaml
resources:
  requests:
    cpu: "50m"        # 50 milicores = 5% jedne CPU jezgre
    memory: "64Mi"    # 64 megabajta
  limits:
    cpu: "200m"       # maksimalno 200 milicores
    memory: "128Mi"   # ne može preći 128Mi (OOMKilled ako premaši)
```

**Requests** — garantovani resursi. Scheduler koristi ovo da odluči na koji node staviti Pod. "Ovaj node ima dovoljno slobodnih resursa za ovaj Pod."

**Limits** — maksimum koji Pod može potrošiti. CPU limit = throttling (sporije, ali radi). Memory limit = OOMKilled (Pod se ubija i restartuje).

Zašto ne staviti visoke limits "za svaki slučaj"? Jer requests i limits zajedno definišu **QoS klasu** Pod-a:
- `requests == limits` → **Guaranteed** (nikad ne može biti evicted osim ako nema memorije na nodu)
- `requests < limits` → **Burstable** (može biti evicted pod pritiskom)
- Nema requests/limits → **BestEffort** (prvi na listi za eviction)

Preporuka za produkciju: postavite i requests i limits. Za stateless servise kao nginx, razumno je `cpu requests: 50m, limits: 200m` — može burstovati ali ne može "ukrasti" sve CPU.

## HPA: Horizontal Pod Autoscaler

HPA prati metrike (CPU, memorija, custom metrike) i mijenja `replicas` u Deployment-u.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hello-world-hpa
  namespace: helloworld-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hello-world
  minReplicas: 2        # nikad manje od 2 (HA)
  maxReplicas: 10       # nikad više od 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70   # skaliraj gore kada CPU > 70% od request-a
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

Kako HPA odlučuje o broju replika:

```
željene_replike = ceil(trenutne_replike * (trenutna_utilizacija / target_utilizacija))

Primjer: 2 replike, CPU 90%, target 70%
željene_replike = ceil(2 * (90/70)) = ceil(2.57) = 3
```

HPA čeka s scale-down odlukama da bi izbjegao flapping — podrazumijevano čeka 5 minuta stabilnog nižeg load-a.

Provjera HPA stanja:

```bash
kubectl get hpa -n helloworld-prod
# NAME              REFERENCE         TARGETS   MINPODS   MAXPODS   REPLICAS
# hello-world-hpa   Deployment/...    45%/70%   2         10        3

kubectl describe hpa hello-world-hpa -n helloworld-prod
# Vidi events: ScalingReplicaSet (scale up/down)
```

## Resource planning: procjena resursa

Za nginx koji servira statički HTML, profil je predvidiv:

```
Jedan nginx Pod za statički sadržaj:
- CPU request: 10-50m (uglavnom idle, spike pri zahtjevima)
- Memory request: 32-64Mi (nginx je izuzetno efikasan)
- Pod može obraditi 1000+ req/s s minimalnim resursima

Za dinamičke aplikacije (Node.js, Python):
- Profajlirajte lokalno: k6 ili Apache Benchmark
- CPU request: mjerite p95 CPU pri normalnom load-u
- Memory request: mjerite steady-state memorijsku upotrebu
```

Alati za profajliranje:

```bash
# Kratki load test
kubectl run -it --rm load-test \
  --image=williamyeh/wrk \
  --restart=Never \
  -- wrk -t4 -c100 -d30s http://hello-world.helloworld-prod

# Praćenje resursa tokom testa
kubectl top pods -n helloworld-prod --watch
```

## Veza sa project-A: skaliranje po okruženju

| Okruženje | Strategija | HPA |
|-----------|-----------|-----|
| dev | 1 replika, nema HPA | - |
| staging | 2 replike, nema HPA | - |
| prod | 2-10 replika | CPU 70%, Memory 80% |

Dev ne treba HPA — troši resurse i skuplje je. Staging ima 2 replike za HA testing ali ne skalira. Produkcija ima HPA s minimalnih 2 replike (ako jedan Pod padne, drugi odgovara).

```yaml
# k8s/overlays/prod/hpa.yaml — samo u prod overlay-u
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hello-world-hpa
  namespace: helloworld-prod
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hello-world
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Na EKS-u, Cluster Autoscaler radi u paru s HPA: kada HPA hoće više Podova ali nema slobodnih node-ova, Cluster Autoscaler dodaje novi EC2 instance u node group. Kada load padne i HPA smanji replike, Cluster Autoscaler uklanja prazne node-ove. Troškovi se automatski optimizuju.
