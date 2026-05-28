# 15. Skaliranje u praksi

Stack: Vue.js (frontend, nginx) + PHP 8.3 (php-service) + Go 1.22 (go-service + go-notification-service) + MySQL + Redis na AWS EKS. Helm charts za deployment. HPA konfigurisan u prod.

---

## 1. Tri načina skaliranja — kada koji

| Metoda | Persistentno? | Prepisuje na deploy? | Kada koristiti |
|--------|--------------|---------------------|----------------|
| `kubectl scale` | Ne | Da (helm override) | Hitna intervencija, testing |
| `helm upgrade --set` | Da (do sljedećeg values commit-a) | Ne | Temporary change |
| `values.yaml` commit + pipeline | Da | Nikad | Standardni put |
| HPA | Automatski | Ne | Load-based auto-scaling |

**Pravilo:** `kubectl scale` za hitne situacije, `values.yaml` commit za sve ostalo. `helm upgrade --set` je kompromis koji stvara git drift — koristi ga samo kada nema vremena za proper commit.

---

## 2. Ručno skaliranje (kubectl) — hitna intervencija

```bash
# Scenarij: traffic spike, PHP service gušen
# Trenutno: php=2, go=3, frontend=2

# Skaliraj odmah (bez deploy-a):
kubectl scale deployment php-service --replicas=3 -n project-a-prod
kubectl scale deployment go-service --replicas=4 -n project-a-prod
kubectl scale deployment frontend --replicas=7 -n project-a-prod   # 2+5

# Provjeri:
kubectl get deployment -n project-a-prod -o wide
# NAME             READY   UP-TO-DATE   AVAILABLE
# php-service      3/3     3            3
# go-service       4/4     4            4
# frontend         7/7     7            7

# Provjeri da li je rollout završen:
kubectl rollout status deployment/php-service -n project-a-prod
# deployment "php-service" successfully rolled out

# UPOZORENJE: sljedeći helm upgrade ovo RESETUJE na vrijednosti iz chart-a!
# Mora se sinhronizovati sa values.yaml — uradi commit odmah.
```

### Kada koristiti kubectl scale

- Production je pao, nema vremena za pipeline
- Testiraš kako se aplikacija ponaša s više replika
- HPA je isključen i treba brza korekcija

### Zašto je opasno

Sljedeći `helm upgrade` (čak i za nesrodnu promjenu kao što je image tag) resetuje `replicaCount` na vrijednost iz `values.yaml`. Ako si zaboravio commitati promjenu — izgubio si je.

---

## 3. Helm skaliranje — persistentno bez full redeploy

```bash
# --reuse-values: zadrži sve ostale vrijednosti, promijeni samo ove
helm upgrade project-a ./helm/project-a \
  -n project-a-prod \
  --reuse-values \
  --set phpService.replicaCount=3 \
  --set goService.replicaCount=4 \
  --set frontend.replicaCount=7 \
  --wait

# Verify:
helm get values project-a -n project-a-prod
# phpService.replicaCount: 3
# goService.replicaCount: 4
# frontend.replicaCount: 7

# Provjeri da li su pod-ovi gotovi:
kubectl get deployment -n project-a-prod
# NAME             READY   UP-TO-DATE   AVAILABLE
# php-service      3/3     3            3
# go-service       4/4     4            4
# frontend         7/7     7            7
```

### Razlika između --set i --reuse-values

```bash
# BEZ --reuse-values: helm merge-uje samo default values + ono što proslijediš
# Sve custom vrijednosti koje nisu u default values.yaml se GUBE

# Sa --reuse-values: zadrži sve što je trenutno deployano, override samo --set vrijednosti
# Sigurnije za produkciju — ne mijenja slučajno ostale settinge
```

**NAPOMENA:** `--reuse-values` + git je out-of-sync. Odmah commitaj promjenu u `values.yaml` ili ćeš imati drift između git-a i produkcije.

---

## 4. Pravi put — values.yaml commit + pipeline

```yaml
# helm/project-a/values/prod.yaml — promijeni i commitaj
phpService:
  replicaCount: 3    # bylo: 2

goService:
  replicaCount: 4    # bylo: 3

frontend:
  replicaCount: 7    # bylo: 2
```

