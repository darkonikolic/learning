# 10 — Workloads, Jobs i StatefulSets

Pregled svih tipova workload resursa u Kubernetesu, s realnim primjerima za project-A stack (nginx, PHP 8.3, Go 1.22, MySQL 8.0, Redis 7).

---

## Deployment — stateless aplikacije

Standardni workload za sve stateless servise: nginx (Vue frontend), php-service, go-service.

### Rolling Update strategija — zero downtime

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-service
  namespace: project-a-prod
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1          # pokreni 1 ekstra pod dok update ide
      maxUnavailable: 0    # nikad ne ugasi pod dok novi nije Ready
  minReadySeconds: 10      # čekaj 10s da pod bude stabilan prije nego nastavi
  revisionHistoryLimit: 3  # čuvaj samo 3 stare revizije u etcd-u
  selector:
    matchLabels:
      app: go-service
  template:
    metadata:
      labels:
        app: go-service
    spec:
      containers:
        - name: go-service
          image: registry.gitlab.com/project-a/go-service:1.4.2
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
```

**Zašto `maxUnavailable: 0`**: nikad ne ugasi stari pod dok novi nije prošao readinessProbe. S tri replike, u toku update-a radi 3-4 poda (ne 2).

**`minReadySeconds`**: pod je "ready" po readinessProbe, ali deployment smatra uspješnim tek nakon N sekundi stabilnosti. Štiti od situacije gdje pod prode health check pa odmah crashuje.

**`revisionHistoryLimit: 3`**: svaka revizija čuva ReplicaSet u etcd-u. Default je 10. U produkciji s čestim deploymentima ovo troši etcd storage. Tri revizije = mogu rollback 3 koraka unazad, što je dovoljno.

### Recreate strategija — kada schema migracija mora biti gotova

```yaml
strategy:
  type: Recreate
# Ugasi SVE stare pode, tek onda pokreni nove
```

**Kada koristiti**: PHP servis koji ima breaking schema promjenu — stari kod ne smije raditi s novom DB shemom. Prihvaćamo downtime (uglavnom maintenance window) u zamjenu za garantovanu konzistentnost.

**Problem s Rolling Update + schema migracija**: stara i nova verzija PHP-a rade paralelno dok update ide. Ako nova verzija očekuje novu kolonu koja još ne postoji (ili obratno), dobijamo 500 errore na dijelu requesta.

**Rješenje za zero-downtime migracije** (preferirani pattern):
1. Deploy backward-compatible migracija (dodaj kolonu, ne brišuj staru)
2. Rolling update aplikacije
3. Deploy cleanup migracije (ukloni stare kolone) u sljedećem releaseu

---

## StatefulSet — state i stabilan identity

Koristiti kad pod treba:
- Stabilan network identity (predvidiv DNS naziv)
- Stabilan storage (isti PVC svaki restart)
- Uređen startup/shutdown (pod-0 uvijek prije pod-1)

### MySQL StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mysql
  namespace: project-a-dev
spec:
  serviceName: "mysql"    # headless service — stable DNS per pod
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8.0
          env:
            - name: MYSQL_ROOT_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: mysql-credentials
                  key: root-password
            - name: MYSQL_DATABASE
              value: project_a
          ports:
            - containerPort: 3306
              name: mysql
          volumeMounts:
            - name: mysql-data
              mountPath: /var/lib/mysql
          livenessProbe:
            exec:
              command:
                - mysqladmin
                - ping
                - "-h"
                - "127.0.0.1"
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - mysql
                - "-h"
                - "127.0.0.1"
                - "-e"
                - "SELECT 1"
            initialDelaySeconds: 10
            periodSeconds: 5
  volumeClaimTemplates:         # ← jedino u StatefulSet-u, nema u Deployment-u
    - metadata:
        name: mysql-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: gp3   # AWS EBS SSD — za EKS prod
        resources:
          requests:
            storage: 20Gi
```

**`volumeClaimTemplates`**: svaki pod dobija vlastiti PVC. `mysql-0` → PVC `mysql-data-mysql-0`. Ako pod restartuje, dobija isti PVC (iste podatke). Ovo je fundamentalna razlika od Deployment-a.

**Stable DNS pattern**:
```
mysql-0.mysql.project-a-dev.svc.cluster.local
mysql-1.mysql.project-a-dev.svc.cluster.local  # ako replicas: 2
```

**Ordered startup**: pod-0 mora biti Running i Ready prije nego se kreira pod-1. Ovo je kritično za MySQL replication setup — master (pod-0) mora biti spreman da se replica (pod-1) može prijaviti.

### Lokalni dev gotcha sa kind

kind ne dolazi s AWS gp3 StorageClass. Koristiti `standard` (hostPath provisioner koji kind uključuje):

```yaml
# Za lokalni razvoj (kind):
storageClassName: standard

# Za EKS produkciju:
storageClassName: gp3
```

