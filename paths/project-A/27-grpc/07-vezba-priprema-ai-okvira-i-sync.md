# 07 — Vežba: priprema AI-okvira i sync (gRPC)

Pripremaš AI-okvir za gRPC servise (proto kontrakti, lint, kompatibilnost), pa testiraš poziv.

## Cilj

- okvir koji pokriva proto higijenu i unazadnu kompatibilnost
- dokazano: proto lint čist, poziv radi, breaking promene uhvaćene

## Deo A — Priprema AI-okvira za gRPC

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| Go persona | da | `/golang-engineer` |
| Proto/kontrakt checklist | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `proto-checks` (ne reciklirati field broj; rezervisati uklonjena polja; provera breaking promena u CI preko `buf`). Uvedi — kompatibilnost kontrakta je kritična.

### A3 — Minimalni dodatak (primer)

```
# kandidat: proto-checks
- Nikad ne menjaj broj/postojeći tip polja; uklonjena polja idu u `reserved`.
- CI pokreće `buf lint` + `buf breaking` protiv glavne grane.
- Verzionisanje paketa (v1, v2) za nekompatibilne promene.
```

## Deo B — Praktičan rad (sync)

### Lint, breaking check i poziv

```bash
docker run --rm -v "$PWD":/work -w /work bufbuild/buf lint
docker run --rm -v "$PWD":/work -w /work bufbuild/buf breaking --against '.git#branch=main'
grpcurl -plaintext localhost:9090 list        # reflection
grpcurl -plaintext -d '{"id":1}' localhost:9090 pkg.Service/Method
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `buf lint` čist
- [ ] `buf breaking` ne prijavljuje nenamerne breaking promene
- [ ] `grpcurl` poziv vraća očekivani odgovor
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Evo .proto za [servis]. Hoću da dodam polje bez kvarenja klijenata.
Objasni pravila kompatibilnosti i kako buf breaking to štiti u CI-ju.
```
