# Feature Flags

## Šta su feature flags i zašto ih koristiti

Feature flag je runtime switch koji kontroliše da li je određena funkcionalnost uključena ili isključena — bez ponovnog deploya koda.

**Osnovni princip:** odvojiti deploy od release-a.

```
Bez feature flags:
  Deploy nov kod → Odmah dostupno svim korisnicima
  Bug u novom kodu → Hitni rollback (deploy starog koda)

Sa feature flags:
  Deploy nov kod (flag je OFF) → Niko ne vidi novu funkcionalnost
  Testiraj u prod sa internim korisnicima (flag ON za 5%)
  Uključi flag → Release bez deploymenta
  Bug pronađen → Isključi flag → Nema potrebe za rollback-om
```

**Kad koristiti feature flags:**
- Nova kompleksna funkcionalnost koja treba testiranje u prod okruženju
- A/B testiranje (novo vs staro sučelje)
- Graduated rollout — postepeno širenje na sve korisnike
- Emergency kill switch — ako nešto pukne, isključiš bez rollback-a
- Maintenance mode — privremeno isključi dio sistema

**Kad NE koristiti feature flags:**
- Svaka sitna promjena — pretjerana upotreba stvara "feature flag dug"
- Feature flagovi koji nikad ne budu obrisani — čiste se nakon stabilizacije

---

## Redis-based feature flags (bez eksternog servisa)

Za project-a koristimo Redis koji već imamo u infrastrukturi. Nema potrebe za LaunchDarkly ni sličnim SaaS rješenjima dok projekt nije na dovoljnoj skali.

**Go: Feature Flag Service:**

```go
type FeatureFlags struct {
    redis  *redis.Client
    logger *zap.Logger
}

func NewFeatureFlags(redis *redis.Client, logger *zap.Logger) *FeatureFlags {
    return &FeatureFlags{redis: redis, logger: logger}
}

// IsEnabled — provjeri je li flag uključen
func (f *FeatureFlags) IsEnabled(ctx context.Context, flag string) bool {
    val, err := f.redis.Get(ctx, "feature:"+flag).Result()
    if err != nil {
        if err != redis.Nil {
            f.logger.Warn("feature flag redis error, defaulting to disabled",
                zap.String("flag", flag),
                zap.Error(err),
            )
        }
        return false  // Default: isključeno ako Redis nije dostupan
    }
    return val == "1"
}

func (f *FeatureFlags) Enable(ctx context.Context, flag string) error {
    return f.redis.Set(ctx, "feature:"+flag, "1", 0).Err()
}

func (f *FeatureFlags) Disable(ctx context.Context, flag string) error {
    return f.redis.Set(ctx, "feature:"+flag, "0", 0).Err()
}

// ListAll — lista svih definisanih flagova i njihovog stanja
func (f *FeatureFlags) ListAll(ctx context.Context) (map[string]bool, error) {
    keys, err := f.redis.Keys(ctx, "feature:*").Result()
    if err != nil {
        return nil, err
    }

    result := make(map[string]bool, len(keys))
    for _, key := range keys {
        val, _ := f.redis.Get(ctx, key).Result()
        flagName := strings.TrimPrefix(key, "feature:")
        result[flagName] = val == "1"
    }
    return result, nil
}
```

**Korištenje u HTTP handleru:**

```go
func (s *Server) handleDashboard(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()

    if s.flags.IsEnabled(ctx, "new-dashboard") {
        s.handleNewDashboard(w, r)
        return
    }
    s.handleOldDashboard(w, r)
}

// Ili u business logici
func (s *OrderService) CreateOrder(ctx context.Context, order *Order) error {
    if s.flags.IsEnabled(ctx, "new-pricing-engine") {
        return s.createOrderWithNewPricing(ctx, order)
    }
    return s.createOrderLegacy(ctx, order)
}
```

---

## Graduated rollout (% korisnika)

Postepeno puštanje funkcionalnosti na dio korisnika. Počneš sa 1%, pa 5%, 10%, 50%, 100%.

```go
// IsEnabledForUser — deterministički, isti user uvijek dobija isti rezultat
func (f *FeatureFlags) IsEnabledForUser(ctx context.Context, flag string, userID int64) bool {
    // Provjeri boolean flag — ako je full on, vrijedi za sve
    if f.IsEnabled(ctx, flag) {
        return true
    }

    // Provjeri percentage flag
    pct, err := f.redis.Get(ctx, "feature:"+flag+":percentage").Int()
    if err != nil {
        return false
    }

    if pct <= 0 {
        return false
    }
    if pct >= 100 {
        return true
    }

    // Deterministički hash: userID % 100 daje konzistentan bucket
    // User 1234 uvijek pada u isti bucket, ne mijenja se između requesta
    bucket := int(userID % 100)
    return bucket < pct
}
```

**Korištenje za graduated rollout:**

```go
func (s *Server) handleCheckout(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    userID := getUserID(ctx)

    if s.flags.IsEnabledForUser(ctx, "new-checkout-flow", userID) {
        s.handleNewCheckout(w, r)
        return
    }
    s.handleOldCheckout(w, r)
}
```

**Postepeno uključivanje:**