```bash
git add helm/project-a/values/prod.yaml
git commit -m "scale: php=3, go=4, frontend=7 for Black Friday"
git push
# Pipeline automatski deploya promjenu
```

Ovo je jedini pravi put koji:
- Ostaje u git historiji (znaš ko, kada i zašto je skalirao)
- Ima code review ako je MR (drugi tim pregleda prije deploy-a)
- Može se rollbackovati (`helm rollback project-a 3 -n project-a-prod`)
- Uvijek je sinhronizovano sa pipeline-om

### Rollback skaliranja

```bash
# Vidi historiju deploy-a:
helm history project-a -n project-a-prod
# REVISION  STATUS     CHART              APP VERSION  DESCRIPTION
# 1         deployed   project-a-1.0.0    1.0.0        Initial deployment
# 2         deployed   project-a-1.0.0    1.0.0        scale: php=2, go=3
# 3         deployed   project-a-1.0.0    1.0.0        scale: php=3, go=4, frontend=7

# Rollback na prethodnu reviziju:
helm rollback project-a 2 -n project-a-prod

# Provjeri:
helm status project-a -n project-a-prod
```

---

## 5. HPA (Horizontal Pod Autoscaler) — dinamička optimizacija

HPA automatski skalira pod-ove na osnovu metrika — bez ručne intervencije.

```yaml
# helm/project-a/templates/hpa.yaml
{{- if .Values.phpService.hpa.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: php-service-hpa
  namespace: {{ .Release.Namespace }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: php-service
  minReplicas: {{ .Values.phpService.hpa.minReplicas }}
  maxReplicas: {{ .Values.phpService.hpa.maxReplicas }}
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70   # Scale out kada CPU > 70%
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60    # Čekaj 60s prije scale up
      policies:
        - type: Pods
          value: 2                       # Max 2 poda po koraku
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300   # Čekaj 5 min prije scale down (cooldown)
      policies:
        - type: Pods
          value: 1                       # Max 1 pod prema dolje odjednom
          periodSeconds: 120
{{- end }}
```

```yaml
# values/prod.yaml — HPA konfiguracija
phpService:
  replicaCount: 2      # Minimalni baseline (HPA override-uje ovo kada skalira gore)
  hpa:
    enabled: true
    minReplicas: 2
    maxReplicas: 10

goService:
  replicaCount: 3
  hpa:
    enabled: true
    minReplicas: 3
    maxReplicas: 15

frontend:
  replicaCount: 2
  hpa:
    enabled: true
    minReplicas: 2
    maxReplicas: 20    # Frontend je statički — jeftino skalirati

# values/dev.yaml — HPA isključen u dev
phpService:
  replicaCount: 1
  hpa:
    enabled: false    # Dev nema dovoljno load-a za HPA

goService:
  replicaCount: 1
  hpa:
    enabled: false
```

### Provjera HPA

```bash
kubectl get hpa -n project-a-prod
# NAME              REFERENCE                TARGETS         MINPODS  MAXPODS  REPLICAS
# php-service-hpa   Deployment/php-service   45%/70%         2        10       2
# go-service-hpa    Deployment/go-service    32%/70%         3        15       3
# frontend-hpa      Deployment/frontend      8%/70%          2        20       2

kubectl describe hpa php-service-hpa -n project-a-prod
# Conditions:
#   AbleToScale    True    SucceededRescale
#   ScalingActive  True    ValidMetricFound
#   ScalingLimited False   DesiredWithinRange
# Events:
#   ... Scaled up replica count to 4 (CPU utilization: 78% > 70%)
#   ... Scaled down replica count to 2 (CPU utilization: 22% < 70%)
```

### Važno: HPA i ručno postavljeni replicaCount

Kada je HPA aktivan, `kubectl scale` i `replicaCount` u values.yaml djeluju samo kao minimum:

```bash
# Ako je HPA minReplicas=2 i ti ručno postaviš 1:
kubectl scale deployment php-service --replicas=1 -n project-a-prod
# HPA će odmah korigovati nazad na 2 (minReplicas)

# Ako postaviš 5 (unutar HPA range-a):
kubectl scale deployment php-service --replicas=5 -n project-a-prod
# HPA će zadržati 5 dok CPU ne padne ispod threshold-a, onda će scale down
```

---

## 6. KEDA — skaliranje po custom metrikama