Helm values za različite environments:
```yaml
# values-dev.yaml
mysql:
  storageClassName: standard
  storage: 5Gi

# values-prod.yaml
mysql:
  storageClassName: gp3
  storage: 20Gi
```

### Redis StatefulSet (ako u K8s)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
  namespace: project-a-dev
spec:
  serviceName: "redis"
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command: ["redis-server", "--appendonly", "yes", "--requirepass", "$(REDIS_PASSWORD)"]
          env:
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: password
          ports:
            - containerPort: 6379
          volumeMounts:
            - name: redis-data
              mountPath: /data
  volumeClaimTemplates:
    - metadata:
        name: redis-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: standard
        resources:
          requests:
            storage: 2Gi
```

**Napomena**: u cloud-native setupu Redis se često drži izvan K8s (AWS ElastiCache), ali za lokalni dev i staging StatefulSet je sasvim OK.

---

## DaemonSet — jedan pod po NODE-u

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: promtail
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: promtail
  template:
    metadata:
      labels:
        app: promtail
    spec:
      serviceAccountName: promtail
      containers:
        - name: promtail
          image: grafana/promtail:2.9.0
          args:
            - -config.file=/etc/promtail/config.yaml
          volumeMounts:
            - name: logs
              mountPath: /var/log
              readOnly: true
            - name: pods
              mountPath: /var/log/pods
              readOnly: true
            - name: config
              mountPath: /etc/promtail
      volumes:
        - name: logs
          hostPath:
            path: /var/log
        - name: pods
          hostPath:
            path: /var/log/pods
        - name: config
          configMap:
            name: promtail-config
```

**Primjeri u project-A infrastrukturi:**
- `promtail` — skuplja logove s node-a, šalje u Loki
- `node-exporter` — hardware metrike (CPU, disk, network) za Prometheus
- `aws-node` — EKS VPC CNI plugin (AWS-managed, automatski)
- `kube-proxy` — network rules (system-managed)

**Kada NE koristiti DaemonSet**: za skaliranje aplikacijskih servisa. DaemonSet znači "točno jedan po node-u", što nije ono što se želi za go-service ili php-service (broj instanci treba ovisiti o load-u, ne o broju node-ova).

---

## Job — jednokratni task

### Database migracija

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-v1-4-2
  namespace: project-a-prod
spec:
  backoffLimit: 3                # pokušaj 3 puta (ukupno 4 pokušaja)
  activeDeadlineSeconds: 300     # ubij Job ako traje duže od 5 minuta
  ttlSecondsAfterFinished: 3600  # automatski obriši 1h nakon završetka
  template:
    spec:
      restartPolicy: Never       # OBAVEZNO za Job — ne restartuj na failure
      containers:
        - name: migrate
          image: registry.gitlab.com/project-a/go-service:1.4.2
          command: ["/server", "migrate", "--direction=up"]
          env:
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: host
            - name: DB_PORT
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: port
            - name: DB_NAME
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: database
            - name: DB_USER
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: username
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-credentials
                  key: password
```

**`restartPolicy: Never` vs `OnFailure`**:
- `Never`: ako pod padne, kreira se NOVI pod (do backoffLimit puta). Stariji pod ostaje za debugging (`kubectl logs`).
- `OnFailure`: isti pod se restartuje (podsjeti na CrashLoopBackOff). Izgubi se log prethodnog pokušaja.

Za migracije: koristiti `Never` — svaki pokušaj je čist slate i može se debugirati.

**Provjeri status migracije:**
```bash
kubectl get jobs -n project-a-prod
kubectl describe job db-migration-v1-4-2 -n project-a-prod
kubectl logs job/db-migration-v1-4-2 -n project-a-prod
```

### Init Container vs Job — kada što

| Kriterij | Init Container | Job |
|----------|---------------|-----|
| Veza s podem | Blokira startup glavnog poda | Samostalan |
| Timing | Svaki restart poda | Jednokratno (ili CronJob) |
| Use case | "wait-for-dependency", quick checks | Migracije, batch obrada |
| Idempotency | Mora biti idempotent (može se pokrenuti više puta) | Idealno idempotent |
| Failure | Pod ostaje u Init:Error | Job može retry-ati |

---

## CronJob — Job na rasporedu

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: cleanup-expired-sessions
  namespace: project-a-prod
spec:
  schedule: "0 2 * * *"           # svaki dan u 02:00 UTC
  concurrencyPolicy: Forbid        # ne pokreći novi ako prethodni radi
  successfulJobsHistoryLimit: 3    # čuvaj 3 uspješna
  failedJobsHistoryLimit: 3        # čuvaj 3 neuspješna (za debugging)
  startingDeadlineSeconds: 120     # ako propustio scheduled time, pokušaj unutar 2 min
  jobTemplate:
    spec:
      backoffLimit: 2
      activeDeadlineSeconds: 600   # 10 minuta timeout
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: cleanup
              image: registry.gitlab.com/project-a/go-service:latest
              command: ["/server", "cleanup-expired-sessions"]
              env:
                - name: DB_DSN
                  valueFrom:
                    secretKeyRef:
                      name: db-credentials
                      key: dsn
```

