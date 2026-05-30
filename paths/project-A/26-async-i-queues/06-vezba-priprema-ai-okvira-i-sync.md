# 06 — Vežba: priprema AI-okvira i sync (async i redovi)

Pripremaš AI-okvir za asinhronu obradu (redovi, worker-i, idempotencija), pa verifikuješ producer/consumer tok.

## Cilj

- okvir koji forsira idempotenciju, retry sa backoff-om i dead-letter
- dokazano: poruka se obrađuje tačno jednom (efektivno), neuspeh ide u DLQ

## Deo A — Priprema AI-okvira za async

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Go persona | da | `/golang-engineer` |
| Async/queue checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `async-checks` (idempotentni handler-i; retry + backoff; dead-letter; vidljivost dubine reda). Uvedi — async greške su suptilne i ponavljaju se.

### A3 — Minimalni dodatak (primer)

```
# kandidat: async-checks
- Handler idempotentan (dedup ključ / upsert), jer at-least-once isporuka.
- Retry sa eksponencijalnim backoff-om; posle N pokušaja → dead-letter queue.
- Metrika dubine reda i starosti najstarije poruke (observability).
```

## Deo B — Praktičan rad (sync)

### Producer/consumer provera

```bash
# objavi test poruku i prati obradu
docker compose exec app ./publish --topic orders --payload '{"id":1}'
docker compose logs -f worker          # potvrdi tačno-jednom efekat
# proveri dubinu reda / DLQ (npr. Redis/SQS metrika)
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] dupla isporuka ne pravi dvostruki efekat (idempotencija)
- [ ] neuspela poruka posle retry-ja završi u DLQ
- [ ] dubina reda vidljiva u metrikama
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Imam worker koji obrađuje [poruke]. Isporuka je at-least-once.
Predloži idempotentan dizajn handler-a + retry/backoff/DLQ i objasni rizike.
```