Kubernetes Event-Driven Autoscaling. Skalira na osnovu Redis queue dubine, SQS poruka, broja događaja u stream-u i dr. Idealno za go-notification-service koji procesira email queue.

```yaml
# helm/project-a/templates/keda-scaledobject.yaml
# Email worker skaliraj po broju poruka u Redis Streamu:
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: email-worker-scaler
  namespace: project-a-prod
spec:
  scaleTargetRef:
    name: go-notification-service
  minReplicaCount: 1
  maxReplicaCount: 20
  pollingInterval: 10        # Provjeri svakih 10s
  cooldownPeriod: 30         # 30s cooldown pri scale down
  triggers:
    - type: redis-streams
      metadata:
        address: redis:6379
        stream: queue:email
        consumerGroup: email-workers
        lagCount: "50"        # 1 worker per 50 pending poruka
        # 100 poruka = 2 workera
        # 500 poruka = 10 workera
        # 1000 poruka = 20 workera (max)
```

### KEDA instalacija

```bash
helm repo add kedacore https://kedacore.github.io/charts
helm repo update

helm upgrade --install keda kedacore/keda \
  --namespace keda \
  --create-namespace \
  --version 2.14.0

# Provjeri:
kubectl get pods -n keda
# NAME                                      READY   STATUS    RESTARTS
# keda-operator-5d4c8b7f6b-xk9p2           1/1     Running   0
# keda-operator-metrics-apiserver-...       1/1     Running   0

# Provjeri ScaledObject:
kubectl get scaledobject -n project-a-prod
# NAME                   SCALETARGETKIND   SCALETARGETNAME          MIN  MAX  READY
# email-worker-scaler    Deployment        go-notification-service  1    20   True
```

### Kada koristiti KEDA umjesto HPA

| Scenarij | HPA | KEDA |
|----------|-----|------|
| CPU/memory based scaling | Da | Može |
| Redis queue dubina | Ne | Da |
| AWS SQS broj poruka | Ne | Da |
| Kafka consumer lag | Ne | Da |
| Scale to zero (0 replika) | Ne | Da |

---

## 7. Cluster Autoscaler — skaliraj AWS EC2 nodove

Kada HPA traži više pod-ova ali nema dostupnih nodova → Cluster Autoscaler dodaje novi EC2 node automatski.

```hcl
# terraform/modules/eks/cluster-autoscaler.tf
resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  namespace  = "kube-system"
  version    = "9.37.0"

  values = [
    <<-EOT
    autoDiscovery:
      clusterName: ${var.cluster_name}
    awsRegion: ${var.aws_region}
    rbac:
      serviceAccount:
        annotations:
          eks.amazonaws.com/role-arn: ${aws_iam_role.cluster_autoscaler.arn}
    extraArgs:
      scale-down-utilization-threshold: "0.5"
      scale-down-delay-after-add: "2m"
      scale-down-unneeded-time: "5m"
      skip-nodes-with-local-storage: "false"
    EOT
  ]
}
```

### Node group min/max

```hcl
# terraform/modules/eks/node-groups.tf
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-nodes"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = var.private_subnet_ids

  instance_types = ["t3.large"]

  scaling_config {
    desired_size = 2
    min_size     = 1    # Nikad ispod 1 node
    max_size     = 10   # Max 10 nodova u prod
  }

  # Obavezno za Cluster Autoscaler auto-discovery:
  tags = {
    "k8s.io/cluster-autoscaler/enabled"             = "true"
    "k8s.io/cluster-autoscaler/${var.cluster_name}" = "owned"
  }
}
```

### IAM permissions za Cluster Autoscaler

```hcl
# terraform/modules/eks/iam-cluster-autoscaler.tf
resource "aws_iam_policy" "cluster_autoscaler" {
  name = "${var.cluster_name}-cluster-autoscaler"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeTags",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:DescribeInstanceTypes"
        ]
        Resource = "*"
      }
    ]
  })
}
```

### Cluster Autoscaler monitoring

