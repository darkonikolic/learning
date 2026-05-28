# 05 — Self-Service Deploy

## Kada je Ručni Deploy Potreban

Pipeline je tu da automatizuje deploje — ali pipeline može zakazati. Ili treba testirati nešto specifično bez pokretanja cijelog CI-a. Ili treba hitni rollback na prethodnu verziju odmah, ne za 15 minuta koliko pipeline traje.

**Legitimni razlozi za self-service deploy:**

1. **Pipeline je pao** — GitLab CI ima problem, deployment se ne može pokrenuti automatski
2. **Hitni rollback** — production je degradiran, treba odmah na prethodnu verziju
3. **Testiranje specifičnog image tag-a** — developer želi testirati konkretni build bez punog release procesa
4. **Hotfix bypass** — kritičan security fix koji mora ići u prod odmah

**Nije legitimni razlog:**
- "Pipeline je spor, brže ću ručno" — smanji pipeline, ne zaobilazi ga
- Rutinski deployment — to je posao pipeline-a
- Skrivanje promjena od tima — sve mora ići kroz VCS

---

## Kubeconfig za Više Environments

Kubeconfig je autentifikacioni fajl koji kubectl koristi za pristup Kubernetes cluster-u. Svaki environment (dev, staging, prod) je zasebni context.

### Dodavanje EKS Clustera u Kubeconfig

```bash
# Dev cluster
aws eks update-kubeconfig \
  --name project-a-dev \
  --region eu-west-1 \
  --alias dev

# Prod cluster
aws eks update-kubeconfig \
  --name project-a-prod \
  --region eu-west-1 \
  --alias prod
```

`--alias` daje kratko ime contextu — koristit ćeš ga za prebacivanje.

### Upravljanje Contextima

```bash
# Prikaži sve dostupne contexte
kubectl config get-contexts

# Prebaci na dev (sigurno okruženje za testiranje komandi)
kubectl config use-context dev

# Provjeri koji je context aktivan
kubectl config current-context

# Privremeno koristi drugi context (bez permanentne promjene)
kubectl --context=prod get pods -n project-a-prod
```

**Habit za sigurnost:** uvijek provjeri context prije operacije u produkciji:

```bash
kubectl config current-context && kubectl get pods -n project-a-prod | head -5
```

### Zaštita Kubeconfig-a

```bash
# Provjeri dozvole (mora biti 600)
ls -la ~/.kube/config

# Postavi ispravne dozvole
chmod 600 ~/.kube/config
```

**NIKAD:**
- Commitovati `~/.kube/config` u git
- Kopirati kubeconfig drugim osobama (svako ima svoju IAM rolu → vlastiti kubeconfig)
- Ostavljati kubeconfig na CI serveru trajno (CI koristi kratkotrajan ServiceAccount token)

---

## Deploy na Dev

Dev je slobodna zona — eksperimentiraj, testiraj, griješi. Uvijek s dev contextem:

```bash
# Provjeri context
kubectl config use-context dev

# Deploy sa specifičnim image tag-om (npr. konkretni GitLab commit SHA)
helm upgrade --install project-a ./helm/project-a \
  --namespace project-a-dev \
  -f helm/project-a/values/dev.yaml \
  --set services.goService.image.tag=abc123def456 \
  --wait \
  --timeout 5m

# Provjeri deploy
kubectl get pods -n project-a-dev -w  # -w = watch, Ctrl+C za izlaz

# Logovi novog pod-a
kubectl logs -f deployment/go-service -n project-a-dev
```

`--wait` blokira dok Helm ne potvrdi da su svi resursi Ready. `--timeout 5m` — ako ne uspije za 5 minuta, Helm vraća grešku (ne čeka beskonačno).

---

## Deploy na Prod: Kontrola Pristupa

### IAM Sloj

`developer` IAM rola smije:
- `eks:DescribeCluster` — da može update-kubeconfig
- Kubernetes RBAC: `update` na Deployments u prod namespace-u

`developer` IAM rola **ne smije**:
- `eks:UpdateCluster` — promjena samog EKS clustera
- `iam:*` — IAM promjene
- `rds:*` — direktna manipulacija RDS-om

```bash
# Provjeri što možeš raditi u prod
kubectl auth can-i update deployments -n project-a-prod
kubectl auth can-i delete pods -n project-a-prod
kubectl auth can-i create secrets -n project-a-prod
```

### Kubernetes RBAC Sloj

