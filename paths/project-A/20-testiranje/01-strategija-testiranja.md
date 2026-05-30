# 01 — Strategija testiranja

## Test piramida za ovaj stack

```
        ┌─────────────────────────┐
        │    E2E (Playwright)     │  ← mali broj, visoka vrijednost, sporo
        │  review app / staging   │
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │   Integration tests     │  ← testiraju service boundary
        │  Go+MySQL, PHP+Go, Redis│
        └───────────┬─────────────┘
                    │
        ┌───────────▼─────────────┐
        │      Unit tests         │  ← brzi, izolirani, većina coverage-a
        │  svaki servis, svaki PR │
        └─────────────────────────┘
```

Piramida nije samo metafora — ona opisuje omjer troškova. Unit test koji pada za 10ms govori točno šta je puklo. E2E test koji pada za 30 sekundi govori da nešto nije u redu, ali ne govori gdje. Više unit testova znači manje debuggiranja u skupim slojevima.

---

## Šta testirati po servisu

### Go service (auth + backend API)

| Sloj | Šta | Pristup |
|------|-----|---------|
| Auth logika | validateLogin, token generation, expiry | Unit test — nema I/O |
| MySQL query layer | INSERT/SELECT/UPDATE pravilno mapiraju na structs | Integration — Testcontainers |
| Redis cache hit/miss | Cache miss dohvaća iz DB, hit vraća iz cache-a | Integration — Testcontainers Redis |
| HTTP handlers | Status kodovi, response body, error paths | `httptest` — nema network |
| Middleware | Auth header parsing, rate limiting logika | Unit test ili httptest |

Go ima odlično ugrađeno `testing` pakovanje — nema razloga koristiti framework. Testcontainers-go daje pravu MySQL i Redis instancu u Docker containeru koji živi koliko i test i automatski se briše.

### PHP service (proxy + session)

| Sloj | Šta | Pristup |
|------|-----|---------|
| Request proxy logika | Prosljeđuje zahtjev Go servisu s ispravnim headerima | Unit test s Mockery |
| Session handling | Session se kreira, čita, briše ispravno | Unit test, mock storage |
| Input validation | Email format, dužina, SQL injection pattern reject | Unit test — data dataset |
| Error propagation | Go servis vrati 401 → PHP vrati 401 | Integration mock ili Testcontainers |

PHP proxy je thin sloj — majority logike živi u Go. Testovi stoga fokusirani na: da li PHP ispravno prosljeđuje, da li ispravno parsira odgovor, da li ispravno obrađuje greške.

### Vue.js (frontend)

| Sloj | Šta | Pristup |
|------|-----|---------|
| Komponente | Render, props, emits, computed | Vitest + Vue Test Utils |
| Store (Pinia) | State transitions, actions | Vitest, isolated store |
| API integration | Axios mock, response handling | Vitest s vi.mock() |
| E2E flow | Login, navigacija, form submit | Playwright (zasebni stage) |

Vue komponente se ne testiraju Playwrightom direktno — to je skupo i sporo. Playwright testira integrisani sistem. Vitest testira izoliranu komponentu za 5ms.

---

## Šta NE testirati

**Infrastructure as Code (Terraform):**
Terraform plan/apply nije aplikacijska logika. `terraform validate` i `terraform plan` u CI-ju su dovoljni. Testiranje da li se S3 bucket kreira nije unit test — to je end-to-end infrastruktura.

**Kubernetes manifesti:**
`kubectl apply --dry-run=client` za syntax validation. Helm `helm lint` za chart validation. Funkcionalno testiranje K8s manifesta = deployment u cluster = nije unit test.

**nginx config:**
`nginx -t` u CI-ju za syntax check. Funkcionalna konfiguracija se verificira kroz E2E (da li app radi iza nginx-a).

**Vendor/third-party kod:**
Ne testiramo da MySQL radi. Ne testiramo da JWT library ispravno generiše token. Testiramo OUR logiku koja koristi te alate.

---

## Merge requirements

```
Merge allowed ←→ unit tests PASS + E2E PASS
```

Implementacija u GitLab:

1. **Settings → Merge Requests → "Pipelines must succeed"** — blokira merge ako ijedan job u pipeline-u padne
2. **Required approval count** — bar jedan reviewer mora approvati
3. **Protected branch rules** — `main` branch: push zabranjen, merge samo kroz MR

Redosljed u pipeline-u je bitan:
```
test → build → deploy (review app) → e2e → merge allowed
```

E2E ne može raditi bez deploymenta review app-a. Build ne počinje dok testovi ne prođu. Merge nije moguć dok E2E ne prođe.

---

## Test isolation princip

**Svaki test mora biti independent.** Ovo nije preporuka — ovo je hard requirement.

Šta znači isolated test:
- Ne ovisi o tome koji test je prethodno pokrenuo
- Ne ovisi o redoslijedu izvršavanja
- Ne dijeli state s drugim testovima (DB stanje, Redis keys, global varijable)
- Može se pokrenuti sam (`go test -run TestUserLogin ./...`) i dati isti rezultat

Zašto ovo nije uvijek intuitivno:

```go
// BAD: test ovisi o prethodnom testu koji je kreirao usera
func TestLoginExistingUser(t *testing.T) {
    // Pretpostavlja da je TestCreateUser već pokrenuo i kreirao user-a
    // Radi lokalno, puca u CI jer go test ne garantuje redoslijed
    resp := loginUser("existing@test.com", "pass")
    assert.Equal(t, 200, resp.StatusCode)
}

// GOOD: test kreira vlastiti state, čisti za sobom
func TestLoginExistingUser(t *testing.T) {
    // Arrange: kreiraš što trebaš
    user := createTestUser(t, "login-test@test.com", "pass")
    t.Cleanup(func() { deleteUser(t, user.ID) })

    // Act
    resp := loginUser("login-test@test.com", "pass")

    // Assert
    assert.Equal(t, 200, resp.StatusCode)
}
```

`t.Cleanup()` se izvršava čak i kad test padne — garantira čišćenje. Ovo je ekvivalent `defer` ali vezan uz test lifecycle.

Za testcontainers: svaki integration test koji treba bazu dobiva svoju čistu bazu (ili barem transaction rollback na kraju). Dijeljenje baze između testova u parallelnom izvršavanju garantira flaky testove.

---

## Makefile — dodaj u ovom poglavlju

Ovo poglavlje uvodi strategiju testiranja. Dodaj u `Makefile` u korenu projekta:

```makefile
# === OBLAST 20: Testiranje ===

test-go: ## Pokreni Go unit testove sa race detektorom
	docker run --rm \
	  -v $(PWD):/app -w /app \
	  golang:1.22-alpine go test -race ./...

test-php: ## Pokreni PHP testove sa Pest
	docker compose run --rm php ./vendor/bin/pest

test-e2e: ## Pokreni Playwright E2E testove
	docker run --rm \
	  -v $(PWD):/app -w /app \
	  mcr.microsoft.com/playwright:latest \
	  npx playwright test
```

Centralni Makefile već sadrži ove targete — ovo je referenca šta si dodao u ovoj oblasti.

Provjeri da targeti rade:
```bash
make test-go
make test-php
make help | grep "^test-"
```
