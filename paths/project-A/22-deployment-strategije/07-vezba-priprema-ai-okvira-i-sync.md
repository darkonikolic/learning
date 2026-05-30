# 07 — Vežba: Deployment strategije

Gradiš AI-okvir za rolling, blue-green i canary deploy sa health gate-ovima, pa verifikuješ zero-downtime rollout i automatski rollback.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Proširujemo postojeća CI i K8s pravila stavkama o health gate-ovima i rollback putu, konfigurišemo canary promociju na osnovu error-rate/latency metrika, i dokazujemo zero-downtime tokom rollout-a.

**Pretpostavke za potvrdu:**
- Kubernetes cluster je dostupan (local ili staging)
- Deployment manifest za ciljni servis postoji
- Observability stack (Prometheus ili sličan) prikuplja error-rate i latency metrike
- `kubectl` i `helm` (ako se koristi) su konfigurisani

**Van opsega:**
- Podešavanje observability stack-a od nule (pokriveno u oblasti 11)
- Multi-cluster deploy strategije
- GitOps (ArgoCD/Flux) — zasebna oblast

**Prompt za diskusiju:**
```
Hoću canary deploy za [servis] sa promocijom na osnovu error-rate/latency.
Predloži strategiju (manifesti + CI koraci) i siguran rollback.
Kako da definišem health gate koji CI čeka pre nego što nastavi?
Koji readiness probe je dovoljan za ovaj servis?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Dokazati zero-downtime canary deploy sa automatskim rollback-om kada metrike padnu.

**Fajlovi koji se diraju:**
- `k8s/deployment.yaml` — dodati strategy, readiness probe i rollback annotation
- `.gitlab-ci.yml` ili ekvivalentni CI fajl — dodati health gate korak
- `.cursor/rules/deploy-checks.mdc` ili `.claude/rules/deploy-checks.md`

**Fajlovi koji se NE diraju:**
- `k8s/service.yaml` — service definicija ostaje ista tokom ovog runda
- Aplikacioni kod — deploy strategija je infrastrukturna promena

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/deploy-checks.mdc`
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/deploy-checks.md`

Sadržaj pravila (isti za oba alata):
```
- Svaki deploy ima readiness gate; CI čeka `rollout status` pre nego što nastavi na sledeći korak.
- Canary: promovisati tek ako error-rate i latency ostaju unutar SLO za definisano vreme osmatranja.
- Definisan i testiran rollback (prethodni revision ili image tag) pre svakog prod deploya.
- Bez `kubectl apply` bez prethodnog `kubectl diff` u CI-ju.
- Health check endpoint (/health ili /ready) mora vraćati 200 pre nego što rollout napreduje.
```

**Acceptance criteria:**
- [ ] `kubectl rollout status` uspeva u zadatom timeout-u (npr. 120s)
- [ ] canary se promoviše samo uz zdrave metrike (error-rate i latency unutar SLO)
- [ ] `kubectl rollout undo` vraća na prethodnu verziju i servis ostaje dostupan
- [ ] zero-downtime potvrđen: `curl` petlja ne beleži grešku tokom rollout-a
- [ ] deploy pravila ažurirana u AI-okviru

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Ažurirati deploy-checks pravila u AI-okviru
2. Pokrenuti rolling rollout i pratiti status
3. Simulovati canary sa manjim brojem replika i proveriti metrike
4. Pokrenuti rollout undo i verifikovati da servis ostaje dostupan
5. Potvrditi zero-downtime curl petljom

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta
> **Claude Code:** direktno u terminalu

Prati status rolling rollout-a:

```bash
kubectl rollout status deployment/<ime> --timeout=120s
kubectl rollout history deployment/<ime>
```

Verifikuj zero-downtime tokom rollout-a (pokreni u pozadini pre deploy-a):

```bash
while true; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://<servis>/health)
  echo "$(date +%T) — HTTP $STATUS"
  sleep 0.5
done
```

Proveri metrike canary-ja (prilagodi query za svoj observability stack):

```bash
# Primer za kubectl port-forward + PromQL
kubectl port-forward svc/prometheus 9090:9090 &
curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~'5..'}[1m])" | jq '.data.result'
```

Testiraj rollback:

```bash
kubectl rollout undo deployment/<ime>
kubectl rollout status deployment/<ime> --timeout=60s
kubectl get pods -l app=<ime> -w
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- kubectl rollout status uspeva u 120s
- canary se promoviše samo uz zdrave metrike
- kubectl rollout undo vraća prethodnu verziju, servis ostaje dostupan
- zero-downtime potvrđen curl petljom

Evo outputa:
[ovde lepiš output kubectl rollout status]
[ovde lepiš output curl petlje tokom rollout-a — da li ima grešaka?]
[ovde lepiš metrike canary-ja]
[ovde lepiš output rollout undo]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `kubectl rollout status deployment/<ime> --timeout=120s` | Ispisuje "successfully rolled out" u roku od 120 sekundi |
| 2 | Pokreni curl petlju (`while true; do curl -s /health; sleep 0.5; done`) i u toku toga triggeruj rollout | Svi HTTP odgovori su 200, nula grešaka tokom celog rollout-a |
| 3 | Proveri metrike tokom canary faze | Error-rate ostaje ispod SLO praga; latency P99 ostaje unutar limita |
| 4 | Pokreni `kubectl rollout undo deployment/<ime>` | Deployment se vratio na prethodnu reviziju; `rollout history` prikazuje ispravnu reviziju |
| 5 | Tokom rollback-a ponovo pokreni curl petlju | Nula HTTP grešaka tokom rollback-a; servis kontinuirano dostupan |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/deployment-tooling.md` ili `CLAUDE.md`

```
## [datum] — Deployment strategije sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
