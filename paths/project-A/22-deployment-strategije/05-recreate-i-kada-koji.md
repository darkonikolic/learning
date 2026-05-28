# 05 — Recreate strategija i decision tree

## Recreate: razumjeti da ne bi koristio u prod

```yaml
spec:
  strategy:
    type: Recreate
    # Nema rollingUpdate bloka — Recreate ga ne koristi
```

Što se desi:
1. K8s terminira SVE postojeće pode odjednom
2. Čeka da svi budu Terminated
3. Kreira SVE nove pode
4. Čeka da budu Ready

Downtime = trajanje terminacije + startup novih poda ≈ 30-90 sekundi.

### Jedini legitimni use case za Recreate u produkciji

Stateful aplikacija koja **ne može raditi s dvije verzije istovremeno** i gdje je downtime prihvatljiv:

- Singleton data processing job koji piše u jednu datoteku/stream
- Aplikacija koja drži ekskluzivni lock na resursu (distribuirani mutex)
- Inicijalni setup poda s jednokratnom migracijom koja se ne smije pokrenuti dvaput

Za sve ostalo: koristi Rolling Update, Blue-Green ili Canary.

---

## Decision tree — koja strategija

```
Imaš DB schema change koji nije backward-compatible?
│
├─ DA → Primijeni expand-contract pattern FIRST (vidi modul 01)
│       pa Rolling Update za svaki korak. Nikad ne deployaj nekompatibilni
│       schema change direktno.
│
└─ NE → nastavi dole

Kolika je tolerancija za downtime?
│
├─ Downtime je prihvatljiv (npr. maintenance window, interni alat) →
│       Recreate (jedino ovdje ima smisla)
│
└─ Zero downtime → nastavi dole

Treba li instant rollback (< 1 sekunda)?
│
├─ DA → Blue-Green
│       Razlog: ALB weight promjena je instant. Rolling Update rollback
│       traje još jedan Rolling Update (1-2 minute).
│
└─ NE → nastavi dole

Je li promjena rizična / High-traffic produkcija?
│
├─ DA → Canary (10% → 25% → 50% → 75% → 100%)
│       Razlog: izlažeš mali postotak korisnika. Automatski rollback
│       na osnovu metrika. Idealno za A/B test i algoritamske promjene.
│
└─ NE → nastavi dole

Koliko replika imaš?
│
├─ 1 replika i trebaš zero downtime →
│       Blue-Green (jedini choice — Rolling Update s 1 replikom
│       i maxUnavailable:0 funkcionira, ali Blue-Green je čišće)
│
└─ 3+ replike → Rolling Update s maxSurge:1, maxUnavailable:0
                Razlog: standard za svakodnevne deploye. Jednostavno,
                predvidivo, dovoljno brz rollback za većinu scenarija.
```

---

## Per-scenario preporuka za project-a

| Scenario | Strategija | Obrazloženje |
|----------|-----------|-------------|
| Svakodnevni feature deploy | Rolling Update | Brzo, jednostavno, zero downtime |
| Major API refactoring (breaking change) | Blue-Green | Nema mixed-version perioda, instant rollback |
| A/B test nove Vue komponente | Canary (10%) | Podaci o ponašanju korisnika prije full deploy |
| DB schema change | Expand-contract + Rolling | Backward-compatible u svakom koraku |
| Hotfix u produkciji | Rolling Update + `--atomic` | Brzina deployovanja je prioritet |
| Novi go-service algoritam (nepoznato ponašanje) | Canary (10%) | Provjeri pod realnim opterećenjem |
| Promjena nginx konfiguracije | Rolling Update | Nginx brzo starta, nema state-a |
| ElastiCache key format change | Expand-contract + Rolling | Cache i app verzije moraju biti kompatibilne |

---

## Cheat sheet: kubectl i Helm komande

