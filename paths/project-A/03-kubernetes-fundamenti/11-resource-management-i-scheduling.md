# 11 — Resource Management i Scheduling

Requests, limits, QoS klase, scheduling constraints i protection mehanizmi — kritično za stabilnost produkcijskog clustera.

---

## Requests vs Limits — fundamentalna razlika

```yaml
resources:
  requests:            # minimalni resursi koje pod GARANTOVANO dobija
    cpu: 100m          # 100 millicores = 0.1 CPU jezgra
    memory: 128Mi
  limits:              # maksimalni resursi — što se dešava pri prekoračenju ovisi o tipu
    cpu: 500m
    memory: 256Mi
```

**Requests** — scheduler koristi ovo za placement. Pod se može schedulirati na node samo ako node ima dovoljno neraspoređenih resursa. Ako node ima 4 CPU i podovi su zatražili ukupno 3.8 CPU, novi pod s `cpu request: 300m` ne može biti scheduliran na taj node (čak i ako su svi podovi spavaju i CPU usage je 10%).

**Limits** — gornja granica pri izvršavanju. Ponašanje pri prekoračenju NIJE isto za CPU i memoriju:

| Resurs | Prekoračenje limita | Posljedica |
|--------|--------------------|-----------| 
| CPU | Throttling | Pod radi sporije, ne ubija se |
| Memory | OOM Kill | Pod ubijen, exit code 137 |

**Zašto razlika**: CPU je *compressible* resurs — može se dijeliti, ograničiti, dobiti manje bez gubitka podataka. Memorija je *incompressible* — jednom alocirana, podaci su tamo. Kernel ne može "usporiti" memoriju.

### Praktična implikacija za project-A

```bash
# Simptomi CPU throttling-a:
# - Sporiji API odgovori, ali ne crashevi
# - kubectl top pods pokazuje nizak CPU usage (jer je throttlovan)
# - Metrička: container_cpu_throttled_seconds_total u Prometheusu

# Simptomi OOM Kill-a:
# - Pod u CrashLoopBackOff
# - kubectl describe pod → "Last State: Terminated, Reason: OOMKilled, Exit Code: 137"
# - kubectl logs --previous  → nema logova (kernel je ubio bez graceful shutdown)
```

---

## Realni requests/limits za project-A

```yaml
# nginx (Vue frontend) — predvidivo, malo opterećenje
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 200m
    memory: 128Mi

# php-service — varijabilno opterećenje, PHP-FPM workers
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi

# go-service — mala memorija (compiled binary), brzi CPU bursts
resources:
  requests:
    cpu: 50m
    memory: 64Mi
  limits:
    cpu: 300m
    memory: 128Mi

# MySQL — IO-bound, visoka memorija za InnoDB buffer pool
resources:
  requests:
    cpu: 500m
    memory: 1Gi
  limits:
    cpu: 1000m      # 1 CPU core
    memory: 2Gi     # nikad ne smijemo OOM-killati MySQL u produkciji!

# Redis — in-memory, predvidiva memorija
resources:
  requests:
    cpu: 50m
    memory: 256Mi
  limits:
    cpu: 200m
    memory: 512Mi
```

**Zašto MySQL nema ograničen memory na minimum**: InnoDB buffer pool cache je direktno proporcionalan performansama. MySQL koji dobije OOM Kill u produkciji = downtime + potencijalna korupcija podataka ako nije bila graceful shutdown. Bolje dati više memorije nego riskovati.

**Praktičan pristup za podešavanje requests/limits:**
1. Pokreni servis bez limits (ili s visokim limits) tjedan dana
2. Prati `kubectl top pods` i Prometheus metrike
3. Postavi `requests` na ~70% prosječne upotrebe
4. Postavi `limits` na ~2-3x requests (za burst)
5. Prati OOMKill i CPU throttle metrike 2 tjedna
6. Koriguj prema potrebi

---

## QoS klase — K8s ih automatski dodjeljuje

Kubernetes dodjeljuje QoS klasu svakom podu baziranu na requests/limits konfiguraciji. Ovo direktno utječe na koji pod biva ubijen prvi kada node ima memory pressure.

| QoS klasa | Uvjet | Prioritet pri eviction |
|-----------|-------|----------------------|
| `Guaranteed` | Svaki kontejner ima requests == limits za CPU i memory | Ubijen zadnji |
| `Burstable` | Barem jedan kontejner ima requests < limits | Ubijen u sredini |
| `BestEffort` | Nema requests ni limits ni na jednom kontejneru | Ubijen prvi |

```bash
# Provjeri QoS klasu poda
kubectl get pod go-service-xxx -o jsonpath='{.status.qosClass}'
# Output: Burstable

kubectl describe pod go-service-xxx | grep "QoS Class"
```

