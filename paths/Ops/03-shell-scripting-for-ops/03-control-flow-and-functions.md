# Shell — `03` Control flow i funkcije

**Zasto:** Uvjetna logika i funkcije su razlika između skripte koja radi jednu stvar i skripte koja se može koristiti u više scenarija. U opsu to znači: isti kod za staging i production, isti deploy script za K8s i ECS.

---

## if i testovi

Koristi `[[ ]]` umjesto `[ ]` u bash skriptama — nema word splitting, podržava `&&`/`||` i regex.

```bash
# Provjera fajla
if [[ -f "/etc/nginx/nginx.conf" ]]; then
  echo "nginx config postoji"
fi

# -f fajl postoji    -d direktorij    -e postoji (bilo što)
# -r čitljivo        -w zapisivo      -x izvršivo
# -s neprazan fajl   -L symlink

# String provjere
if [[ -z "$VAR" ]]; then      # prazan string
if [[ -n "$VAR" ]]; then      # neprazan string
if [[ "$ENV" == "prod" ]]; then
if [[ "$ENV" != "prod" ]]; then
if [[ "$ENV" =~ ^(staging|prod)$ ]]; then   # regex match

# Numeričke provjere
if (( count > 0 )); then      # aritmetički context, čistiji za brojeve
if [[ $count -gt 0 ]]; then   # tradicionalno, radi sa -eq -ne -lt -gt -le -ge
```

---

## for i while

```bash
# Lista servisa
for service in nginx postgresql redis; do
  systemctl is-active --quiet "$service" || echo "FAIL: $service nije aktivan"
done

# Fajlovi u direktoriju (nikad ne parsuj ls!)
for logfile in /var/log/app/*.log; do
  [[ -f "$logfile" ]] || continue    # provjeri da glob nije ostao literal
  process_log "$logfile"
done

# Čitanje fajla liniju po liniju (jedini siguran način)
while IFS= read -r line; do
  echo "Processing: $line"
done < hosts.txt

# Čitanje outputa komande
while IFS= read -r pod; do
  kubectl logs "$pod" --tail=100
done < <(kubectl get pods -o name)

# Numerička petlja
for i in $(seq 1 5); do
  echo "Attempt $i"
  deploy && break || sleep $((i * 5))
done
```

---

## case — za routing po env/tipu

```bash
case "$APP_ENV" in
  staging)
    REPLICAS=1
    DB_HOST="db-staging.internal"
    ;;
  production)
    REPLICAS=3
    DB_HOST="db-prod.internal"
    ;;
  *)
    echo "ERROR: nepoznat env '$APP_ENV'" >&2
    exit 2
    ;;
esac
```

---

## Funkcije — jedini način da skripta ostane čitljiva

```bash
#!/usr/bin/env bash
set -euo pipefail

# Pravila:
# 1. Svaka funkcija radi jednu stvar
# 2. local za sve lokalne varijable — nikad ne zagađuj global scope
# 3. Funkcija komunicira kroz exit kod (0=ok, non-zero=greška) i stdout za vrijednosti

check_prereqs() {
  local missing=0
  for cmd in docker kubectl jq; do
    if ! command -v "$cmd" &>/dev/null; then
      echo "ERROR: '$cmd' nije instaliran" >&2
      missing=1
    fi
  done
  return $missing
}

get_current_image() {
  local deployment="$1"
  local namespace="${2:-default}"
  kubectl get deployment "$deployment" -n "$namespace" \
    -o jsonpath='{.spec.template.spec.containers[0].image}'
}

deploy() {
  local env="$1"
  local image_tag="$2"
  echo "Deploying $image_tag na $env..."
  # ...
}

main() {
  check_prereqs || exit 2

  local current
  current=$(get_current_image "myapp" "production")
  echo "Trenutni image: $current"

  deploy "$APP_ENV" "$IMAGE_TAG"
}

main "$@"
```

---

## Argumenti skripte i getopts

```bash
usage() {
  echo "Usage: $0 --env <staging|production> --tag <image-tag> [--dry-run]"
  exit 1
}

parse_args() {
  DRY_RUN=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --env)    APP_ENV="$2";    shift 2 ;;
      --tag)    IMAGE_TAG="$2";  shift 2 ;;
      --dry-run) DRY_RUN=true;  shift   ;;
      -h|--help) usage ;;
      *) echo "ERROR: nepoznata opcija '$1'" >&2; usage ;;
    esac
  done

  [[ -n "${APP_ENV:-}" ]] || { echo "ERROR: --env je obavezan" >&2; usage; }
  [[ -n "${IMAGE_TAG:-}" ]] || { echo "ERROR: --tag je obavezan" >&2; usage; }
}

main() {
  parse_args "$@"
  echo "Deploying $IMAGE_TAG na $APP_ENV (dry_run=$DRY_RUN)"
}

main "$@"
```

---

## Vjezba

Napiši skriptu `rollout.sh`:
- Prima `--env` (obavezno), `--image` (obavezno), `--namespace` (default: `default`), `--dry-run`
- Funkcija `validate_env()` — provjeri da je env staging ili production
- Funkcija `current_image()` — vrati trenutni image iz kubectl (ili echo "unknown" ako kubectl nije dostupan)
- Funkcija `do_rollout()` — u dry-run modu ispiši što bi uradila, inače pozovi `kubectl set image`
- U main: validiraj, ispiši trenutni image, uradi rollout, ispiši poruku o uspjehu
