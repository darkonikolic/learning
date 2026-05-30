# 07 — Vežba: DB migracije

Gradiš AI-okvir za bezbedne, reverzibilne migracije šeme po expand-contract obrascu, pa verifikuješ da `up` i `down` rade korektno i da je migracija idempotentna.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo migration-checks pravila (reverzibilnost, expand-contract, izbegavanje dugih lock-ova), pa pokrećemo konkretnu migraciju gore i dole na lokalnoj bazi i proveravamo stanje šeme nakon svakog koraka.

**Pretpostavke za potvrdu:**
- Migracioný alat je instaliran (golang-migrate, dbmate, ili Doctrine Migrations)
- Lokalna baza je dostupna i prazna ili na poznatom baseline stanju
- Aplikacija može da radi sa starom i novom verzijom šeme istovremeno (expand faza)

**Van opsega:**
- Migracije podataka (data migrations) — šema i podaci su odvojene operacije
- Automatski rollback u produkciji — to zahteva poseban runbook
- Seed podaci za testove — zasebna oblast

**Prompt za diskusiju:**
```
Treba mi da [promena šeme] bez downtime-a dok aplikacija radi.
Objasni expand-contract korake i daj reverzibilne migracije (up/down).
Koja ALTER operacija drži lock na tabeli i kako da je izbegnem?
Kako da proverim idempotentnost migracije?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Dokazati da up/down migracije rade, da je promena reverzibilna i da dvostruko pokretanje ne prave grešku.

**Fajlovi koji se diraju:**
- `migrations/` direktorijum — nova migracija fajl (up + down)
- `.cursor/rules/migration-checks.mdc` ili `.claude/rules/migration-checks.md`

**Fajlovi koji se NE diraju:**
- Aplikacioni model/entity fajlovi — menjaju se u zasebnom koraku posle migracije
- CI pipeline — dodavanje migracionog koraka u CI je sledeći task

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/migration-checks.mdc`
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/migration-checks.md`

Sadržaj pravila (isti za oba alata):
```
- Svaka migracija ima `down` korak (ili dokumentovan razlog zašto je nepovratna).
- Expand-contract za promene koje aplikacija koristi uživo: dodaj → dvostruko piši → backfill → preusmeri → ukloni.
- Izbegavaj ALTER koji drži lock na velikoj tabeli u prometu; koristi ghost ili pt-online-schema-change za velike tabele.
- Migracije su idempotentne: dvostruko pokretanje up ne pravi grešku.
- Migracije se testiraju lokalno (up + down + up) pre nego što idu u CR.
```

**Acceptance criteria:**
- [ ] `migrate up` primenjuje promenu šeme — SHOW COLUMNS potvrđuje novu kolonu/indeks
- [ ] `migrate down 1` vraća šemu na prethodno stanje — SHOW COLUMNS potvrđuje uklanjanje
- [ ] `migrate up` pokrenut drugi put ne pravi grešku (idempotentnost)
- [ ] nijedna migracija ne drži `LOCK` više od 100ms na tabeli u prometu
- [ ] migration-checks pravila zapisana u AI-okviru

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Definisati migration-checks pravila i dodati u AI-okvir
2. Pokrenuti migrate up i proveriti šemu
3. Pokrenuti migrate down i proveriti rollback
4. Pokrenuti migrate up drugi put i potvrditi idempotentnost
5. Proveriti da nema dugotrajnog lock-a

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/golang-engineer` za golang-migrate ili `/php-architect` za Doctrine
> **Claude Code:** direktno u terminalu

Pokreni migraciju gore i proveri šemu (prilagodi komande svom alatu):

```bash
# golang-migrate
migrate -path ./migrations -database "mysql://user:pass@localhost:3306/dbname" up

# dbmate
dbmate up

# Doctrine (PHP)
docker compose exec php bin/console doctrine:migrations:migrate --no-interaction
```

Proveri da je promena primenjena:

```bash
mysql -u user -ppass dbname -e "SHOW COLUMNS FROM <tabela>;"
# ili za PostgreSQL:
psql -U user -d dbname -c "\d <tabela>"
```

Pokreni rollback jednog koraka:

```bash
# golang-migrate
migrate -path ./migrations -database "mysql://user:pass@localhost:3306/dbname" down 1

# dbmate
dbmate rollback

# Doctrine
docker compose exec php bin/console doctrine:migrations:execute --down <VersionClass> --no-interaction
```

Proveri da je rollback primenjen:

```bash
mysql -u user -ppass dbname -e "SHOW COLUMNS FROM <tabela>;"
```

Pokreni `up` drugi put za idempotentnost:

```bash
migrate -path ./migrations -database "mysql://user:pass@localhost:3306/dbname" up
echo "Exit code: $?"  # mora biti 0
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- migrate up primenjuje promenu šeme
- migrate down vraća šemu na prethodno stanje
- migrate up pokrenut drugi put ne pravi grešku (idempotentnost)
- nijedna migracija ne drži LOCK više od 100ms

Evo outputa:
[ovde lepiš output migrate up]
[ovde lepiš output SHOW COLUMNS nakon up]
[ovde lepiš output migrate down]
[ovde lepiš output SHOW COLUMNS nakon down]
[ovde lepiš output drugog migrate up — exit code i poruka]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Pokreni `migrate up` na čistoj bazi | Migracija se primenjuje bez greške; SHOW COLUMNS prikazuje novu kolonu/indeks |
| 2 | Pokreni `SHOW COLUMNS FROM <tabela>` | Izlaz pokazuje tačno očekivanu promenu šeme (nova kolona prisutna, tačan tip) |
| 3 | Pokreni `migrate down 1` | Migracija se vraća bez greške; SHOW COLUMNS potvrđuje da je promena uklonjena |
| 4 | Pokreni `migrate up` odmah nakon down | Migracija se ponovo primenjuje — dvostruki ciklus potvrđuje reverzibilnost |
| 5 | Pokreni `migrate up` drugi put zaredom (bez down između) | Exit code je 0, alat javlja "no change" ili "already applied" — bez greške |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/db-migracije-tooling.md` ili `CLAUDE.md`

```
## [datum] — DB migracije sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