**Preporuka za project-A:**
- Sve aplikacijske workloade: `Burstable` (requests < limits) — kompromis između predvidivosti i efikasnosti
- MySQL: razmisli o `Guaranteed` u produkciji (requests == limits) — garantuje da neće biti evictovan
- Monitoring (Prometheus, Grafana): `Burstable` — mogu se restartovati bez kritičnog uticaja

```yaml
# Guaranteed QoS — requests mora == limits ZA SVE kontejnere u podu
resources:
  requests:
    cpu: 1000m
    memory: 2Gi
  limits:
    cpu: 1000m     # identično requests
    memory: 2Gi    # identično requests
```

---

## ResourceQuota — ograniči namespace

Sprečava jedan namespace (dev environment) od konzumiranja svih resursa clustera. Kritično za multi-tenant setup gdje više timova/projekata dijeli isti cluster.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: project-a-dev-quota
  namespace: project-a-dev
spec:
  hard:
    # Agregat requests za sve pode u namespace-u
    requests.cpu: "2"
    requests.memory: 4Gi
    # Agregat limits
    limits.cpu: "4"
    limits.memory: 8Gi
    # Broj objekata
    count/pods: "20"
    count/persistentvolumeclaims: "5"
    count/services: "10"
    count/secrets: "30"
    count/configmaps: "20"
```

```yaml
# Stroži quota za prod — ali višji limiti
apiVersion: v1
kind: ResourceQuota
metadata:
  name: project-a-prod-quota
  namespace: project-a-prod
spec:
  hard:
    requests.cpu: "8"
    requests.memory: 16Gi
    limits.cpu: "16"
    limits.memory: 32Gi
    count/pods: "50"
    count/persistentvolumeclaims: "10"
```

**Provjeri ResourceQuota iskorištenost:**
```bash
kubectl describe resourcequota project-a-dev-quota -n project-a-dev
# Prikazuje Used vs Hard za svaki resurs
```

**Česta greška**: deploy pada s `exceeded quota` ali ne znaš zašto — provjeri `kubectl describe resourcequota` u namespace-u.

---

## LimitRange — default i min/max po kontejneru

LimitRange rješava problem kontejnera koji nisu postavili resources (dobivaju `BestEffort` QoS):

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: project-a-dev
spec:
  limits:
    - type: Container
      # Default vrijednosti ako kontejner ne postavi vlastite
      default:
        cpu: 200m
        memory: 256Mi
      defaultRequest:
        cpu: 50m
        memory: 64Mi
      # Apsolutni min/max — deploy će failati ako kontejner postavi van opsega
      max:
        cpu: "2"
        memory: 2Gi
      min:
        cpu: 10m
        memory: 32Mi

    - type: PersistentVolumeClaim
      max:
        storage: 50Gi
      min:
        storage: 1Gi
```

**Zašto LimitRange u svakom namespace-u:**
1. Kontejneri bez resources automatski dobivaju razumne defaults umjesto `BestEffort`
2. Sprečava slučajno kreiranje kontejnera s npr. `limits.memory: 64Gi`
3. Kombinacija s ResourceQuota osigurava predvidivo ponašanje cijelog namespace-a

---

## Taints i Tolerations — specijalizirani node-ovi

Koristi se u EKS-u za namjenska workloads na specifičnim tipovima instanci.

```bash
# Dodaj taint na node (managed u EKS kroz node group labels/taints)
kubectl taint nodes ip-10-0-3-45.eu-west-1.compute.internal workload=database:NoSchedule
```

```yaml
# Pod koji toleriše ovaj taint (samo ovaj pod može biti scheduliran na taj node)
spec:
  tolerations:
    - key: "workload"
      operator: "Equal"
      value: "database"
      effect: "NoSchedule"
```

**`effect` opcije:**
- `NoSchedule` — novi podovi bez toleracije se NE scheduliraju, postojeći ostaju
- `NoExecute` — novi se ne scheduliraju, POSTOJEĆI se evictuju (agresivno)
- `PreferNoSchedule` — scheduler preferira drugi node, ali nije strogo

**Praktični use cases za project-A na EKS:**

```yaml
# MySQL pod na r5.large instanci (memory-optimized):
tolerations:
  - key: "node-type"
    operator: "Equal"
    value: "memory-optimized"
    effect: "NoSchedule"

# Go service na spot instancama (cost savings):
tolerations:
  - key: "kubernetes.azure.com/scalesetpriority"
    operator: "Equal"
    value: "spot"
    effect: "NoSchedule"
```

---

## Node Affinity — preferiraj ili zahtijevaj određene node-ove

```yaml
spec:
  affinity:
    nodeAffinity:
      # REQUIRED — pod se NE schedulira ako uvjet nije ispunjen
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: kubernetes.io/arch
                operator: In
                values: [amd64]   # ne deployuj na ARM (Graviton) node-ove

      # PREFERRED — scheduler preferira, ali nije obavezno
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100             # 0-100, viši = jači preference
          preference:
            matchExpressions:
              - key: node.kubernetes.io/instance-type
                operator: In
                values: [r5.large, r5.xlarge]   # memory-optimized za MySQL
        - weight: 50
          preference:
            matchExpressions:
              - key: topology.kubernetes.io/zone
                operator: In
                values: [eu-west-1a]   # preferiraj primarnu AZ
```