**`concurrencyPolicy` opcije:**
- `Forbid` — ne pokreći novi dok prethodni radi (za migracije, cleanup)
- `Replace` — ubij prethodni, pokreni novi (za svježe podatke)
- `Allow` — dozvoli paralelne pokretanje (za neovisne zadatke)

**Praktični CronJobs za project-A:**

```yaml
# Backup MySQL baze (svaki dan u 03:00 UTC)
schedule: "0 3 * * *"
command: ["/scripts/backup.sh"]

# Synthetic monitoring (svakih 5 minuta)
schedule: "*/5 * * * *"
command: ["/server", "synthetic-check"]

# Rotate log files (svake nedjelje u 04:00)
schedule: "0 4 * * 0"
command: ["/scripts/rotate-logs.sh"]

# Send weekly report (ponedjeljak 08:00 UTC)
schedule: "0 8 * * 1"
command: ["/server", "send-weekly-report"]
```

**Forsiraj ručno pokretanje CronJob-a:**
```bash
kubectl create job --from=cronjob/cleanup-expired-sessions manual-cleanup-$(date +%s) -n project-a-prod
```

---

## Init Containers — kontrola startup redosljeda

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: go-service
  namespace: project-a-prod
spec:
  template:
    spec:
      initContainers:
        # Init 1: čekaj MySQL da bude spreman
        - name: wait-for-mysql
          image: mysql:8.0
          command:
            - sh
            - -c
            - |
              until mysqladmin ping -h mysql -u healthcheck --password=$HEALTH_PASS --silent; do
                echo "Waiting for MySQL..."
                sleep 2
              done
              echo "MySQL is ready"
          env:
            - name: HEALTH_PASS
              valueFrom:
                secretKeyRef:
                  name: mysql-credentials
                  key: healthcheck-password

        # Init 2: čekaj Redis
        - name: wait-for-redis
          image: redis:7-alpine
          command:
            - sh
            - -c
            - |
              until redis-cli -h redis -a $REDIS_PASS ping; do
                echo "Waiting for Redis..."
                sleep 2
              done
          env:
            - name: REDIS_PASS
              valueFrom:
                secretKeyRef:
                  name: redis-credentials
                  key: password

        # Init 3: pokreni migracije (samo ako je nova verzija)
        - name: run-migrations
          image: registry.gitlab.com/project-a/go-service:1.4.2
          command: ["/server", "migrate", "--direction=up", "--no-lock"]

      containers:
        - name: go-service
          image: registry.gitlab.com/project-a/go-service:1.4.2
```

**Izvršni redosljed**:
```
wait-for-mysql (mora završiti OK)
    ↓
wait-for-redis (mora završiti OK)
    ↓
run-migrations (mora završiti OK)
    ↓
go-service (main container — pokreće se)
```

Svaki init container mora exitovati s kode 0 da bi sljedeći počeo. Ako bilo koji padne, pod ostaje u `Init:CrashLoopBackOff`.

**Debugging init container problema:**
```bash
# Status poda
kubectl get pod go-service-xxx -n project-a-prod
# Init:0/3 → čeka, Init:Error → pao, Init:CrashLoopBackOff → ponavlja i pada

# Logovi specifičnog init containera
kubectl logs go-service-xxx -n project-a-prod -c wait-for-mysql
kubectl logs go-service-xxx -n project-a-prod -c run-migrations

# Prethodni pokušaj (ako CrashLoopBackOff)
kubectl logs go-service-xxx -n project-a-prod -c run-migrations --previous
```

**Važno**: init containeri dijele volumes s main containerima, ali ne dijele network (loopback namespace). Init container može pisati fajl koji main container čita (npr. generisani config, preuzeti artifact).

---

## Workload odlučivačka tablica

| Tip | Kada koristiti | Primjeri u project-A |
|-----|---------------|---------------------|
| `Deployment` | Stateless servisi, horizontalno skaliranje | nginx, php-service, go-service |
| `StatefulSet` | Stabilan identity + storage, ordered ops | MySQL, Redis (ako u K8s) |
| `DaemonSet` | Node-level infrastruktura, po jedan per node | Promtail, node-exporter |
| `Job` | Jednokratni task, mora uspješno završiti | DB migracije, data exports |
| `CronJob` | Ponavljajući job po rasporedu | Cleanup, backup, synthetic monitoring |
| Init Container | Blokira pod startup dok dependency nije spreman | wait-for-mysql, migracije before go-service |
