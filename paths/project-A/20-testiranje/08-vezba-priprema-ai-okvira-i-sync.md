# 08 — Vežba: Testiranje

Gradiš AI-okvir za testove (Go test, PHP/Pest, E2E Playwright) i pokrećeš ceo test suite sa pragom pokrivenosti koji blokira CI ako nije zadovoljen.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo pravila testne piramide, postavljamo prag pokrivenosti u CI-ju i pokrećemo unit, integration i E2E testove za Go i PHP servise.

**Pretpostavke za potvrdu:**
- Go i PHP servisi imaju bar po jedan postojeći test koji prolazi
- Playwright je instaliran i konfigurisan za E2E smoke
- CI pipeline čita coverage report i može da obori build

**Van opsega:**
- Pisanje novih feature testova (samo okvir i pokrivenost)
- Mocking eksternih servisa trećih strana

**Prompt za diskusiju:**
```
Evo funkcije/servisa [kod]. Predloži unit testove za rubne slučajeve
i jedan E2E smoke; objasni zašto baš ti slučajevi nose rizik.
Koje coverage metrike su relevantne za jezgro logike nasuprot helpera?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Uspostaviti testnu piramidu sa merljivim pragom pokrivenosti koji CI blokira.

**Fajlovi koji se diraju:**
- `CLAUDE.md` ili `.claude/rules/test-checks.md`
- `Makefile` ili CI konfiguracija — dodati coverage threshold korak
- `playwright.config.ts` — smoke test konfiguracija

**Fajlovi koji se NE diraju:**
- Postojeći test fajlovi — ne brišemo testove, samo dodajemo okvir
- `docker-compose.yml` — runtime okruženje ostaje nepromenjeno

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/test-checks.md`

Sadržaj pravila:
```
- Piramida: jezgro logike pokriveno unit-testovima; integracija samo za kritične putanje; malo, stabilnih E2E.
- CI obara build ako coverage < prag (npr. 70% na jezgru logike).
- Bez sleep/retry hakova u testovima; koristi deterministička čekanja i test doubles.
- Flaky testovi se odmah izolovaju i ispravljaju, ne skipuju.
- E2E smoke pokriva samo "mora da radi" putanje, ne sve permutacije.
```

**Acceptance criteria:**
- [ ] unit testovi (Go + PHP) prolaze bez grešaka
- [ ] coverage jezgra logike iznad definisanog praga (npr. 70%)
- [ ] E2E smoke prolazi
- [ ] CI korak obara build kada coverage padne ispod praga
- [ ] pravila testne piramide zapisana u AI-okviru

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Definisati test-checks pravila i dodati ih u AI-okvir
2. Pokrenuti go test sa coverage profilom
3. Pokrenuti PHP/Pest sa coverage izveštajem
4. Pokrenuti Playwright E2E smoke
5. Verifikovati da CI korak čita threshold i pada ako nije zadovoljen

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Pokreni Go testove sa coverage profilom:

```bash
go test ./... -cover -coverprofile=cover.out
go tool cover -func=cover.out | grep total
```

Pokreni PHP testove sa coverage:

```bash
docker compose exec php ./vendor/bin/pest --coverage --coverage-min=70
```

Pokreni E2E smoke:

```bash
npx playwright test --grep @smoke
```

Proveri da CI threshold radi (lokalno simulacija):

```bash
# Primer: izvuci ukupan coverage i pali grešku ako je ispod praga
COVERAGE=$(go tool cover -func=cover.out | grep total | awk '{print $3}' | tr -d '%')
if (( $(echo "$COVERAGE < 70" | bc -l) )); then
  echo "Coverage $COVERAGE% je ispod praga 70%" && exit 1
fi
echo "Coverage OK: $COVERAGE%"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- unit testovi (Go + PHP) prolaze bez grešaka
- coverage jezgra logike iznad 70%
- E2E smoke prolazi
- CI korak obara build kada coverage padne ispod praga
- pravila testne piramide zapisana u AI-okviru

Evo outputa:
[ovde lepiš output go test, pest i playwright komandi]
[ovde lepiš sadržaj test-checks pravila]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `go test ./... -cover` | Sve funkcije prolaze, prikazan ukupan coverage procenat |
| 2 | Pokreni `pest --coverage-min=70` | Pest prolazi i ispisuje zeleni coverage izveštaj iznad 70% |
| 3 | Pokreni `npx playwright test --grep @smoke` | Sve smoke test klase prolaze, nula failova |
| 4 | Smanji prag na 99% u CI koraku i pokreni ponovo | CI korak eksplicitno pada sa porukom o coverage pragu |
| 5 | Vrati prag na 70% i ponovo pokreni | CI prolazi, build je uspešan |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Testiranje sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
