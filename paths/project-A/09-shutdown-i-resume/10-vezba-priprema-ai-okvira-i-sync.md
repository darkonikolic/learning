# 10 — Vežba: priprema AI-okvira i sync (shutdown i resume)

Pripremaš AI-okvir za bezbedno gašenje/podizanje okruženja radi uštede, pa verifikuješ da nema gubitka podataka.

## Cilj

- okvir koji štiti od gubitka stanja pri gašenju i ubrzava resume
- dokazano: snapshot/backup postoji pre destroy-a, resume vraća radno stanje

## Deo A — Priprema AI-okvira za shutdown/resume

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Cost svest | da | `real-world-focus` |
| Redosled gašenja/podizanja | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat skill `safe-teardown-checklist` (šta snapshot-ovati, redosled rušenja, šta NE rušiti — state bucket, podaci). Uvedi jer je rizik gubitka podataka visok i ponavlja se.

### A3 — Minimalni dodatak (primer)

```
# kandidat: safe-teardown-checklist
Pre destroy: RDS snapshot, EBS snapshot, izvoz tajni; potvrdi da state bucket ostaje.
Resume: vrati iz snapshot-a, proveri konekcije, smoke test pre saobraćaja.
```

## Deo B — Praktičan rad (sync)

### Verifikacija pre/posle

```bash
# pre destroy: dokaz da backup postoji
aws rds describe-db-snapshots --db-instance-identifier <id>
terraform plan -destroy   # svestan pregled šta odlazi
# resume: posle apply
terraform plan            # očekuje se "no changes" na infra delu
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] snapshot/backup dokazano postoji pre destroy-a
- [ ] `terraform plan -destroy` pregledan (state/podaci zaštićeni)
- [ ] posle resume-a smoke test prolazi
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Gasim okruženje preko noći radi uštede. Šta moram da snapshot-ujem
i kojim redom da rušim/podižem da ne izgubim podatke ni state?
```
