# 05 - Volumes i Storage

## Kontejneri su ephemeral

Sve što kontejner zapiše na filesystem — nestaje kada kontejner stane. Nginx logovi, database fajlovi, upload-ovi korisnika — sve se briše pri restartu.

Za hello-world nginx aplikaciju to nije problem (stateless). Ali kada dodamo Prometheus za monitoring, on treba trajno čuvati metrics podatke. Bez persistent storage, svaki restart Prometheus-a znači gubitak historije metrika.

Kubernetes rješava ovo s **Volumes** — direktorijumima koji nadžive kontejner.

## Tipovi volumena (od jednostavnog ka kompleksnom)

### emptyDir: privremeni, dijeljeni unutar Pod-a

```yaml
spec:
  volumes:
    - name: shared-data
      emptyDir: {}
  containers:
    - name: nginx
      volumeMounts:
        - name: shared-data
          mountPath: /var/cache/nginx
    - name: cache-warmer
      volumeMounts:
        - name: shared-data
          mountPath: /data
```

`emptyDir` živi dok živi Pod. Kada Pod nestane (restart, reschedule), podaci se brišu. Korisno za: deljenje fajlova između kontejnera unutar Pod-a, privremeni scratch space.

### hostPath: directory s host node-a

```yaml
volumes:
  - name: node-logs
    hostPath:
      path: /var/log/nginx
      type: DirectoryOrCreate
```

Mount direktorija s worker node-a. Korisno za: pristup host logovima, lokalni razvoj gdje znate na kom node-u je Pod. **Ne koristiti u produkciji** (Pod vezan za specifičan node, sigurnosni rizik).

Za kind lokalni razvoj, hostPath je OK za brzo testiranje.

## PersistentVolume i PersistentVolumeClaim: produkcijska apstrakcija

Direktno referencirati disk u Pod specifikaciji je loše — Pod ne bi trebao znati što je "iza" njega (NFS, EBS, lokal disk...). PV/PVC razdvaja tu odgovornost.

**PersistentVolume (PV)** — resurs koji administrator (ili StorageClass) kreira. Predstavlja stvarni disk.

**PersistentVolumeClaim (PVC)** — zahtjev Poda za storage. Kubernetes pronalazi odgovarajući PV i "veže" ga za PVC.

```yaml
# PVC — što aplikacija traži
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-data
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce       # jedan node može pisati istovremeno
  storageClassName: standard
  resources:
    requests:
      storage: 10Gi
```

Korištenje PVC u Pod-u:

```yaml
spec:
  volumes:
    - name: prometheus-storage
      persistentVolumeClaim:
        claimName: prometheus-data
  containers:
    - name: prometheus
      image: prom/prometheus:v2.48.0
      volumeMounts:
        - name: prometheus-storage
          mountPath: /prometheus
```

Access modes:
- **ReadWriteOnce (RWO)** — jedan node može pisati. AWS EBS, tipičan za baze podataka.
- **ReadOnlyMany (ROX)** — više node-ova može čitati. Za shared config fajlove.
- **ReadWriteMany (RWX)** — više node-ova može pisati. AWS EFS (NFS), skuplje, za dijeljene uploadove.

## StorageClass: dinamičko provisionovanje

Umjesto ručnog kreiranja PV-ova za svaki PVC, **StorageClass** automatski kreira storage na zahtjev.

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
reclaimPolicy: Delete        # obriši disk kada se PVC obriše
volumeBindingMode: WaitForFirstConsumer
```

Na EKS-u: EBS CSI driver automatski kreira gp3 volumene. Na kind-u: ugrađeni `standard` StorageClass kreira lokalni storage.

## AWS storage opcije za project-A

| Tip | Koristiti za | Access Mode | Cijena |
|-----|-------------|-------------|--------|
| EBS gp3 | Baze podataka, Prometheus | RWO | $ |
| EFS | Shared config, NFS share | RWX | $$ |
| S3 (ne K8s volume) | Statički fajlovi, backup | - | $ |

Za hello-world projekat specifično:
- Prometheus metrics → EBS gp3, 10-50GB
- Grafana dashboards → EBS gp3, 5GB
- Loki logs → S3 bucket (Loki ima native S3 podrška)
- hello-world nginx → nema storage potrebe (stateless)

## Kada NIJE potreban persistent storage

Stateless aplikacije kao hello-world nginx ne trebaju storage:

- `index.html` je u Docker image-u (ili u ConfigMap-u)
- nginx ne piše ništa što treba preživjeti restart
- Horizontalno skaliranje je trivijalno (svaki Pod identičan)

Ovo je prednost stateless dizajna — lakše skaliranje, jednostavniji operativni model. Kada god možete izbjeći state u K8s Podovima, izbjegavajte. Database može biti RDS (van K8s-a), filestorage može biti S3.

## Kind lokalni storage

Za lokalni rad s kind clusterom:

```bash
# Kind ima ugrađeni standard StorageClass koji kreira lokalne direktorije
kubectl get storageclass
# NAME                 PROVISIONER             ...
# standard (default)   rancher.io/local-path   ...

# PVC se automatski veže
kubectl apply -f prometheus-pvc.yaml
kubectl get pvc -n monitoring
# NAME              STATUS   VOLUME                     CAPACITY
# prometheus-data   Bound    pvc-abc123...              10Gi
```

Za Prometheus u kasnijim modulima, PVC je jedina razlika između kind i EKS konfiguracije — StorageClass naziv (`standard` vs `gp3`). Kustomize overlay mijenja samo tu jednu liniju.
