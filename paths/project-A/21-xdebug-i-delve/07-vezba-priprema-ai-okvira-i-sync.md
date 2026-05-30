# 07 — Vežba: Xdebug i Delve

Podešavaš Xdebug za PHP i Delve za Go unutar dev kontejnera, pa potvrđuješ da se breakpoint pogađa u IDE-u sa vidljivim vrednostima promenljivih.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Konfigurišemo Xdebug (PHP, port 9003) i Delve (Go, port 2345) isključivo u dev Docker compose override-u, verifikujemo step-through debug u IDE-u, i osiguravamo da ništa od debug konfiguracije ne ode u prod image.

**Pretpostavke za potvrdu:**
- IDE (PhpStorm ili VS Code) je konfigurisan da prihvata debug konekciju na odgovarajućem portu
- Docker compose override fajl (`docker-compose.override.yml`) postoji ili se pravi sada
- Prod image build target je odvojen od dev targeta

**Van opsega:**
- Profajliranje (Xdebug profiler mode, pprof) — to je zasebna oblast
- Remote debug na staging/prod okruženju

**Prompt za diskusiju:**
```
Hoću Xdebug za PHP i Delve za Go, ali samo u dev kontejnerima.
Daj compose override + IDE konfiguraciju i objasni kako da debug ne ode u prod.
Koji Xdebug mode je pravi za step-through (ne coverage, ne profiler)?
Kako da proverim da Delve radi pre nego što otvorim IDE?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Funkcionalan step-through debug za PHP i Go u Docker dev okruženju, bez curenja u prod.

**Fajlovi koji se diraju:**
- `docker-compose.override.yml` — dodati debug portove i env varijable
- `php/Dockerfile` — debug build target sa Xdebug ekstenzijom
- `go/Dockerfile` — debug build target sa Delve instalacijom
- `CLAUDE.md` ili `.claude/rules/debug-checks.md`

**Fajlovi koji se NE diraju:**
- `docker-compose.yml` (prod compose) — debug ne sme ovde da se pojavi
- `php/Dockerfile` prod stage — Xdebug ne ide u final/prod stage
- Aplikacioni kod — samo infrastruktura se menja

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/debug-checks.md`

Sadržaj pravila:
```
- Xdebug i Delve samo u dev/debug build target-u, nikad u prod image-u.
- Debug portovi (9003 za Xdebug, 2345 za Delve) izloženi samo u docker-compose.override.yml.
- XDEBUG_MODE=debug (ne coverage, ne profiler) za step-through sesiju.
- Delve pokretan sa --headless i --api-version=2 za IDE integraciju.
- Prod Dockerfile mora proći `docker build --target prod` bez debug zavisnosti.
```

**Acceptance criteria:**
- [ ] PHP breakpoint se pogađa kroz Xdebug — IDE se zaustavlja na liniji
- [ ] Go breakpoint se pogađa kroz Delve — IDE prikazuje stack i promenljive
- [ ] `docker build --target prod` ne sadrži Xdebug ni Delve
- [ ] debug portovi nisu izloženi u prod compose fajlu
- [ ] IDE konfiguracija (launch.json ili PhpStorm run config) je dokumentovana

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Dodati Xdebug u PHP dev Dockerfile target
2. Dodati Delve u Go dev Dockerfile target
3. Definisati debug portove u docker-compose.override.yml
4. Potvrditi da prod build ne sadrži debug alate
5. Testirati breakpoint u IDE-u za oba servisa

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Proveri da Xdebug je aktivan u PHP kontejneru:

```bash
docker compose exec php php -i | grep -E "xdebug|XDEBUG_MODE"
```

Pokreni Delve u Go kontejneru (headless, čeka IDE konekciju):

```bash
docker compose exec go dlv debug ./cmd/server --headless --listen=:2345 --api-version=2
```

Proveri da prod image ne sadrži debug alate:

```bash
docker build --target prod -t myapp:prod-check .
docker run --rm myapp:prod-check php -i | grep xdebug || echo "OK: Xdebug nije u prod"
docker run --rm myapp:prod-check which dlv 2>/dev/null || echo "OK: Delve nije u prod"
```

Postavi testni breakpoint — u PHP:

```bash
# 1. U IDE-u: postavi breakpoint na liniju u nekom PHP kontroleru/servisu
# 2. Okini HTTP request ka tom endpointu:
curl -v http://localhost:8080/some-endpoint
# 3. IDE treba da se zaustavi na breakpointu
```

Postavi testni breakpoint — u Go:

```bash
# 1. U IDE-u (VS Code): otvori launch.json, dodaj remote attach na localhost:2345
# 2. Pokreni debug sesiju iz IDE-a
# 3. Okini request ili pokreni test koji prolazi kroz breakpointovanu funkciju
curl -v http://localhost:8081/some-go-endpoint
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- PHP breakpoint se pogađa kroz Xdebug — IDE se zaustavlja na liniji
- Go breakpoint se pogađa kroz Delve — IDE prikazuje stack i promenljive
- docker build --target prod ne sadrži Xdebug ni Delve
- debug portovi nisu izloženi u prod compose fajlu

Evo outputa:
[ovde lepiš output php -i | grep xdebug]
[ovde lepiš screenshot ili opis IDE debug sesije — gde se zaustavio, koje promenljive su vidljive]
[ovde lepiš output docker run prod-check komandi]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `docker compose exec php php -i \| grep xdebug` | Ispisuje Xdebug verziju i `XDEBUG_MODE=debug` |
| 2 | Postavi breakpoint u PHP kontroleru i okini HTTP request | IDE se zaustavlja na toj liniji; vidljive su lokalne promenljive i call stack |
| 3 | Step-over kroz 3 linije u PHP debug sesiji | IDE prelazi liniju po liniju, vrednosti promenljivih se ažuriraju |
| 4 | Pokreni Delve i povezi se iz IDE-a, okini Go endpoint | IDE se zaustavlja na Go breakpointu; goroutine, stack frame i promenljive su vidljivi |
| 5 | Pokreni `docker build --target prod` i proveri output | Prod image ne sadrži Xdebug ekstenziju ni `dlv` binarni fajl |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Xdebug i Delve sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
