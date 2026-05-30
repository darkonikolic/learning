# 06 — Vežba: priprema AI-okvira i sync (kopija baze između okruženja)

Pripremaš AI-okvir za bezbedno kopiranje/anonimizaciju baze između okruženja, pa verifikuješ integritet.

## Cilj

- okvir koji štiti PII pri kopiranju prod → niža okruženja
- dokazano: kopija je konzistentna i anonimizovana

## Deo A — Priprema AI-okvira za DB kopiju

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Secrets/PII svest | da | `secrets-hygiene` |
| Dump/anonimizacija checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat checklist-skill `db-copy-safety` (nikad prod PII u dev bez maskiranja; redosled dump/restore; verifikacija reda zapisa). Uvedi — pravni/PII rizik.

### A3 — Minimalni dodatak (primer)

```
# kandidat: db-copy-safety
- Prod → niže okruženje SAMO uz maskiranje PII (email, ime, telefon).
- Verifikuj broj redova i checksum ključnih tabela posle restore-a.
- Restore u izolovan namespace/instancu, ne preko žive baze.
```

## Deo B — Praktičan rad (sync)

### Dump, maskiranje, verifikacija

```bash
mysqldump --single-transaction db > dump.sql
# anonimizacija osetljivih kolona (UPDATE ... SET email=CONCAT('user',id,'@example.com'))
mysql dev_db < dump_masked.sql
mysql -e "SELECT COUNT(*) FROM users;"   # uporedi sa izvorom
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] dump je konzistentan (`--single-transaction`)
- [ ] PII kolone maskirane pre ulaska u niže okruženje
- [ ] broj redova/checksum se poklapaju gde treba
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Treba mi kopija prod MySQL baze u dev, ali bez pravih PII podataka.
Predloži dump + anonimizaciju (koje kolone, kako) i kako da verifikujem integritet.
```