```bash
# Faza 1: 5% korisnika
kubectl exec redis-xxx -- redis-cli SET feature:new-checkout-flow:percentage 5

# Faza 2: Provjeri metrics, nema grešaka → 25%
kubectl exec redis-xxx -- redis-cli SET feature:new-checkout-flow:percentage 25

# Faza 3: 100% — full rollout
kubectl exec redis-xxx -- redis-cli SET feature:new-checkout-flow 1
kubectl exec redis-xxx -- redis-cli DEL feature:new-checkout-flow:percentage
```

---

## Naming konvencija

```
feature:<flag-name>                  → boolean on/off (0 ili 1)
feature:<flag-name>:percentage       → graduated rollout (0-100)
feature:maintenance-mode             → emergency toggle
feature:new-dashboard                → nova funkcionalnost
feature:new-pricing-engine           → nova poslovna logika
```

**Primjeri:**

```
feature:new-dashboard            = 0  (isključeno)
feature:new-checkout-flow        = 1  (uključeno za sve)
feature:new-checkout-flow:percentage = 25  (uključeno za 25%)
feature:maintenance-mode         = 0  (normalan rad)
feature:experimental-search      = 1  (uključeno za testiranje)
```

**Pravila imenovanja:**
- Kebab-case, uvijek opisno
- Prefiks tipa: `new-`, `experimental-`, `maintenance-`
- Nakon stabilizacije — obriši flag i kod za staru putanju

---

## Upravljanje flagovima

**Iz CLI-a direktno kroz Redis:**

```bash
# Uključi flag
kubectl exec -n project-a-prod deployment/go-service -- \
  redis-cli -h redis-master SET feature:new-dashboard 1

# Ili kroz Redis pod direktno
kubectl exec -n project-a-dev redis-xxx -- \
  redis-cli SET feature:new-dashboard 1

# Isključi flag
kubectl exec -n project-a-prod redis-xxx -- \
  redis-cli SET feature:new-dashboard 0

# Provjeri status
kubectl exec redis-xxx -- redis-cli GET feature:new-dashboard

# Lista svih flagova
kubectl exec redis-xxx -- redis-cli KEYS "feature:*"

# Provjeri sve flagove i vrijednosti
kubectl exec redis-xxx -- redis-cli MGET \
  feature:new-dashboard \
  feature:new-checkout-flow \
  feature:maintenance-mode
```

**Admin endpoint u Go service (interno, auth required):**

```go
// GET /internal/features — lista svih flagova
func (s *Server) handleListFeatures(w http.ResponseWriter, r *http.Request) {
    flags, err := s.features.ListAll(r.Context())
    if err != nil {
        http.Error(w, "redis error", http.StatusInternalServerError)
        return
    }
    json.NewEncoder(w).Encode(flags)
}

// POST /internal/features/{flag}/enable
// POST /internal/features/{flag}/disable
```

---

## GitLab CI integration

Feature flagovi se mogu uključivati kao dio pipeline-a, ali uvijek `when: manual` — nikad automatski u prod.

```yaml
# .gitlab-ci.yml

stages:
  - build
  - deploy
  - release

deploy:prod:
  stage: deploy
  script:
    - helm upgrade --install project-a ./charts/project-a
        --namespace project-a-prod
        --values values/prod.yaml
        --set image.tag=$CI_COMMIT_SHORT_SHA
  environment:
    name: production

# Feature flag enable — odvojen job, ručno
enable-feature:new-dashboard:
  stage: release
  when: manual                    # Ručno — ne dešava se automatski
  needs: [deploy:prod]            # Mora biti deploy završen
  environment:
    name: production
  script:
    - |
      kubectl exec -n project-a-prod \
        $(kubectl get pod -n project-a-prod -l app=redis -o jsonpath='{.items[0].metadata.name}') -- \
        redis-cli SET feature:new-dashboard 1
    - echo "Feature new-dashboard enabled in production"

# Emergency disable — uvijek dostupno
disable-feature:new-dashboard:
  stage: release
  when: manual
  environment:
    name: production
  script:
    - |
      kubectl exec -n project-a-prod \
        $(kubectl get pod -n project-a-prod -l app=redis -o jsonpath='{.items[0].metadata.name}') -- \
        redis-cli SET feature:new-dashboard 0
    - echo "Feature new-dashboard DISABLED in production"
```

---

## Feature flag lifecycle

```
1. DEVELOPMENT
   Kod pisan iza flag-a
   Flag defaultno isključen

2. STAGING
   Feature:flag = 1 u staging
   QA testiranje

3. PRODUCTION — DARK LAUNCH
   Deploy na prod (flag = 0)
   Samo interna testiranja (ručno uključiš za svoj account)

4. PRODUCTION — GRADUATED ROLLOUT
   feature:flag:percentage = 5
   Pratite metrics 24h
   → 25% → 50% → 100%

5. FULL RELEASE
   feature:flag = 1
   Obriši percentage key

6. CLEANUP (nakon 2-4 sedmice stabilnosti)
   Obriši flag check iz koda
   Obriši staru putanju koda
   Obriši Redis key
   Commit: "Remove feature flag new-dashboard, now default behavior"
```

---

## Checklist

- [ ] FeatureFlags service inicijalizovan sa Redis klientom
- [ ] Default je `false` (isključeno) kada Redis nije dostupan
- [ ] Graduated rollout koristi deterministički hash (ne random)
- [ ] Naming konvencija: `feature:kebab-case-name`
- [ ] GitLab pipeline ima `when: manual` za enable/disable u prod
- [ ] Stari feature flag kod obrisan nakon stabilizacije
- [ ] Nema feature flag-a starijih od 2 meseca bez plana za cleanup
