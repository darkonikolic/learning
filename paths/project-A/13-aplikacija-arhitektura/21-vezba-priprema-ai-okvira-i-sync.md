# 21 — Vežba: Arhitektura aplikacije (multi-servisni stack)

Validiraš AI-okvir za multi-servisnu aplikaciju (Vue SPA, PHP API proxy, Go backend, MySQL, Redis) i dokazuješ da se ceo stack diže sa ispravnim zdravstvenim stanjem i end-to-end komunikacijom.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Uvodimo rule `service-contract-checks` koji definiše granice između servisa (SPA → PHP proxy → Go backend), health endpoint standard i compose higijenu. Dokazujemo da stack radi kroz smoke test celog lanca.

**Pretpostavke za potvrdu:**
- `docker compose` je instaliran (v2, ne legacy `docker-compose`)
- PHP proxy sluša na portu 8080, Go backend na 9090
- MySQL i Redis su definisani u compose fajlu sa healthcheck-ovima
- SPA nema direktan pristup Go backend-u — sve ide kroz PHP proxy

**Van opsega:**
- Produkcioni deployment (Kubernetes, ECS)
- SSL/TLS termination
- Autentikacija i autorizacija između servisa

**Prompt za diskusiju:**
```
Imam SPA → PHP proxy → Go backend → MySQL/Redis.
Predloži docker-compose sa healthcheck-ovima i ispravnim depends_on
da se diže pouzdano (bez sleep hakova).
Potom objasni: zašto SPA ne sme direktno zvati Go backend,
i kako PHP proxy enforces tu granicu.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene  
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Uvesti `service-contract-checks` rule i dokazati da svi servisi stanu zdravi i da poziv kroz ceo lanac vraća 200.

**Fajlovi koji se diraju:**
- `docker-compose.yml` — dodaješ healthcheck-ove i depends_on ako nedostaju
- `.cursor/rules/service-contract-checks.mdc` ili `CLAUDE.md` — novi rule

**Fajlovi koji se NE diraju:**
- `src/vue/` — aplikacioni kod SPA-e ostaje nepromenjen
- `src/php/` — proxy logika se ne menja u ovoj vežbi
- `src/go/` — backend kod se ne menja

**AI okvir za ovu oblast:**

> **Cursor:** napravi `.cursor/rules/service-contract-checks.mdc`  
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/service-contract-checks.md`

Sadržaj pravila (isti za oba alata):
```
# service-contract-checks
- Svaki servis izlaže /health endpoint koji vraća 200 kada je spreman.
- Granice: SPA → PHP proxy → Go backend; bez preskakanja slojeva (nema direktnog SPA→Go).
- docker-compose: depends_on sa condition: service_healthy, ne sleep.
- Sve konfiguracije dolaze iz env varijabli (12-factor), ne hardkodovane.
- PHP proxy ne sme eksponovati interni Go URL klijentu.
```

Anti-sprawl: uvodi se jer arhitektura dodiruje PHP, Go i Docker oblasti — zajednički rule ima smisla.

**Acceptance criteria:**
- [ ] `docker compose up -d --build` završava bez grešaka
- [ ] `docker compose ps` prikazuje sve servise kao `healthy`
- [ ] `curl -fsS localhost:8080/health` vraća HTTP 200 (PHP proxy)
- [ ] `curl -fsS localhost:9090/health` vraća HTTP 200 (Go backend)
- [ ] Poziv kroz ceo lanac (SPA → PHP → Go → DB) vraća očekivani odgovor
- [ ] Nema direktnog SPA → Go poziva (PHP proxy enforces granicu)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Napraviti service-contract-checks rule
2. Proveriti docker-compose.yml za healthcheck-ove i depends_on
3. Pokrenuti docker compose up -d --build
4. Proveriti docker compose ps
5. Curl smoke test kroz svaki health endpoint i ceo lanac

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta  
> **Claude Code:** direktno u terminalu

Podizanje stack-a:

```bash
docker compose up -d --build
```

Provera stanja servisa:

```bash
docker compose ps
```

Smoke test health endpoint-a:

```bash
curl -fsS localhost:8080/health     # PHP proxy
curl -fsS localhost:9090/health     # Go backend
```

End-to-end poziv kroz ceo lanac:

```bash
curl -fsS localhost:8080/api/ping   # SPA → PHP proxy → Go backend → DB
```

Provera da SPA nema direktan pristup Go backend-u (port 9090 ne sme biti izložen van Docker mreže):

```bash
curl -fsS localhost:9090/api/ping   # Mora da ne radi spolja ili je zaštićen
docker network inspect <mreza>      # SPA container nema direktan link ka Go
```

Logovi za dijagnostiku ako nešto ne stane:

```bash
docker compose logs --tail=50 php-proxy
docker compose logs --tail=50 go-backend
docker compose logs --tail=50 mysql
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- docker compose up --build završava bez grešaka
- docker compose ps: svi servisi healthy
- curl localhost:8080/health vraća 200
- curl localhost:9090/health vraća 200
- End-to-end poziv kroz PHP proxy radi
- Nema direktnog SPA→Go pristupa

Evo outputa / diff-a / konfiguracije:
[ovde lepiš: output docker compose ps, curl outpute, docker compose logs ako ima grešaka]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `docker compose ps` | Svi servisi u koloni Status prikazuju `healthy` |
| 2 | `curl -fsS localhost:8080/health` | Vraća HTTP 200 i JSON body sa statusom |
| 3 | `curl -fsS localhost:9090/health` | Vraća HTTP 200 i JSON body sa statusom |
| 4 | `curl -fsS localhost:8080/api/ping` | Odgovor putuje kroz PHP proxy do Go backend-a i vraća se |
| 5 | Pokušaj direktno `curl localhost:9090/api/ping` iz hosta | Port nije dostupan ili je vraćen error (SPA nema direktan put) |
| 6 | Zaustavi MySQL kontejner, proveri PHP proxy | PHP proxy prijavljuje grešku, ne pada bez poruke |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`  
> **Claude Code:** zapiši u `docs/decisions/arhitektura-tooling.md` ili `CLAUDE.md`

```
## [datum] — Arhitektura aplikacije sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
