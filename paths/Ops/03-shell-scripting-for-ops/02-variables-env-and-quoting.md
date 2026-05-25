# Shell — `02` Varijable, env i quoting

**Zasto:** Greške u quotingu i rukovanju varijablama su broj jedan uzrok pucanja skripti u CI. Ime fajla sa razmakom, varijabla koja nije postavljena, PATH koji ne postoji u cron okruženju — sve to ubija skriptu tiho ili na spektakularan način.

---

## Quoting — zlatno pravilo

**Uvijek stavljaj varijable u navodnike.** Bez navodnika bash radi word splitting i glob ekspanziju, što ima neočekivane efekte.

```bash
# Bez navodnika — pukne ako ime fajla ima razmak
filename="moj fajl.txt"
rm $filename       # bash vidi: rm moj fajl.txt → briše "moj" i "fajl.txt"

# Sa navodnicima — ispravno
rm "$filename"     # bash vidi: rm "moj fajl.txt"

# Globbing problem
pattern="*.txt"
ls $pattern        # bash ekspanduje *.txt OVDJE, ne prosljeđuje string komandi
ls "$pattern"      # prosljeđuje literal "*.txt"
```

---

## Čitanje env varijabli

Tri načina, svaki za drugi slučaj:

```bash
# 1. Obavezna varijabla — pada s greškom ako nije postavljena
DB_HOST="${DB_HOST:?ERROR: DB_HOST mora biti postavljen}"

# 2. Opcionalna s defaultom — tiho koristi default
APP_PORT="${APP_PORT:-8080}"
APP_ENV="${APP_ENV:-development}"

# 3. Prosto čitanje — prazno ako nije postavljeno (rijetko što hoćeš u ops)
OPTIONAL_FLAG="${OPTIONAL_FLAG:-}"
```

`:?` je tvoj prijatelj za skripte koje deployuju. Ako zaboraviš postaviti `DB_HOST`, skripta odmah pada s jasnom porukom — ne deployuje na pogrešnu bazu.

---

## Validacija na početku skripte

Sve varijable validiraj na vrhu, prije nego uradiš bilo šta:

```bash
main() {
  # Validacija — skripta pada ovdje, ne na pola deploya
  : "${APP_ENV:?}"
  : "${IMAGE_TAG:?}"
  : "${REGISTRY_URL:?}"

  # Defaults za opcionalne
  local dry_run="${DRY_RUN:-false}"
  local timeout="${DEPLOY_TIMEOUT:-120}"

  deploy "$APP_ENV" "$IMAGE_TAG"
}
```

---

## Command substitution

```bash
# Zastarjelo — backticks, teško za čitanje i ne može se nestovati
VERSION=`git describe --tags`

# Moderno — $() sintaksa
VERSION=$(git describe --tags)

# Može se nestovati
SHORT_SHA=$(git rev-parse --short "$(git rev-parse HEAD)")

# Uvijek u navodnicima kad dodjeluješ
HOSTNAME="$(hostname -f)"
```

---

## Korisne string operacije bez spawnanja procesa

```bash
IMAGE="registry.example.com/myapp:v1.2.3"

# Ukloni prefiks do zadnje /
NAME="${IMAGE##*/}"          # → "myapp:v1.2.3"

# Ukloni sufiks od zadnje :
REPO="${IMAGE%:*}"           # → "registry.example.com/myapp"

# Uzmi samo tag
TAG="${IMAGE##*:}"           # → "v1.2.3"

# Zamjena
CLEAN="${IMAGE/registry.example.com\//}"  # → "myapp:v1.2.3"
```

Ovo je brže od `sed` za jednostavne transformacije jer ne spawna subprocess.

---

## Export — šta child procesi nasljeđuju

```bash
# Lokalna varijabla — samo u trenutnoj ljusci
APP_ENV="staging"

# Exported — vidljiva child procesima (docker, kubectl, make...)
export APP_ENV="staging"

# Postavi i exportuj odjednom
export DB_HOST="db.internal"

# Provjeri što je exported
export -p | grep APP
```

Sve što CLI alati trebaju čitati mora biti exported.

---

## Ceste greške

```bash
# GREŠKA — varijabla bez navodnika u if
if [ $status = "ok" ]; then    # pada ako je status prazan
  
# ISPRAVNO
if [ "$status" = "ok" ]; then

# GREŠKA — aritmetika sa stringovima
count=$count+1                 # "5+1", ne 6

# ISPRAVNO
count=$(( count + 1 ))
```

---

## Vjezba

Napiši skriptu `deploy-validate.sh`:
- Čita iz env: `APP_ENV` (obavezno), `IMAGE_TAG` (obavezno), `REPLICAS` (default: 2), `DRY_RUN` (default: false)
- Validira da `APP_ENV` je jedan od: `staging`, `production` — ako nije, ispiši grešku i izađi s kodom 2
- Iz `IMAGE_TAG` (format: `registry/app:v1.2.3`) ekstraktuj samo verziju (`v1.2.3`) bez pozivanja `sed` ili `cut`
- Ispisi sve vrijednosti na stdout u formatu `KEY=VALUE`, jednu po liniji