```bash
# Provjeri CA logs:
kubectl logs -l app.kubernetes.io/name=cluster-autoscaler -n kube-system --tail=50

# Provjeri koji nodovi su dodani/uklonjeni:
kubectl get events -n kube-system | grep -i "scale\|node"

# Provjeri pending pod-ove (trigger za CA scale up):
kubectl get pods -n project-a-prod --field-selector=status.phase=Pending

# Node status:
kubectl get nodes -o wide
# NAME                          STATUS   ROLES    AGE   VERSION   INTERNAL-IP
# ip-10-0-1-50.eu-west-1...     Ready    <none>   5d    v1.29.x   10.0.1.50
# ip-10-0-1-51.eu-west-1...     Ready    <none>   2m    v1.29.x   10.0.1.51  # <-- novi
```

---

## 8. Scenarij: Black Friday scaling

Korak po korak — "znam da dolazi spike, pripremi se dan unaprijed":

```bash
# DAN UNAPRIJED:

# 1. Povećaj HPA maksimum (da ima prostora za auto-scaling):
helm upgrade project-a ./helm/project-a -n project-a-prod \
  --reuse-values \
  --set phpService.hpa.maxReplicas=20 \
  --set goService.hpa.maxReplicas=30 \
  --set frontend.hpa.maxReplicas=40 \
  --wait

# 2. Povećaj node group max (da ima nodova kada HPA traži više pod-ova):
aws eks update-nodegroup-config \
  --cluster-name project-a-prod \
  --nodegroup-name project-a-prod-nodes \
  --scaling-config minSize=2,maxSize=20,desiredSize=5

# 3. Pre-scale na anticipirani minimum (ne čekaj HPA, kreni spreman):
helm upgrade project-a ./helm/project-a -n project-a-prod \
  --reuse-values \
  --set phpService.replicaCount=5 \
  --set goService.replicaCount=8 \
  --set frontend.replicaCount=10 \
  --wait

# Provjeri da su svi pod-ovi ready:
kubectl get deployment -n project-a-prod
kubectl get nodes

# TOKOM SPIKE:
# HPA automatski skalira dalje ako CPU > 70%
# Prati u realnom vremenu:
watch -n 5 "kubectl get hpa -n project-a-prod && echo '---' && kubectl get nodes"

# AKO TREBA BRZA KOREKCIJA (bez čekanja pipeline-a):
kubectl scale deployment php-service --replicas=12 -n project-a-prod

# NAKON SPIKE — vrati na normalne vrijednosti:
helm upgrade project-a ./helm/project-a -n project-a-prod \
  --reuse-values \
  --set phpService.replicaCount=2 \
  --set goService.replicaCount=3 \
  --set frontend.replicaCount=2 \
  --set phpService.hpa.maxReplicas=10 \
  --set goService.hpa.maxReplicas=15 \
  --set frontend.hpa.maxReplicas=20 \
  --wait

# Smanji node group (da ne plaćaš prazne EC2 nodove):
aws eks update-nodegroup-config \
  --cluster-name project-a-prod \
  --nodegroup-name project-a-prod-nodes \
  --scaling-config minSize=1,maxSize=10,desiredSize=2
```

### Checklist za Black Friday prep

```bash
# [ ] HPA maxReplicas povećan na 2-3x normal
# [ ] Node group max povečan (minSize * 2 bar)
# [ ] Node group desired pre-scaled (ne čekaj CA lag)
# [ ] Redis/MySQL connection pool limits provjereni
# [ ] PodDisruptionBudget konfigurisan (da update ne srušuje sve odjednom)
# [ ] Alerting pravila snižena (alert na 60% umjesto 80%)
# [ ] Rollback plan spreman (helm rollback project-a X -n project-a-prod)
```

---

## 9. Monitoring skaliranja

