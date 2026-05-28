# 01 — Strategija kopiranja baze između okruženja

## Zašto kopija prod podataka u lower envs?

Testiranje sa mock podacima je privlačno jer je jednostavno, ali u praksi krije klasu grešaka koje mock podaci nikad ne otkrivaju.

### Realni test data umjesto mock podataka

Prod baza sadrži distribuciju podataka koja odražava stvarno korištenje: neujednačene dužine stringova, NULL vrijednosti u neočekivanim kolonama, rubni slučajevi koji nikad nisu zabilježeni u specifikaciji. Mock data generatori produciraju "ureden" set podataka koji prolazi kroz svaki query bez problema — i upravo su ti ne-uredeni slučajevi ono što u prod okida bugove.

Konkretni primjeri iz prakse:
- Query koji radi perfektno na 100 mock redova, ali puca na 50.000 prod redova zbog missing index i full table scan
- `GROUP BY` koji vraća pogrešne rezultate jer prod podaci sadrže duplicirane composite key vrijednosti koje mock nikad ne generira
- Timezone mismatch koji se manifestuje samo sa stvarnim timestamp-ovima koji prelaze DST granicu

### Otkrivanje schema/data mismatch grešaka

Svaka migracija koja dodaje `NOT NULL` kolonu bez `DEFAULT` vrijednosti potencijalno razbija restore na dev ako dev baza ima stariji schema. Kopija prod sheme u dev okruženju znači da schema mismatch greška bude uhvaćena u dev, a ne tek u prod deploymentu.

Schema drift između okruženja je jedna od najopasnijih tiha grešaka u DevOps pipelinu. Ako dev baza živi tjednima bez svježe kopije, schema divergencija postaje gotovo zajamčena.

### Reprodukcija prod bugova lokalno

Kada korisnik prijavi bug koji se ne može reproducirati lokalno, prva hipoteza uvijek treba biti: "jesu li podaci identični?". Sa kopijom prod baze, dev može lokalno reproducirati egzaktno stanje koje je uzrokovalo bug, uključujući i specifičan red koji je triggerao problem.

---

## Dva pristupa kopiranja

### Pristup 1: `mysqldump`

**Kako radi:** logički dump — exportira SQL INSERT naredbe (ili `LOAD DATA` format) koje rekonstruišu bazu na ciljnoj instanci.

**Prednosti:**
- Portabilno: radi između bilo koje dvije MySQL instance, uključujući Docker → RDS, RDS → lokalni, prod → dev
- Nema potrebe za identičnom cloud infrastrukturom — dump je samo SQL fajl
- Verzija damp-a može biti pohranjena u S3 i koristiti se za audit/rollback
- Radi sa svim MySQL 8.0 kompatibilnim endpointima

**Mane:**
- Sporo za veliku bazu: dump od 10GB može trajati 30+ minuta, restore još duže
- CPU i I/O load na source instanci (mitigiramo pokretanjem na read replica)
- Dump fajl ne sadrži binlog poziciju na atomičan način osim ako koristimo `--master-data` (deprecated u 8.0, zamijenjeno sa `--source-data`)

**Kada koristiti:** baze do ~5GB, ili kad trebamo portabilnost između okruženja koja nisu oba AWS.

### Pristup 2: RDS Snapshot restore

**Kako radi:** AWS kreira point-in-time fizičku kopiju RDS storage volumena i iz nje kreira novu RDS instancu.

**Prednosti:**
- Drastično brže za veliku bazu: snapshot od 100GB restore-uje se u ~10-15 minuta (ne skalira linearno s veličinom)
- Nema load-a na source bazu tokom restore-a (snapshot je async operacija u pozadini)
- AWS garantuje konzistentnost na nivou storage blokova

**Mane:**
- Samo za AWS okruženja — ne možeš restore-ovati RDS snapshot na lokalni Docker
- Kreira novu RDS instancu s novim endpointom — Terraform mora biti svjestan
- Složenija IAM konfiguracija i cross-account/cross-region scenariji
- Storage cost za snapshot retenciju (~$0.095/GB/mj)

**Kada koristiti:** baze > 5GB, svi target envovi su na AWS RDS.

---

## Za project-A: mysqldump pristup

Trenutna baza project-A je mala (< 1GB u prvim fazama), a potreba za lokalnim dev workflow-om je visoka — dev mora moći raditi i offline, bez AWS pristupa. Zbog toga koristimo mysqldump svugdje:

- **Lokalni dev:** dump iz prod RDS → restore u Docker Compose MySQL
- **Dev env na EKS:** dump iz prod RDS → restore u dev RDS instancu
- **Staging env:** isti workflow kao dev
- **Review apps:** automatski restore pri kreiranju dynamic env-a

Dump se čuva u S3, pipeline ga update-uje svaki dan u 02:00 UTC.

---

## Budući prijelaz: kada baza preraste 5GB

Threshold za prelazak na RDS snapshot workflow:

1. Dump + upload na S3 traje > 10 minuta → pipeline postaje predugo za review apps
2. Restore traje > 20 minuta → ukupno čekanje na novi review env postaje neprihvatljivo
3. mysqldump load na read replica počinje utjecati na replication lag

U tom trenutku: migriramo na hybrid pristup — RDS snapshot za AWS envove, mysqldump za lokalni dev (ili reduciran subset podataka za lokalni dev).

---

## Sigurnosna napomena: no-anonymization policy

Trenutna politika kopiranja prod podataka bez anonymizacije je prihvatljiva **samo** dok baza ne sadrži PII (Personally Identifiable Information) ili druge osjetljive podatke (financijski podaci, zdravstveni podaci, lozinke u clear text itd.).

**Jasni signali da je vrijeme za anonymizaciju:**
- Baza počne čuvati email adrese ili korisničke profile
- Financijske transakcije ili billing podaci
- Bilo koji GDPR/CCPA-relevantni podaci

**Plan za kada dođe taj trenutak:**
- Uvesti `mysqlanon` ili custom anonymization SQL skriptu koja se pokreće odmah nakon restore-a u non-prod envovima
- Anonymizirati direktno u dump procesu koristeći `--replace` opciju ili view-based dump
- Definirati data classification policy u dokumentaciji projekta

Bez ovog plana, "privremena" no-anonymization politika može ostati zauvijek — što je sigurnosni dug koji raste sa svakim korisnikom koji se registrira.
