# 07 — Vežba: priprema AI-okvira i sync (Xdebug i Delve)

Pripremaš AI-okvir za debug PHP-a (Xdebug) i Go-a (Delve) u kontejnerima, pa potvrđuješ da step-through radi.

## Cilj

- okvir koji pokriva podešavanje debug-a unutar Docker-a (bez bare-metal alata)
- dokazano: breakpoint se pogađa i u PHP-u i u Go-u

## Deo A — Priprema AI-okvira za debug

### A1 — Mapiraj

| Potreba | Postoji? | Gde |
|---------|----------|-----|
| PHP persona | da | `/php-architect` |
| Go persona | da | `/golang-engineer` |
| Debug-in-docker checklist | ? | — |

### A2 — Odluka (anti-sprawl)

Najčešće **bez novog rule-a** — debug je razvojni alat. Eventualni mali dodatak: napomena u `docker`-checks da debug build/profil ne ide u prod image. Uvedi samo ako se debug konfiguracija curi u produkciju.

### A3 — Minimalni dodatak (primer)

```
# dopuna dockerfile-checks (dev)
- Xdebug/Delve samo u dev/debug build target-u, nikad u prod image-u.
- Debug portovi (9003, 2345) izloženi samo u dev compose override-u.
```

## Deo B — Praktičan rad (sync)

### Provera debug toka

```bash
# PHP: Xdebug sluša 9003; IDE postavi breakpoint, okini request
docker compose exec php php -i | grep xdebug
# Go: Delve u kontejneru
docker compose exec go dlv debug --headless --listen=:2345 --api-version=2
```

## Validacija — acceptance kriterijumi

- [ ] (po potrebi) odluka A2 doneta preko `/system-maintainer`
- [ ] PHP breakpoint se pogađa kroz Xdebug
- [ ] Go breakpoint se pogađa kroz Delve
- [ ] debug nije prisutan u prod image-u
- [ ] sync zapisan u `decision_log.md`

## AI workflow

```
Hoću Xdebug za PHP i Delve za Go, ali samo u dev kontejnerima.
Daj compose override + IDE konfiguraciju i objasni kako da debug ne ode u prod.
```