Tipičan RBAC za developer u prod:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer-prod
  namespace: project-a-prod
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "watch", "update", "patch"]
- apiGroups: [""]
  resources: ["pods", "pods/log", "pods/exec"]
  verbs: ["get", "list", "watch", "create"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get", "list"]
# Šta developer ne može: delete deployments, manage secrets, manage RBAC
```

### GitLab Protected Environment

U GitLab: Settings → CI/CD → Environments → `production` → Protected = ON, manual approval required. Čak i ako developer može `helm upgrade` ručno, deployment kroz pipeline zahtijeva odobrenje.

### Deploy na Prod Ručno

```bash
# UVIJEK provjeri context!
kubectl config use-context prod
kubectl config current-context  # mora biti "prod"

# Provjeri trenutnu verziju koja se vrti
helm list -n project-a-prod
helm status project-a -n project-a-prod

# Deploy (isti helm command, drugi values fajl)
helm upgrade project-a ./helm/project-a \
  --namespace project-a-prod \
  -f helm/project-a/values/prod.yaml \
  --set services.goService.image.tag=abc123def456 \
  --wait \
  --timeout 5m \
  --atomic  # --atomic: rollback automatski ako deploy ne uspije

# Prati rollout
kubectl rollout status deployment/go-service -n project-a-prod --timeout=5m
```

`--atomic` je posebno koristan u produkciji: ako novi deploy ne postane Ready u timeout periodu, Helm automatski rollback na prethodnu reviziju. Nema ručnog intervencije.

---

## Rollback

### Helm Rollback

```bash
# Prikaži historiju deploja
helm history project-a -n project-a-prod

# Output primjer:
# REVISION  UPDATED                   STATUS     CHART             DESCRIPTION
# 1         Mon Jan 13 10:00:00 2025  superseded project-a-1.2.3  Install complete
# 2         Mon Jan 13 11:30:00 2025  superseded project-a-1.2.4  Upgrade complete
# 3         Mon Jan 13 14:00:00 2025  deployed   project-a-1.2.5  Upgrade complete

# Rollback na prethodnu reviziju (3 → 2)
helm rollback project-a -n project-a-prod
# Ili eksplicitno na reviziju 2:
helm rollback project-a 2 -n project-a-prod

# Prati rollback
kubectl rollout status deployment/go-service -n project-a-prod
```

### Kubernetes Native Rollback

```bash
# Historija rollout-a za specifični deployment
kubectl rollout history deployment/go-service -n project-a-prod

# Detalji konkretne revizije
kubectl rollout history deployment/go-service -n project-a-prod --revision=3

# Rollback na prethodnu verziju
kubectl rollout undo deployment/go-service -n project-a-prod

# Rollback na specifičnu reviziju
kubectl rollout undo deployment/go-service -n project-a-prod --to-revision=2
```

**Razlika:** `helm rollback` vraća cijelu Helm release na prethodno stanje (svi resursi: Deployment, ConfigMap, Service...). `kubectl rollout undo` vraća samo taj jedan Deployment. Za promjene koje su u Helm values-ima (env varijable, config) — Helm rollback je ispravniji.

---

## Zero-Downtime Deploy Verifikacija

```bash
# Prati rollout u realnom vremenu
kubectl rollout status deployment/go-service -n project-a-prod --timeout=5m

# Provjeri koji pod-ovi su novi (gledaj AGE kolonu)
kubectl get pods -n project-a-prod -l app=go-service --sort-by=.metadata.creationTimestamp

# Provjeri da nema pod-ova u CrashLoopBackOff ili Error stanju
kubectl get pods -n project-a-prod | grep -v Running | grep -v Completed

# Provjeri error rate u Grafani u toku deploja
# Dashboard: project-a-prod → HTTP 5xx rate → trebalo bi ostati na baseline-u
```

### Rolling Update Strategija

U Helm values-ima za prod:
```yaml
deployment:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Max 1 novi pod istovremeno
      maxUnavailable: 0  # Nikad ugasiti pod dok novi nije Ready
```

`maxUnavailable: 0` garantuje zero-downtime: stari pod živi dok novi nije spreman primati promet.

---

## Checklist Za Ručni Deploy u Prod

Prije pokretanja `helm upgrade`:

- [ ] Context je `prod` (`kubectl config current-context`)
- [ ] Image tag je tačan i postoji u registriju (`docker manifest inspect ...`)
- [ ] Prethodni Helm status je `deployed`, ne `failed` (`helm status project-a -n project-a-prod`)
- [ ] Inform tim (Slack: "Deployujem X u prod, ref: INC-123")
- [ ] Grafana tab otvoren za praćenje tokom deploja
- [ ] Koristim `--atomic` za auto-rollback
- [ ] Znam koji je deployment plan ako `--atomic` rollbackuje (da li rollback rješava problem?)
