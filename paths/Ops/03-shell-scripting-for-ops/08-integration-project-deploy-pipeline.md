# Shell — `08` Integration project: deploy pipeline skripta

**Zasto:** Sve prethodne lekcije imaju smisla tek kad ih vidiš zajedno u jednoj pravoj skripti. Ovo je skripta kakvu ćeš pisati i održavati na poslu.

---

## Šta skripta radi

`deploy.sh` — deploy aplikacije na K8s cluster:
1. Validira argumente i env
2. Provjerava da su svi alati prisutni
3. Updateuje image tag u manifestu (yq)
4. Primjenjuje manifest (kubectl apply)
5. Čeka da rollout završi
6. Provjeri zdravlje aplikacije (curl)
7. Na grešci — automatski rollback

---

## Kompletna skripta

```bash
#!/usr/bin/env bash
set -euo pipefail

readonly SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Konfiguracija
readonly HEALTH_CHECK_RETRIES=5
readonly HEALTH_CHECK_INTERVAL=10
readonly ROLLOUT_TIMEOUT=300

# State za cleanup
TEMP_DIR=""
DEPLOYMENT_APPLIED=false

# ─── Logging ──────────────────────────────────────────────────────────────────

log()  { echo "[$(date '+%H:%M:%S')] INFO  $*"; }
warn() { echo "[$(date '+%H:%M:%S')] WARN  $*" >&2; }
err()  { echo "[$(date '+%H:%M:%S')] ERROR $*" >&2; }

# ─── Cleanup ──────────────────────────────────────────────────────────────────

cleanup() {
  local exit_code=$?
  
  [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
  
  if [[ "$DEPLOYMENT_APPLIED" == "true" && $exit_code -ne 0 ]]; then
    warn "Deploy pukao (exit $exit_code), pokrećem rollback..."
    kubectl rollout undo deployment/"$DEPLOYMENT" \
      --namespace "$NAMESPACE" || err "Rollback neuspješan!"
  fi
  
  exit $exit_code
}

trap cleanup EXIT
trap 'err "Puklo na liniji $LINENO: $BASH_COMMAND"' ERR

# ─── Helpers ──────────────────────────────────────────────────────────────────

usage() {
  cat >&2 <<EOF
Usage: $SCRIPT_NAME --env <env> --tag <tag> [opcije]

Obavezno:
  --env <staging|production>   Target okruženje
  --tag <image-tag>            Docker image tag za deploy

Opcionalno:
  --deployment <name>          Naziv K8s deploymenta (default: myapp)
  --namespace <ns>             K8s namespace (default: default)
  --manifest <path>            Path do deployment.yaml (default: deploy/deployment.yaml)
  --health-url <url>           URL za health check (default: bez provjere)
  --dry-run                    Ispiši akcije bez izvršavanja
  -h, --help                   Ova poruka
EOF
  exit 1
}

check_prereqs() {
  local missing=0
  for cmd in kubectl yq jq curl; do
    if ! command -v "$cmd" &>/dev/null; then
      err "Nedostaje alat: $cmd"
      missing=1
    fi
  done
  (( missing == 0 )) || exit 2
}

parse_args() {
  APP_ENV=""
  IMAGE_TAG=""
  DEPLOYMENT="myapp"
  NAMESPACE="default"
  MANIFEST="${SCRIPT_DIR}/../deploy/deployment.yaml"
  HEALTH_URL=""
  DRY_RUN=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --env)        APP_ENV="$2";     shift 2 ;;
      --tag)        IMAGE_TAG="$2";   shift 2 ;;
      --deployment) DEPLOYMENT="$2";  shift 2 ;;
      --namespace)  NAMESPACE="$2";   shift 2 ;;
      --manifest)   MANIFEST="$2";    shift 2 ;;
      --health-url) HEALTH_URL="$2";  shift 2 ;;
      --dry-run)    DRY_RUN=true;     shift   ;;
      -h|--help)    usage ;;
      *) err "Nepoznata opcija: $1"; usage ;;
    esac
  done

  [[ -n "$APP_ENV" ]]   || { err "--env je obavezan";   usage; }
  [[ -n "$IMAGE_TAG" ]] || { err "--tag je obavezan";   usage; }
  [[ "$APP_ENV" =~ ^(staging|production)$ ]] || { err "env mora biti staging ili production"; exit 2; }
  [[ -f "$MANIFEST" ]]  || { err "Manifest ne postoji: $MANIFEST"; exit 2; }
}

# ─── Deploy koraci ────────────────────────────────────────────────────────────

prepare_manifest() {
  TEMP_DIR=$(mktemp -d)
  local tmp_manifest="$TEMP_DIR/deployment.yaml"
  
  cp "$MANIFEST" "$tmp_manifest"
  
  local current_tag
  current_tag=$(yq '.spec.template.spec.containers[0].image' "$tmp_manifest" | cut -d: -f2)
  log "Trenutni tag: $current_tag → novi tag: $IMAGE_TAG"
  
  yq -i ".spec.template.spec.containers[0].image |= sub(\":.*\", \":$IMAGE_TAG\")" "$tmp_manifest"
  echo "$tmp_manifest"
}

apply_manifest() {
  local manifest="$1"
  
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY-RUN: kubectl apply -f $manifest"
    kubectl apply -f "$manifest" --dry-run=client
    return
  fi
  
  kubectl apply -f "$manifest"
  DEPLOYMENT_APPLIED=true
}

wait_for_rollout() {
  if [[ "$DRY_RUN" == "true" ]]; then
    log "DRY-RUN: kubectl rollout status deployment/$DEPLOYMENT"
    return
  fi
  
  log "Čekam rollout (max ${ROLLOUT_TIMEOUT}s)..."
  kubectl rollout status deployment/"$DEPLOYMENT" \
    --namespace "$NAMESPACE" \
    --timeout "${ROLLOUT_TIMEOUT}s"
}

verify_health() {
  [[ -n "$HEALTH_URL" ]] || return 0
  
  local attempt=1
  while (( attempt <= HEALTH_CHECK_RETRIES )); do
    log "Health check $attempt/$HEALTH_CHECK_RETRIES: $HEALTH_URL"
    
    if curl --fail --silent --max-time 5 "$HEALTH_URL" &>/dev/null; then
      log "Health check OK"
      return 0
    fi
    
    (( attempt++ ))
    sleep "$HEALTH_CHECK_INTERVAL"
  done
  
  err "Health check neuspješan nakon $HEALTH_CHECK_RETRIES pokušaja"
  return 1
}

# ─── Main ─────────────────────────────────────────────────────────────────────

main() {
  parse_args "$@"
  check_prereqs
  
  log "Deploy: $IMAGE_TAG → $APP_ENV/$NAMESPACE/$DEPLOYMENT"
  [[ "$DRY_RUN" == "true" ]] && warn "DRY-RUN mod — ništa se neće promijeniti"
  
  local manifest
  manifest=$(prepare_manifest)
  
  apply_manifest "$manifest"
  wait_for_rollout
  verify_health
  
  log "✓ Deploy uspješan: $IMAGE_TAG na $APP_ENV"
}

main "$@"
```

---

## Vjezba

1. Pokreni `shellcheck deploy.sh` — popravi sve što ShellCheck nađe
2. Testiraj `--dry-run` mod — provjeri da se ništa ne mijenja
3. Dodaj `--slack-webhook` opciju koja šalje notifikaciju na Slack (curl POST) na kraj deploya i na rollback
4. Dodaj lockfile koji sprečava paralelne deploye na isti env/namespace
5. Napiši GitLab CI job koji poziva ovu skriptu
