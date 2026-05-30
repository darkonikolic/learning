# 21 — Vežba: priprema AI-okvira i sync (arhitektura aplikacije)

Pripremaš AI-okvir za multi-servisnu aplikaciju (Vue SPA, PHP API proxy, Go backend, MySQL, Redis), pa validiraš da se ceo stack diže.

## Cilj

- okvir koji pokriva granice servisa, kontrakte i lokalni stack
- dokazano: ceo stack se diže i servisi komuniciraju (smoke)

## Deo A — Priprema AI-okvira za arhitekturu

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| PHP persona | da | `/php-architect` |
| Go persona | da | `/golang-engineer` |
| Compose/granice servisa | ? | — |

### A2 — Odluka (anti-sprawl)

`/system-maintainer` + `process-feedback`: kandidat rule `service-contract-checks` (svaki servis ima health endpoint, jasne env varijable, definisane zavisnosti u compose-u). Uvedi jer arhitektura dodiruje više oblasti.

### A3 — Minimalni dodatak (primer)

```
# kandidat: service-contract-checks
- Svaki servis izlaže /health i poštuje 12-factor config (env).
- Granice: SPA → PHP proxy → Go backend; bez preskakanja slojeva.
- docker-compose: depends_on + healthcheck, ne sleep.
```

## Deo B — Praktičan rad (sync)

### Diži i smoke-testiraj stack

```bash
docker compose up -d --build
docker compose ps          # svi healthy
curl -fsS localhost:8080/health     # PHP proxy
curl -fsS localhost:9090/health     # Go backend
```

## Validacija — acceptance kriterijumi

- [ ] odluka A2 doneta preko `/system-maintainer`
- [ ] `docker compose ps` svi servisi `healthy`
- [ ] health endpoint-i odgovaraju 200
- [ ] poziv kroz proxy stiže do backend-a (end-to-end)
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Imam SPA → PHP proxy → Go backend → MySQL/Redis.
Predloži docker-compose sa healthcheck-ovima i ispravnim depends_on
da se diže pouzdano (bez sleep hakova).
```
