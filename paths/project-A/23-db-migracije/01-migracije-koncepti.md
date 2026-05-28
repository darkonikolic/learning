# 01 — Database Migracije: Koncepti

## Šta je database migracija

Verzionisana promjena baze podataka (schema ili data). Svaka migracija ima:
- **UP** — primijeni promjenu
- **DOWN** — vrati promjenu (rollback)

Migracije se primjenjuju **jednom, sekvencijalno, nepovratno u produkciji**. Nikada ne mijenjaj postojeći migration fajl koji je već primijenjen.

Schema migrations tracker: `schema_migrations` tabela u bazi (automatski kreirana od strane alata).

---

## Ko je vlasnik migracija za ovaj stack

| Servis | Uloga | Migracije |
|--------|-------|-----------|
| Go 1.22 service | Direktno komunicira sa MySQL | **Vlasnik schema migracija** |
| PHP 8.3 service | Proxy uloga, ne dira bazu direktno | Nema migracija |

Alat: `golang-migrate/migrate` — Go ekosistem, SQL fajlovi, Docker image dostupan, programmatic API.

---

## Zašto NE migrirati u app startup-u

```
App startup + migrate = race condition ako imaš više replika:

  Pod 1 startuje → počne migrate → schema je u middle state
  Pod 2 startuje → počne raditi sa half-migrated schemom → crash
  Pod 3 startuje → isti problem, možda drugačiji crash

Ispravno:
  K8s Job (migrate) → Job completed → Deployment rollout
```

Ovo je kritično na Kubernetesu gdje rolling update podrazumijeva da stara i nova verzija rade istovremeno. Migracija mora biti završena **prije nego što ijedan novi pod startuje**.

---

## Tri alata — nauči sve, koristi golang-migrate

| Alat | Jezik | Format | Docker | Koristiti za |
|------|-------|--------|--------|-------------|
| `golang-migrate` | Go | SQL fajlovi (zasebni up/down) | Da | **Ovaj projekat** |
| `dbmate` | Go | SQL fajlovi (jedan fajl, sekcije) | Da | Jednostavniji projekti |
| Flyway | Java | SQL/Java | Da | Enterprise, Java timovi |

---

## schema_migrations tracking

```sql
-- golang-migrate automatski kreira i upravlja ovom tabelom
SELECT * FROM schema_migrations;
```

```
version | dirty
--------|------
1       | false
2       | false
3       | false
```

- `version` — zadnja uspješno primijenjena migracija
- `dirty = true` — migracija je pala na pola → baza je u nekonzistentnom stanju → potrebna je ručna intervencija

---

## Sekvencijalnost je zakon

```
Migracija 1: CREATE TABLE users
Migracija 2: ADD COLUMN email_verified_at (ovisi o migraciji 1)
Migracija 3: CREATE TABLE sessions (ovisi o migraciji 1)

Svaka migracija mora biti idempotentna po smislu:
  - Primijenjena jednom → OK
  - Primijenjena drugi put → greška (već postoji)
  - zato DOWN mora čisto brisati sve što je UP kreirao
```

---

## Principi za produkciju

1. **Nikada ne mijenjaj primijenjen migration fajl** — dodaj novu migraciju za ispravke
2. **DOWN migracija u produkciji = gubitak podataka** — koristiti samo u razvoju
3. **Expand-contract za zero-downtime** — vidi `03-expand-contract-pattern.md`
4. **Test na staging s produkcijskom veličinom podataka** prije prod deploymenta
5. **Timeout za K8s Job** — migracija koja visi blokira deployment
