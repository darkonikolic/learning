# 06 — Vežba: Priprema AI-okvira i sync (kopija baze između okruženja)

Gradiš AI-okvir koji štiti PII pri kopiranju baze iz produkcije u niža okruženja, pa verifikuješ da su podaci konzistentni, anonimizovani i da nijedan produkcijski kredencijal nije korišćen u staging procesu.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo siguran proces dump → maskiranje → restore za kopiranje prod MySQL baze u staging/dev okruženje, bez pravih PII podataka (email, ime, telefon) i bez korišćenja prod kredencijala u nižim okruženjima.

**Pretpostavke za potvrdu:**
- Prod baza je MySQL (ili prilagodi za Postgres)
- Staging instanca postoji i može primiti restore
- PII kolone su identifikovane (email, ime, telefon, adresa)
- Staging okruženje ima sopstvene kredencijale, odvojene od prod

**Van opsega:**
- Automatizacija ovog procesa u CI/CD (to je posebna vežba)
- Migracija šeme — radimo samo kopiju podataka

**Prompt za diskusiju:**
```
Treba mi kopija prod MySQL baze u dev/staging, ali bez pravih PII podataka.
Predloži kompletan proces:
- Koje kolone tipično sadrže PII i kako ih prepoznati?
- Kako da dump bude konzistentan (--single-transaction)?
- Koje SQL UPDATE naredbe maskiraju email, ime, telefon?
- Kako da verifikujem integritet posle restore-a (broj redova, checksum)?
- Koji prod kredencijali ne smeju biti korišćeni u staging procesu i kako to sprečiti?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Staging baza sadrži kopiju prod podataka sa maskiranim PII, verifikovanim integritetom, i bez traga prod kredencijala u procesu.

**Fajlovi koji se diraju:**
- `scripts/db-copy/dump.sh` — dump script sa `--single-transaction`
- `scripts/db-copy/mask-pii.sql` — SQL naredbe za maskiranje PII kolona
- `scripts/db-copy/verify-integrity.sh` — provera broja redova i checksum-a

**Fajlovi koji se NE diraju:**
- Prod `.env` ili secrets — staging dobija sopstvene kredencijale
- Produkcijska baza direktno — radimo samo dump, nikad direktan write u prod

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/db-copy-safety.md`

Sadržaj pravila:
```
- Prod → niže okruženje SAMO uz maskiranje PII (email, ime, telefon, adresa).
- Dump uvek sa --single-transaction; nikad bez toga na živoj bazi.
- Restore u izolovan namespace/instancu, nikad direktno na živu staging bazu bez backup-a.
- Verifikuj broj redova i checksum ključnih tabela posle restore-a.
- Staging proces koristi isključivo staging kredencijale — prod credentials se ne dodiruju.
- Maskirani dump se ne čuva na deljenim lokacijama; briše se posle restore-a.
```

Anti-sprawl: uvedi `db-copy-safety` — PII/pravni rizik je visok i ovaj proces se ponavlja.

**Acceptance criteria:**
- [ ] dump je konzistentan (`--single-transaction` flag prisutan u komandi)
- [ ] PII kolone (email, ime, telefon) maskirane pre ulaska u staging
- [ ] broj redova u staging odgovara prod dumpovanom skupu (ili dokumentovano zašto ne)
- [ ] staging baza ne sadrži ni jedan pravi email adrese u `users` tabeli
- [ ] nijedan prod kredencijal nije korišćen u staging restore procesu
- [ ] Sync zapisan u `.claude/memory/decisions.md` ili `CLAUDE.md ## Decision log` / `CLAUDE.md`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Dumpujemo prod bazu sa --single-transaction
- Pokrećemo mask-pii.sql na dump fajlu pre restore-a
- Restore-ujemo u staging instancu sa staging kredencijalima
- Verifikujemo broj redova i maskiranje

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Dump prod baze (konzistentan snapshot):

```bash
mysqldump \
  --single-transaction \
  --routines \
  --triggers \
  -h <prod-host> -u <prod-user> -p \
  <db-name> > dump.sql

echo "Dump veličina: $(du -sh dump.sql)"
```

Maskiranje PII kolona (primer — prilagodi tabelama projekta):

```bash
mysql <staging-db-name> -h <staging-host> -u <staging-user> -p < mask-pii.sql
# mask-pii.sql primer:
# UPDATE users SET email = CONCAT('user', id, '@example.com');
# UPDATE users SET first_name = 'Anoniman', last_name = 'Korisnik';
# UPDATE users SET phone = '000-000-0000';
```

Restore u staging (staging kredencijali — ne prod):

```bash
mysql -h <staging-host> -u <staging-user> -p <staging-db-name> < dump.sql
```

Verifikacija integriteta:

```bash
# Broj redova — uporedi sa prod
mysql -h <staging-host> -u <staging-user> -p \
  -e "SELECT COUNT(*) FROM users;" <staging-db-name>

# Verifikuj maskiranje — nijedan pravi email ne sme biti prisutan
mysql -h <staging-host> -u <staging-user> -p \
  -e "SELECT email FROM users LIMIT 10;" <staging-db-name>
# Svi emailovi moraju biti u obliku user<id>@example.com
```

Obriši dump fajl posle restore-a:

```bash
rm -f dump.sql
echo "Dump obrisan"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- dump je konzistentan (--single-transaction)
- PII kolone maskirane pre ulaska u staging
- broj redova se poklapa
- staging ne sadrži pravi email
- prod kredencijali nisu korišćeni u restore-u

Evo outputa:
[ovde lepiš: mysqldump komandu, SELECT COUNT(*) output sa prod i staging, SELECT email FROM users LIMIT 10 output iz staging]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `SELECT COUNT(*) FROM users;` u staging | Broj odgovara prod dumpovanom skupu (±5% prihvatljivo ako je subset) |
| 2 | `SELECT email FROM users LIMIT 20;` u staging | Svi emailovi su `user<id>@example.com` — nijedan pravi email |
| 3 | `SELECT first_name, last_name FROM users LIMIT 5;` u staging | Vrednosti su `Anoniman Korisnik` ili ekvivalent — ne pravi podaci |
| 4 | Proveri history bash komandi na staging serveru — nema prod lozinke | `history | grep -i password` ne pokazuje prod credentials |
| 5 | Aplikacija u staging okruženju radi login sa test korisnikom | Login uspešan — staging app čita iz staging baze sa maskiranim podacima |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — DB kopija okruženja sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