```bash
# ── Rolling Update ──────────────────────────────────────────────────────────

# Deploy nova verzija (Helm)
helm upgrade project-a ./helm/project-a \
  -n project-a-prod \
  --set image.tag=v1.2.0 \
  --atomic \        # Automatski rollback ako deploy padne
  --wait \          # Čekaj da svi podovi budu Ready
  --timeout 5m

# Prati status
kubectl rollout status deployment/go-service -n project-a-prod

# Rollback (kubectl — brži, bez Helm overhead-a)
kubectl rollout undo deployment/go-service -n project-a-prod

# Rollback (Helm — rollbacka sve resurse u release-u)
helm rollback project-a 1 -n project-a-prod

# ── Blue-Green ──────────────────────────────────────────────────────────────

# Deploy green
helm upgrade --install project-a-green ./helm/project-a \
  -n project-a-prod \
  --set deployment.color=green \
  --set image.tag=v1.2.0 \
  --set ingress.enabled=false \
  --wait

# Switch traffic
kubectl annotate ingress project-a -n project-a-prod --overwrite \
  'alb.ingress.kubernetes.io/actions.weighted-routing=...'

# Rollback (instant)
bash scripts/blue-green-rollback.sh project-a-prod

# ── Canary ───────────────────────────────────────────────────────────────────

# Pokreni canary deploy (automatski postepeni rollout)
bash scripts/canary-deploy.sh v1.2.0

# Manualni rollback (ako pipeline nije dostupan)
bash scripts/canary-rollback.sh project-a-prod

# ── Opće korisne komande ─────────────────────────────────────────────────────

# Provjeri readiness svih podova
kubectl get pods -n project-a-prod -o wide

# Pogledaj events (šta se dešavalo tokom deploya)
kubectl get events -n project-a-prod --sort-by=.lastTimestamp | tail -20

# Provjeri da PDB nije blokira deploy
kubectl get pdb -n project-a-prod

# Provjeri resource usage tokom deploya
kubectl top pods -n project-a-prod

# Helm release status
helm status project-a -n project-a-prod
```

---

## Česti problemi i rješenja

### Problem: Rolling Update se zaglavio

```
kubectl rollout status vratio: "timed out waiting for the condition"
```

Dijagnostika:
```bash
# Koji pod ne postaje Ready?
kubectl get pods -n project-a-prod | grep -v Running

# Zašto pod nije Ready?
kubectl describe pod <pod-name> -n project-a-prod
# Tražiš: Events sekcija — ImagePullBackOff, CrashLoopBackOff, readiness probe failures

# Logovi
kubectl logs <pod-name> -n project-a-prod --previous   # Prethodni container (ako je crashirao)
kubectl logs <pod-name> -n project-a-prod              # Trenutni
```

Rješenja:
- `ImagePullBackOff`: registry credential problem ili pogrešan tag → provjeri `imagePullSecrets`
- `CrashLoopBackOff`: aplikacija crasha pri startu → provjeri logove, environment varijable
- Readiness probe failure: endpoint ne postoji ili vraća ne-200 → provjeri `path` u probi

Ako deploy ne može završiti, Helm `--atomic` ga automatski rollbacka. Bez `--atomic`, moraš manualno:
```bash
kubectl rollout undo deployment/go-service -n project-a-prod
```

### Problem: Blue-Green ALB weight se nije promijenio

ALB Ingress Controller čita anotacije i ažurira target group weights u AWS-u. Ovo nije instant — može trajati 10-30 sekundi.

```bash
# Provjeri da je anotacija prihvaćena
kubectl get ingress project-a -n project-a-prod \
  -o jsonpath='{.metadata.annotations.alb\.ingress\.kubernetes\.io/actions\.weighted-routing}'

# Provjeri ALB controller logove
kubectl logs -l app.kubernetes.io/name=aws-load-balancer-controller \
  -n kube-system --since=5m | grep "project-a"
```

### Problem: Canary prima 0 saobraćaja uprkos weight > 0

Uzrok: canary Service ne postoji ili nema healthy endpoints.

```bash
# Provjeri Service
kubectl get svc project-a-canary -n project-a-prod

# Provjeri Endpoints (moraju biti populated)
kubectl get endpoints project-a-canary -n project-a-prod
# NAME                ENDPOINTS           AGE
# project-a-canary    10.0.1.15:8080      2m

# Ako je ENDPOINTS prazno: selector na Service ne odgovara labelama na podu
kubectl get pods -l app=project-a,color=canary -n project-a-prod
```
