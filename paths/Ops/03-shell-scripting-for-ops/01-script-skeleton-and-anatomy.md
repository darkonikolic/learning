# Shell — `01` Script skeleton i anatomija

**Zasto:** Svaka skripta koju napišeš za ops mora imati isti osnov — shebang, zaštitne flagove, main funkciju i smislene exit kodove. Bez toga pišeš skriptu koja tiho kvari produkciju, radi lokalno ali ne u CIu, ili ostavlja smeće kad pukne.

---

## Minimalni šablon koji uvijek koristiš

```bash
#!/usr/bin/env bash
set -euo pipefail

# Konstante
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "$0")"

main() {
  echo "skripta radi"
}

main "$@"
```

Svaka linija ima razlog:

**`#!/usr/bin/env bash`** — traži bash kroz PATH umjesto hardkodovanog `/bin/bash`. Na Macu je `/bin/bash` stari bash 3.x, na serveru može biti drugačiji. `env bash` uvijek nađe pravi.

**`set -e`** — izlazi odmah kad neka komanda vrati non-zero. Bez ovoga skripta nastavlja izvršavanje nakon greške i može obrisati pogrešnu bazu, deployati loš image, ili preskočiti kritičan korak.

**`set -u`** — nedefenisana varijabla je greška, ne prazan string. Bez ovoga `rm -rf /$TYPO/` briše root. Sa ovime padne s jasnom greškom.

**`set -o pipefail`** — pipeline `a | b | c` vraća exit kod prvog koji nije uspio, ne zadnjeg. Bez ovoga `false | true` prolazi. Sa ovime pada.

**`main "$@"`** — sve funkcije definišeš iznad, poziv na dnu. `"$@"` prenosi sve argumente koji su proslijeđeni skripti.

---

## Exit kodovi

Svaka skripta mora završiti sa smislenim exit kodom — CI i monitoring to čitaju.

```bash
main() {
  if ! check_dependency "docker"; then
    echo "ERROR: docker nije instaliran" >&2
    exit 1
  fi

  deploy || exit 2
}

check_dependency() {
  command -v "$1" &>/dev/null
}
```

Konvencija:
- `0` — uspjeh
- `1` — generalna greška
- `2` — greška konfiguracije / nedostaje dependency
- `3+` — specifični scenariji koje dokumentuješ na vrhu skripte

Greške uvijek idu na **stderr** (`>&2`), ne na stdout. Stdout je za output koji CI i drugi procesi konzumiraju — greške ga ne smiju zagaditi.

---

## Cesta greška: set -e i neke komande legalno vraćaju non-zero

```bash
# OVO PADA — grep vraća 1 ako nema match
if grep "error" logfile; then ...

# ISPRAVNO
if grep -q "error" logfile; then ...

# ILI — eksplicitno dozvoli non-zero
grep "error" logfile || true
```

---

## Vjezba

Napiši skriptu `check-services.sh` sa ovim šablonom:
- Prima listu servisa kao argumente: `./check-services.sh nginx postgresql redis`
- Za svaki servis provjerava da li je `systemctl is-active` vratio 0
- Ispisuje `[OK] nginx` ili `[FAIL] postgresql`
- Izlazi sa kodom 1 ako ijedan servis nije aktivan, 0 ako su svi aktivni
- Koristi `main "$@"`, sve u funkcijama, greške na stderr