### Pod Affinity/Anti-Affinity — scheduling u odnosu na druge pode

```yaml
spec:
  affinity:
    # Anti-affinity: ne stavljaj 2 go-service pode na isti node
    podAntiAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        - labelSelector:
            matchExpressions:
              - key: app
                operator: In
                values: [go-service]
          topologyKey: kubernetes.io/hostname   # "različit node"

    # Anti-affinity (soft): preferiraj različite AZ zone
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          podAffinityTerm:
            labelSelector:
              matchExpressions:
                - key: app
                  operator: In
                  values: [go-service]
            topologyKey: topology.kubernetes.io/zone   # "različita AZ"
```

**Zašto anti-affinity za go-service**: s 3 replike, bez anti-affinity scheduler može staviti sve 3 na isti node. Ako taj node padne → downtime. Anti-affinity guarantuje distribuciju.

---

## PodDisruptionBudget — zaštita od masovnog gašenja

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: go-service-pdb
  namespace: project-a-prod
spec:
  minAvailable: 2     # uvijek minimum 2 poda moraju biti available
  # ILI:
  # maxUnavailable: 1  # maksimalno 1 pod može biti nedostupan
  selector:
    matchLabels:
      app: go-service
```

```yaml
# PDB za sve kritične servise u project-a-prod
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: php-service-pdb
  namespace: project-a-prod
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: php-service
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: nginx-pdb
  namespace: project-a-prod
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: nginx
```

**Šta PDB štiti od:**
1. **Node drain** za maintenance (`kubectl drain node`) — ne smije ubiti podove dok PDB nije zadovoljen
2. **Cluster Autoscaler scale-down** — ne smije ukloniti node ako bi narušio PDB
3. **Voluntary disruptions** (upgrade K8s verzije) — K8s respektuje PDB

**PDB ne štiti od:**
- Nevoluntary disruptions: hardware failure, kernel panic, OOMKill
- `kubectl delete pod` direktno — ovo uvijek prođe

```bash
# Provjeri PDB status
kubectl get pdb -n project-a-prod
# NAME             MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE
# go-service-pdb   2               N/A               1                     15d

# Ako je ALLOWED DISRUPTIONS = 0, node drain će biti blokiran
```

---

## Topology Spread Constraints — ravnomjerna distribucija

Modernija alternativa podAntiAffinity za distribuciju po zonama/node-ovima:

```yaml
spec:
  topologySpreadConstraints:
    - maxSkew: 1                    # maksimalna razlika između zona
      topologyKey: topology.kubernetes.io/zone
      whenUnsatisfiable: DoNotSchedule   # ili ScheduleAnyway
      labelSelector:
        matchLabels:
          app: go-service
    - maxSkew: 1
      topologyKey: kubernetes.io/hostname
      whenUnsatisfiable: ScheduleAnyway  # best-effort za node distribuciju
      labelSelector:
        matchLabels:
          app: go-service
```

**Kada koristiti Topology Spread vs PodAntiAffinity:**
- `PodAntiAffinity required` = rigidno (ne schedulira ako nema node) → za mali broj replika
- `TopologySpreadConstraints` = fleksibilno s maxSkew → za veći broj replika gdje savršena distribucija nije uvijek moguća

---

## Debugging resource problema

```bash
# Pod ne može biti scheduliran
kubectl describe pod go-service-xxx -n project-a-prod
# Events: 0/3 nodes are available: 3 Insufficient memory
# → node-ovi nemaju dovoljno memorije za requests

# Koji podovi koriste najviše resursa
kubectl top pods -n project-a-prod --sort-by=memory
kubectl top pods -n project-a-prod --sort-by=cpu

# Node kapacitet i iskorištenost
kubectl top nodes
kubectl describe node ip-10-0-3-45.eu-west-1.compute.internal
# Sekcija "Allocated resources" pokazuje requests per node

# OOMKill historija
kubectl get events -n project-a-prod | grep OOMKill
kubectl describe pod xxx | grep -A5 "Last State"
```

---

## Sažetak: resource management checklista za project-A

Svaki Deployment mora imati:
- `resources.requests` i `resources.limits` na svakom kontejneru
- `PodDisruptionBudget` u namespace-u `project-a-prod`
- `podAntiAffinity` ili `topologySpreadConstraints` za servise s 2+ replika

Svaki namespace mora imati:
- `ResourceQuota` — spriječi resource overconsumption
- `LimitRange` — defaulti za kontejnere bez resources

EKS produkcija dodatno:
- Taints na specijaliziranim node grupama (database, spot)
- Node affinity za MySQL na memory-optimized instancama
- Cluster Autoscaler u svakom namespace-u koji koristi `PodDisruptionBudget`
