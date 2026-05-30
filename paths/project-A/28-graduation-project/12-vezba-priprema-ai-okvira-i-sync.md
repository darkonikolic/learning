# 12 — Vežba: Graduation — Konsolidacija AI okvira i End-to-End

Završna vežba konsoliduje ceo AI okvir izgrađen kroz module 00–27 i vozi kompletan end-to-end tok — od `docker compose up` do produkcijskog rollout-a sa monitoringom i rollback-om.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Prolazimo kroz ceo AI okvir (sva pravila, agenti, skills) izgrađen kroz oblasti 00–27. Identifikujemo šta se preklapa, šta je neiskorišćeno i šta nedostaje. Zatim pokrćemo kompletan end-to-end tok i validiramo da svaki korak prolazi. Ovo je čišćenje i verifikacija, ne dodavanje.

**Pretpostavke za potvrdu:**
- Sva pravila iz svih oblasti su zapisana na jednom mestu (`.cursor/rules/` ili `CLAUDE.md`)
- Stack se može podići jednom komandom (`docker compose up`)
- GitLab CI pipeline ima sve faze: lint → test → security scan → build → deploy
- Rollback mehanizam je implementiran (Kubernetes rollout undo ili docker compose prethodni tag)

**Van opsega:**
- Dodavanje novih pravila koja nisu bila deo učenja (ovo je konsolidacija, ne ekspanzija)
- Produkciona konfiguracija izvan project-A konteksta
- Refaktorisanje aplikacionog koda (fokus je na okviru i pipeline-u)