```bash
# Provjeri trenutni broj replika u realnom vremenu:
watch kubectl get deployment -n project-a-prod

# HPA events (scale up/down historija):
kubectl get events -n project-a-prod \
  --field-selector reason=SuccessfulRescale \
  --sort-by='.lastTimestamp'

# Node utilizacija:
kubectl top nodes
# NAME                              CPU(cores)   CPU%   MEMORY(bytes)   MEMORY%
# ip-10-0-1-50.eu-west-1.compute   1250m        62%    3500Mi          54%
# ip-10-0-1-51.eu-west-1.compute   800m         40%    2800Mi          43%

# Pod utilizacija (sort po CPU):
kubectl top pods -n project-a-prod --sort-by=cpu
# NAME                          CPU(cores)   MEMORY(bytes)
# php-service-7d9f8b6-xk2p1    450m         256Mi
# php-service-7d9f8b6-mn4q8    420m         248Mi
# go-service-5c7b9d4-lp3r7     180m         128Mi

# Grafana queries za dashboard:
# Replica count po deployment-u:
# kube_deployment_spec_replicas{namespace="project-a-prod"}
# kube_deployment_status_replicas_available{namespace="project-a-prod"}

# HPA desired vs current:
# kube_horizontalpodautoscaler_status_desired_replicas{namespace="project-a-prod"}
# kube_horizontalpodautoscaler_status_current_replicas{namespace="project-a-prod"}

# Pending pod-ovi (signal da cluster treba više nodova):
# kube_pod_status_phase{namespace="project-a-prod", phase="Pending"}
```

### Alerting pravila (Prometheus)

```yaml
# monitoring/alerts/scaling.yaml
groups:
  - name: scaling
    rules:
      - alert: HPAAtMaxReplicas
        expr: |
          kube_horizontalpodautoscaler_status_current_replicas
          >= kube_horizontalpodautoscaler_spec_max_replicas
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "HPA {{ $labels.horizontalpodautoscaler }} dostigao maksimum"
          description: "{{ $labels.namespace }}/{{ $labels.horizontalpodautoscaler }} je na max replikama 5+ minuta. Razmotri povećanje maxReplicas."

      - alert: PodsPending
        expr: |
          kube_pod_status_phase{namespace="project-a-prod", phase="Pending"} > 0
        for: 3m
        labels:
          severity: warning
        annotations:
          summary: "Pending pod-ovi u project-a-prod"
          description: "Pod-ovi čekaju na scheduling — cluster autoscaler možda nije dodao nodove."
```

---

## 10. GitLab CI job za scaling (self-service)

```yaml
# .gitlab-ci.yml — manuelni job koji developer može pokrenuti iz GitLab UI
scale:replicas:
  stage: deploy
  when: manual
  image: alpine/helm:3.14
  environment:
    name: production
    url: https://project-a.example.com
  variables:
    PHP_REPLICAS: "2"
    GO_REPLICAS: "3"
    FRONTEND_REPLICAS: "2"
  before_script:
    - apk add --no-cache kubectl
    - echo "$KUBE_CONFIG_PROD" | base64 -d > /root/.kube/config
    - chmod 600 /root/.kube/config
  script:
    - echo "Skaliranje na php=${PHP_REPLICAS}, go=${GO_REPLICAS}, frontend=${FRONTEND_REPLICAS}"
    - |
      helm upgrade project-a ./helm/project-a \
        -n project-a-prod \
        --reuse-values \
        --set phpService.replicaCount=${PHP_REPLICAS} \
        --set goService.replicaCount=${GO_REPLICAS} \
        --set frontend.replicaCount=${FRONTEND_REPLICAS} \
        --wait \
        --timeout 5m
    - kubectl get deployment -n project-a-prod
    - echo "DONE — commit values.yaml promjenu ako je ovo dugotrajna promjena!"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
```

### Pokretanje iz GitLab UI

1. GitLab → CI/CD → Pipelines → pokreni na `main`
2. Klikni na manuelni job `scale:replicas`
3. Set variables:
   - `PHP_REPLICAS` = `5`
   - `GO_REPLICAS` = `8`
   - `FRONTEND_REPLICAS` = `10`
4. Trigger job

**Nakon toga:** commitaj promjenu u `values/prod.yaml` da ostane u git historiji.

---

## Sažetak

| Situacija | Akcija |
|-----------|--------|
| Production pada odmah | `kubectl scale deployment X --replicas=N -n project-a-prod` |
| Promjena za danas, bez pipeline-a | `helm upgrade --reuse-values --set X.replicaCount=N` |
| Planirana promjena | Edit `values/prod.yaml` → commit → push → pipeline |
| Load-based automatski scaling | HPA (CPU/memory threshold) |
| Queue-based automatski scaling | KEDA (Redis stream lag) |
| Nedovoljno nodova | Cluster Autoscaler (automatski) ili `aws eks update-nodegroup-config` |
| Pre-scaling pred event | Kombinacija: node group desired + HPA maxReplicas + replicaCount |
