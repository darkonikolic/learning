# 08 — Vežba: priprema AI-okvira i sync (testiranje)

Pripremaš AI-okvir za testove (Go test, PHP/Pest, E2E), pa pokrećeš testove sa pragom pokrivenosti.

## Cilj

- okvir koji pokriva piramidu testova i prag pokrivenosti u CI-ju
- dokazano: testovi prolaze, pokrivenost iznad praga, E2E smoke radi

## Deo A — Priprema AI-okvira za testiranje

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Go persona | da | `/golang-engineer` |
| PHP persona | da | `/php-architect` |
| Test/coverage checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `test-checks` (piramida: više unit nego E2E; coverage prag u CI; bez flaky `sleep` u testovima). Uvedi — testovi se tiču svih servisa.

### A3 — Minimalni dodatak (primer)

```
# kandidat: test-checks
- Piramida: jezgro logike unit-testovima; malo, stabilnih E2E.
- CI obara build ako coverage < prag (npr. 70% na jezgru).
- Bez sleep/retry hakova; koristi deterministička čekanja.
```

## Deo B — Praktičan rad (sync)

### Pokretanje testova

```bash
go test ./... -cover -coverprofile=cover.out
docker compose exec php ./vendor/bin/pest --coverage
npx playwright test     # E2E smoke
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] unit testovi (Go + PHP) prolaze
- [ ] pokrivenost jezgra iznad praga
- [ ] E2E smoke prolazi
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Evo funkcije/servisa [kod]. Predloži unit testove za rubne slučajeve
i jedan E2E smoke; objasni zašto baš ti slučajevi nose rizik.
```