**Prompt za diskusiju:**
```
Evo celog AI okvira (sva pravila po oblastima): [nalepi inventar]
i liste oblasti koje smo prošli (00-27).

Pre "diplome", proveri:
1. Koja pravila se preklapaju — šta možemo spojiti ili obrisati?
2. Da li svaki artefakt ima jasnu oblast primene i trigger?
3. Da li nešto u end-to-end toku (docker → CI → deploy → monitoring) nije pokriveno?
4. Da li "project-a-workflow" (plan→diskusija→egzekucija→validacija→sync) važi za sve module?

Predloži šta treba konsolidovati — nemoj ništa automatski menjati.
Koji alat koristiti: Cursor, Claude Code, ili oba — i kada?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene — ili **Claude Code:** `/plan` u terminalu
> Oba alata su prihvatljiva za graduation; možeš koristiti oba paralelno.

**Cilj:** Jedan konsolidovan AI okvir bez duplikata; kompletan E2E tok potvrđen.

**Fajlovi koji se diraju:**
- `.cursor/rules/*.mdc` — spajanje ili brisanje preklapajućih pravila (Cursor)
- `CLAUDE.md` ili `.claude/rules/` — konsolidacija za Claude Code
- `.cursor/memory/decision_log.md` — finalni sync zapis
- `docs/decisions/` — finalni Claude Code sync zapisi

**Fajlovi koji se NE diraju:**
- Aplikacioni kod — nije u fokusu graduation vežbe
- `go.mod` / `go.sum` — bez dependency promena
- Proto fajlovi — bez novih RPC-ova

**AI okvir za ovu oblast:**

> **Cursor:** pregledi `.cursor/rules/` folder i ukloni/spoji duplikate
> **Claude Code:** pregledi `CLAUDE.md` sekcije i uradi isto

Finalni kriterijum konsolidovanog okvira:
```
- Nijedan artefakt (rule, skill, agent) nema duplikat sa istom svrhom.
- Svako pravilo ima jasnu oblast primene: koja oblast, koji trigger, šta blokira.
- Sve oblasti 00-27 imaju barem jedno pravilo koje ih pokriva.
- project-a-workflow (plan→diskusija→egzekucija→validacija→sync) dokumentovan
  i primenjen u svim modulima.
- Neiskorišćena pravila su obrisana, ne samo zakomentarisana.
```

**Acceptance criteria:**
- [ ] Inventar okvira kompletan — nema nepoznatih ili neiskorišćenih pravila
- [ ] Nema dupliranih pravila koja pokrivaju istu stvar različitim imenima
- [ ] Ceo stack se diže: `docker compose up -d --build` + `docker compose ps` all healthy
- [ ] CI lanac prolazi: lint → test → security scan → build → deploy (sve faze zelene)
- [ ] `kubectl rollout status` potvrđuje uspešan deploy
- [ ] E2E smoke test prolazi (`curl -fsS https://<host>/health` vraća 200)
- [ ] Rollback je demonstriran i radi
- [ ] Monitoring alert se aktivira na simuliranoj grešci
- [ ] Finalni sync zapisan

**AI pregled plana:**
```
Evo plana za graduation konsolidaciju:
1. Inventar svih pravila po oblastima
2. Identifikacija duplikata i neiskorišćenog
3. Konsolidacija (spajanje/brisanje)
4. E2E tok: docker → CI → deploy → smoke → rollback → alert
5. Finalni sync

Da li su acceptance criteria merljivi i testabilni?
Šta od 00-27 oblasti možda nije pokriveno nijednim pravilom?
Koji deo E2E toka najčešće pada — šta da pratim posebno?
```

---

## 3. Egzekucija

> **Cursor:** koristiš relevantnog agenta — ili **Claude Code:** direktno u terminalu
> Preporučeno: koristi oba alata da proveriš njihovu konzistentnost na istom projektu.

Kompletan end-to-end tok:

```bash
# 1. Digne ceo stack
docker compose up -d --build
docker compose ps   # sve mora biti healthy/running

# 2. CI lint pre push-a
glab ci lint

# 3. Lokalni testovi
go test ./... -race -count=1

# 4. Security scan lokalno
docker run --rm -v "$PWD":/src returntocorp/semgrep semgrep --config=auto /src
docker run --rm -v "$PWD":/src aquasec/trivy fs /src

# 5. Build i push image-a (ako je lokalni registry)
docker build -t registry.example.com/project-a:$(git rev-parse --short HEAD) .
docker push registry.example.com/project-a:$(git rev-parse --short HEAD)

# 6. Deploy
kubectl apply -f k8s/
kubectl rollout status deployment/project-a --timeout=120s

# 7. E2E smoke test
curl -fsS https://<host>/health
curl -fsS https://<host>/api/v1/status

# 8. Rollback test
kubectl rollout undo deployment/project-a
kubectl rollout status deployment/project-a --timeout=60s
curl -fsS https://<host>/health   # prethodna verzija mora da radi

# 9. Monitoring — simuliraj grešku i proveri alert
# (detalji zavise od monitoring stack-a koji si implementirao)
```

---

## 4. AI validacija

```
Evo acceptance criteria graduation vežbe:
- Inventar okvira kompletan, bez duplikata
- Stack se diže, sve healthy
- CI lanac zelen (lint → test → scan → build → deploy)
- Rollout status uspešan
- E2E smoke prolazi
- Rollback demonstriran
- Alert se aktivira

Evo outputa docker compose ps, kubectl rollout status, curl smoke, i inventara pravila:
[ovde lepiš stvarni output]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?

Dodatno: Da li postoje oblasti (00-27) koje nemaju nijedno pravilo u okviru?
Da li ima pravila koja nikad nisu bila triggerovana u ovom projektu — kandidati za brisanje?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `docker compose up -d --build && docker compose ps` | Svi servisi u stanju `running` ili `healthy`; nema `exited` ili `restarting` |
| 2 | Pokreni GitLab CI pipeline na main grani | Sve faze zelene: lint ✓, test ✓, security ✓, build ✓, deploy ✓ |
| 3 | `curl -fsS https://<host>/health` | HTTP 200 sa validnim JSON health response-om |
| 4 | Prođi kompletan korisnički tok kroz deployed aplikaciju (registracija → login → akcija → logout) | Svaki korak radi bez grešaka; response kodovi ispravni |
| 5 | `kubectl rollout undo deployment/project-a` | Rollback uspešan; prethodna verzija servira zahteve; `curl /health` vraća 200 |
| 6 | Simuliraj grešku (uglasi endpoint, premaši error rate) | Monitoring alert se aktivira u roku od 2-3 minuta (Prometheus/Grafana ili GitLab alert) |
| 7 | Preglej konsolidovani AI okvir u `.cursor/rules/` ili `CLAUDE.md` | Nema duplikata; svako pravilo ima jasnu oblast; neiskorišćeno je obrisano |

**Sync — zatvori petlju (finalni):**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/graduation-sync.md` ili `CLAUDE.md`
> Preporučeno: zapiši u oba, jer je ovo graduation — finalni dokument celog učenja.

```
## [datum] — Graduation sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
