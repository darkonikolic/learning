# 07 — Vežba: priprema AI-okvira i sync (DB migracije)

Pripremaš AI-okvir za bezbedne migracije šeme (expand-contract, reverzibilnost), pa verifikuješ up/down.

## Cilj

- okvir koji forsira reverzibilne, zero-downtime migracije
- dokazano: `up` i `down` rade, nema lock-a koji ruši saobraćaj

## Deo A — Priprema AI-okvira za migracije

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| DB svest | delom | `db-copy-safety` (oblast 17) |
| Migracija/deploy checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `migration-checks` (svaka migracija reverzibilna; expand-contract za promene koje aplikacija koristi uživo; izbegavaj duge lock-ove). Uvedi — rizik prod incidenta.

### A3 — Minimalni dodatak (primer)

```
# kandidat: migration-checks
- Svaka migracija ima `down` (ili dokumentovan razlog zašto je nepovratna).
- Expand-contract: dodaj kolonu → dvostruko piši → backfill → preusmeri → ukloni.
- Izbegavaj ALTER koji drži lock na velikoj tabeli u prometu.
```

## Deo B — Praktičan rad (sync)

### Up/down i provera

```bash
migrate up        # (alat koji koristiš: golang-migrate, doctrine, itd.)
migrate down 1    # reverzibilnost
mysql -e "SHOW COLUMNS FROM <tabela>;"   # potvrdi očekivanu šemu
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `up` primenjuje promenu, `down` je vraća
- [ ] velike promene idu expand-contract obrascem
- [ ] nema dugotrajnog lock-a na tabelama u prometu
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Treba mi da [promena šeme] bez downtime-a dok aplikacija radi.
Objasni expand-contract korake i daj reverzibilne migracije (up/down).
```
