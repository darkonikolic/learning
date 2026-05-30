# 06 — Vežba: Performance Testing

Definišeš SLO pragove, pokrećeš k6 load test i verifikuješ da servis zadovoljava P95 latenciju i error rate pod opterećenjem.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Pišemo k6 skriptu sa realnim ramp-up profilom i `thresholds` za P95 latenciju i error rate. Pokrećemo test, čitamo rezultat i identifikujemo bottleneck ako prag padne.

**Pretpostavke za potvrdu:**
- Endpoint je dostupan i vraća 200 pod normalnim opterećenjem
- SLO pragovi su dogovoreni pre testa (ne biramo ih posle)
- Profiling (pprof) se koristi samo ako test padne — ne pre merenja

**Van opsega:**
- Chaos engineering / fault injection
- Dugoročni soak test (trajanje > 30 min)
- Tuning baze ili infrastrukture (to dolazi nakon identifikovanog bottleneck-a)

**Prompt za diskusiju:**
```
Hoću k6 load test za [endpoint] sa pragom p95 < 200ms i error rate < 1%.
Daj skriptu sa thresholds i realnim ramp-up profilom (ne samo max RPS odmah).
Objasni kako da čitam k6 output i kada da pokrenem Go pprof profiling.
Koji su tipični bottleneck-ovi za ovakav endpoint (DB, N+1, lock contention)?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** K6 test sa definisanim pragovima prolazi; bottleneck identifikovan ako padne.

**Fajlovi koji se diraju:**
- `load-tests/load.js` — k6 skripta sa thresholds i ramp-up profilom
- `load-tests/README.md` — opis pragova i kako pokrenuti

**Fajlovi koji se NE diraju:**
- Aplikacioni kod — performance fix dolazi u posebnom tasku ako bottleneck nađeš
- `go.mod` / `go.sum` — nema dependency promena u ovoj vežbi

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/perf-test-checks.md`

Sadržaj pravila:
```
- Definiši prag PRE testa (p95 < Xms, error rate < Y%); ne beri pragove posle.
- Profil opterećenja realan: ramp-up faza, plato, ramp-down — ne samo max RPS odmah.
- Profiling (pprof, trace) tek kad test padne — meri, ne nagađaj bottleneck.
- k6 thresholds moraju biti u skripti, ne samo opisani u tekstu.
- Svaki load test mora imati README sa: šta testiramo, pragovi, kako pokrenuti.
```

**Acceptance criteria:**
- [ ] K6 skripta ima eksplicitne `thresholds` (P95 i error rate)
- [ ] Skripta ima ramp-up fazu (nije odmah max load)
- [ ] Test prolazi postavljene pragove ILI je bottleneck jasno identifikovan i dokumentovan
- [ ] K6 HTML report generisan i čitljiv
- [ ] Profiling pokrenut samo posle pada testa (ne pre)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Napisati k6 skriptu sa thresholds i ramp-up profilom
2. Pokrenuti lokalno i pročitati output
3. Ako prag padne — pokrenuti pprof i identifikovati bottleneck

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno — posebno oko realnog profila opterećenja?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Pokreni k6 test:

```bash
# Standardni run sa k6 Docker slikom
docker run --rm -i grafana/k6 run - < load-tests/load.js

# Sa HTML report-om
docker run --rm -i -v "$PWD/load-tests":/results grafana/k6 run \
  --out json=/results/result.json - < load-tests/load.js

# Go profiling — SAMO ako test padne
go tool pprof http://<host>:6060/debug/pprof/profile?seconds=30
go tool pprof http://<host>:6060/debug/pprof/heap
```

Primer minimalne k6 skripte sa thresholds:

```js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // ramp-up
    { duration: '1m',  target: 20 },   // plato
    { duration: '10s', target: 0 },    // ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200'],  // P95 < 200ms
    http_req_failed:   ['rate<0.01'],  // error rate < 1%
  },
};

export default function () {
  const res = http.get('https://<host>/api/endpoint');
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(1);
}
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- K6 skripta ima thresholds (P95 i error rate)
- Skripta ima ramp-up fazu
- Test prolazi pragove ILI je bottleneck identifikovan
- K6 HTML report generisan

Evo k6 outputa i (ako prag pao) pprof rezultata:
[ovde lepiš stvarni output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali i koji je sledeći korak za optimizaciju?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni k6 test, prati live output | Vidljive su metrike po fazama (ramp-up, plato); P95 i error rate se ispisuju |
| 2 | Test završi | K6 prikazuje `✓` za svaki threshold koji je prošao |
| 3 | Namerno smanji threshold ispod trenutnih vrednosti | K6 prikazuje `✗` i izlazi sa exit code != 0 |
| 4 | Otvori generisan HTML report u browseru | Report čitljiv, prikazuje P95, P99, error rate i profile grafikon |
| 5 | Ako P95 prelazi prag: pokreni pprof i identifikuj top 3 funkcije po CPU | pprof flamegraph prikazuje konkretne funkcije, ne generički "runtime" |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Performance Testing sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
