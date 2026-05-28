# 01 — Performance Testing: Koncepti

## Zašto performance testing?

Znaš da aplikacija radi — unit testovi prolaze, integration testovi zeleni, deploy uspješan. Ali ne znaš koliko korisnika može izdržati. Production incident gdje app pukne pod opterećenjem je najgori način da to saznaš.

Performance testing odgovara na:
- Koliko concurrent korisnika naša app može opsluživati?
- Gdje je bottleneck — nginx, PHP-FPM, Go service, MySQL, Redis?
- Oporavlja li se app nakon naglog skoka traffic-a?
- Postoji li memory leak koji se vidi tek nakon 24h rada?

---

## Tipovi performance testova

### Load test — normalno opterećenje

**Pitanje:** Da li app radi korektno pod očekivanim brojem korisnika?

Simulira tipičan radni dan — 100 concurrent korisnika, normalan mix zahteva. Cilj nije pucanje nego validacija da SLO-ovi drže.

```
Traffic profil: 50-100 korisnika
Trajanje: 10-15 minuta
Uspjeh: p95 < SLO thresholds, error rate < 0.1%
```

### Stress test — raste do pucanja

**Pitanje:** Gdje je tačka pucanja, i kako app pada?

Postepeno povećava broj korisnika dok app ne počne failovati. Važno je i kako app pada — graceful degradation ili hard crash?

```
Traffic profil: 100 → 200 → 400 → 600 → ... do failover-a
Trajanje: dok error rate ne premaši threshold
Uspjeh: znamo gdje je limit, razumijemo mod otkaza
```

### Spike test — iznenadni skok (Black Friday scenario)

**Pitanje:** Što se dešava kad traffic eksplodira za 10x u 10 sekundi?

EKS HPA treba 2-3 minute za scale-up. Šta se dešava dok novi podovi ne budu ready?

```
Traffic profil: 10 → 500 → 10 korisnika
Trajanje: 5-10 minuta
Uspjeh: app se oporavlja nakon pada spike-a, ne ostaje u degradiranom stanju
```

### Soak test — dugotrajno opterećenje

**Pitanje:** Postoji li memory leak ili resource exhaustion koji se pojavljuje tek nakon sati rada?

```
Traffic profil: 50-100 korisnika (steady)
Trajanje: 24+ sati
Uspjeh: memory stabilna, nema goroutine leak-a, nema degradacije p95 kroz vrijeme
```

---

## Alati za ovaj stack

| Alat | Jezik API | Docker | CI integracija |
|------|-----------|--------|----------------|
| **k6** | JavaScript | Da | Nativna |
| Apache JMeter | XML/GUI | Da | Plugin potreban |
| Locust | Python | Da | Da |
| Gatling | Scala | Da | Da |

**Zašto k6 za ovaj stack:**
- Go-based runtime — efikasan, male memorijske potrebe
- JavaScript API — blizak Vue.js/Node.js developerima
- Docker-friendly — `grafana/k6:0.49.0` gotov image
- Native GitLab CI integracija
- Prometheus output — direktna integracija s postojećim monitoring stack-om
- Thresholds u kodu — test faila ako SLO nije ispunjen

---

## SLO definicije za project-a

Ovo su ciljevi koji se validiraju performance testovima:

```
Endpoint               p95 latency    Error rate    Napomena
─────────────────────────────────────────────────────────────
POST /api/auth/login   < 300ms        < 0.1%        PHP service
GET  /api/dashboard    < 500ms        < 0.1%        Go service + DB
GET  /health           < 100ms (p99)  < 0.01%       Go service
GET  /api/users        < 400ms        < 0.1%        Go service

Availability (sve)     99.9% success rate (HTTP 2xx/3xx)
                       Error budget: 43.8 minuta/mjesec
```

---

## Gdje smijemo pokretati testove?

| Okruženje | Load test | Stress test | Napomena |
|-----------|-----------|-------------|----------|
| local | Da | Da | Samo docker-compose stack |
| dev | Da (light) | Ne | Max 20 VU, može smetati drugima |
| staging | Da | Da | Izoliran od production podataka |
| production | Ne | Ne | Nikad bez explicit approve |

---

## Workflow za learning

```
1. Napiši k6 skriptu (modules 02-03)
2. Pokreni lokalno s docker-compose stackom
3. Analiziraj rezultate — gdje je bottleneck?
4. Integriraj u GitLab CI na staging (module 04)
5. Profiling kad nađeš problem (module 05)
```
