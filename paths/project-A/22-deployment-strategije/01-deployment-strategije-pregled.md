# 01 — Deployment strategije: pregled i tradeoffi

## Zašto deployment strategija nije trivijalna odluka

Rolling Update je Kubernetes default — ali to ne znači da je uvijek pravi izbor.

Svaka tehnika nosi tradeoff između četiri dimenzije:
- **Sigurnost** — kolika je vjerovatnoća da korisnik osjeti problem
- **Brzina rollbacka** — koliko brzo možeš poništiti deploy ako nešto krene naopako
- **Resursi** — koliko CPU/memorije/nodova treba tokom deploya
- **Kompleksnost** — koliko logike treba u CI/CD pipelines i Helm chartovima

Pogrešna strategija znači: downtime koji nije bio planiran, ili rollback koji traje 5+ minuta dok korisnici prijavljuju greške.

---

## Komparativna tabela strategija

| Tehnika | Downtime | Rollback speed | Resursi | DB schema change | Kada koristiti |
|---------|----------|----------------|---------|-----------------|----------------|
| Recreate | Da (~30-60s) | Brz | 1x | Bezbjedno* | Nikad u prod |
| Rolling Update | Ne | 2-5 min | 1x | Opasno** | Default za većinu slučajeva |
| Blue-Green | Ne | Instant (<1s) | 2x (kratko) | Opasno** | Major release, API breaking change |
| Canary | Ne | Instant (0% weight) | ~1.1x | Opasno** | High-traffic, A/B test, rizična promjena |

*Recreate: bezbjedno za DB schema change jer nema overlap između verzija — ali downtime je cijena.

**Rolling/Blue-Green/Canary: ako DB migracija nije backward-compatible, stari i novi pod rade istovremeno i čitaju/pišu isti schema → nekonzistentnost. Rješenje: expand-contract pattern.

---

## Expand-Contract pattern za DB migracije

Problem: imaš kolonu `user_name` i hoćeš je podijeliti na `first_name` + `last_name`. Ako deployaš novu aplikaciju direktno, stara verzija pada jer nova kolona ne postoji — ili nova verzija pada jer stara kolona još postoji.

Rješenje je expand-contract u četiri sigurna koraka:

```
Korak 1 — EXPAND (safe deploy):
  Dodaj nove kolone first_name i last_name (nullable).
  Stari kod ih ignorira. Deploy je bezbjed.

Korak 2 — DUAL WRITE (novi kod):
  Deploy aplikacije koja piše u OBJE kolone:
  user_name, first_name, i last_name.
  Čitanje još uvijek ide iz user_name.

Korak 3 — MIGRACIJA PODATAKA:
  Backfill: UPDATE users SET first_name = split_part(user_name,' ',1), ...
  Može biti postupno, bez downtime.

Korak 4 — CONTRACT (cleanup):
  Aplikacija sada čita samo iz first_name/last_name.
  Ukloni user_name kolonu — jedino novi kod radi, nema problema.
```

Svaki korak je nezavisan deploy. Možeš stati između bilo koja dva koraka.

---

## Zero-downtime deploy: preduvjeti

Bez ova četiri elementa, zero-downtime je iluzija:

### 1. Readiness probe

Kubernetes ne šalje saobraćaj podu dok probe ne prođe. Bez readiness probe, K8s šalje request na pod koji još inicijalizira aplikaciju → 502 greške.

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8080
  initialDelaySeconds: 5    # Čekaj 5s nakon starta
  periodSeconds: 5           # Provjeri svakih 5s
  failureThreshold: 3        # 3 uzastopna failure → pod nije ready
  successThreshold: 1
```

### 2. minReadySeconds

Pod postaje "Available" tek nakon što je bio healthy `minReadySeconds` sekundi. Sprečava da se novi pod smatra stabilnim odmah nakon prvog uspješnog readiness check-a.

```yaml
spec:
  minReadySeconds: 10   # Pod mora biti healthy 10s zaredom
```

### 3. PodDisruptionBudget (PDB)

Zaštita od simultanog gašenja previše podova — bilo od strane node draina, cluster autoscalera ili drugog deploya.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: project-a-pdb
  namespace: project-a-prod
spec:
  minAvailable: 2          # Uvijek mora biti alive min 2 poda
  selector:
    matchLabels:
      app: project-a
```

Alternativno: `maxUnavailable: 1` — ne smije biti više od 1 poda nedostupno u isto vrijeme.

### 4. Graceful shutdown (SIGTERM handler)

Kada K8s gasi pod (tokom deploya ili node draina), šalje SIGTERM signal. Aplikacija mora:
1. Prestati prihvatati nove zahtjeve
2. Završiti in-flight zahtjeve (grace period)
3. Zatvoriti konekcije (DB pool, cache)
4. Izaći (exit 0)

Ako aplikacija ne obradi SIGTERM, K8s čeka `terminationGracePeriodSeconds` (default 30s) i šalje SIGKILL — što znači in-flight zahtjevi su ubijeni.

```yaml
spec:
  terminationGracePeriodSeconds: 30   # K8s čeka max 30s nakon SIGTERM
```

---

## Veza s ovim projektom

Stack: Vue.js + PHP 8.3 + Go 1.22 na AWS EKS, Helm, GitLab CI/CD, AWS ALB Ingress Controller.

Pet servisa: nginx (frontend), php-service, go-service, i data layer (RDS + ElastiCache).

Preporuka per scenario:

| Scenario | Strategija |
|----------|-----------|
| Svakodnevni feature deploy | Rolling Update |
| Major API refactoring | Blue-Green |
| A/B test nove Vue komponente | Canary (10%) |
| DB schema change | Expand-contract + Rolling |
| Hotfix u produkciji | Rolling Update (`--atomic`) |

Sljedeći fajlovi: detalji svake strategije sa radnim YAML-om, Helm komandama i GitLab CI integracijom.
