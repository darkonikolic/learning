# Shell — `05` Error handling, trap i retry

**Zasto:** Skripta koja pukne na pola deploya i ostavi klaster u nekonzistentnom stanju je gora od skripte koja nikad nije ni pokrenuta. `trap` i retry logika su razlika između skripta koja se može koristiti u produkciji i one koja je demo.

---

## trap — cleanup koji se uvijek izvrši

`trap` registruje funkciju koja se poziva kad skripta završi — normalno, na grešci, ili na signal.

```bash
#!/usr/bin/env bash
set -euo pipefail

TEMP_DIR=""
DEPLOYMENT_STARTED=false

cleanup() {
  local exit_code=$?
  
  # Uvijek briši temp fajlove
  [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]] && rm -rf "$TEMP_DIR"
  
  # Rollback samo ako je deploy počeo i nije uspio
  if [[ "$DEPLOYMENT_STARTED" == "true" && $exit_code -ne 0 ]]; then
    echo "Deploy pukao, pokrećem rollback..." >&2
    kubectl rollout undo deployment/myapp
  fi
  
  exit $exit_code
}

# Registruj cleanup za svaki izlaz
trap cleanup EXIT

# Registruj ERR da vidiš gdje je puklo
trap 'echo "ERROR na liniji $LINENO: $BASH_COMMAND" >&2' ERR

main() {
  TEMP_DIR=$(mktemp -d)
  
  # Radi nešto s temp direktorijem
  cp deployment.yaml "$TEMP_DIR/"
  yq -i '.image.tag = "'"$IMAGE_TAG"'"' "$TEMP_DIR/deployment.yaml"
  
  DEPLOYMENT_STARTED=true
  kubectl apply -f "$TEMP_DIR/deployment.yaml"
  kubectl rollout status deployment/myapp --timeout=120s
}

main "$@"
```

---

## Retry logika za transient greške

Mreža je nestabilna, registry je spor, K8s API server je zauzet. Retry s backoffom je standard.

```bash
# Osnovna retry funkcija — koristi je za svaku flaky operaciju
retry() {
  local max_attempts="$1"
  local sleep_seconds="$2"
  shift 2
  local cmd=("$@")
  
  local attempt=1
  while (( attempt <= max_attempts )); do
    echo "Pokušaj $attempt/$max_attempts: ${cmd[*]}" >&2
    if "${cmd[@]}"; then
      return 0
    fi
    
    if (( attempt < max_attempts )); then
      echo "Neuspjelo, čekam ${sleep_seconds}s..." >&2
      sleep "$sleep_seconds"
      sleep_seconds=$(( sleep_seconds * 2 ))  # exponential backoff
    fi
    (( attempt++ ))
  done
  
  echo "ERROR: svi pokušaji neuspjeli" >&2
  return 1
}

# Upotreba
retry 3 5 docker pull "registry.example.com/myapp:$IMAGE_TAG"
retry 5 10 curl --fail --silent "$HEALTH_URL"
```

---

## Health check loop — čekaj dok servis ne bude spreman

```bash
wait_for_healthy() {
  local url="$1"
  local timeout="${2:-120}"
  local interval=5
  local elapsed=0
  
  echo "Čekam da $url bude zdrav..."
  
  while (( elapsed < timeout )); do
    if curl --fail --silent --max-time 3 "$url" &>/dev/null; then
      echo "Servis je zdrav nakon ${elapsed}s"
      return 0
    fi
    
    sleep "$interval"
    elapsed=$(( elapsed + interval ))
    echo "  ...još čekam (${elapsed}s/${timeout}s)"
  done
  
  echo "ERROR: servis nije podignut za ${timeout}s" >&2
  return 1
}

# Upotreba
wait_for_healthy "https://staging.example.com/health" 180
```

---

## Lockfile — spriječi paralelne pokretaje

```bash
readonly LOCK_FILE="/tmp/${SCRIPT_NAME}.lock"

acquire_lock() {
  if ! mkdir "$LOCK_FILE" 2>/dev/null; then
    local pid
    pid=$(cat "$LOCK_FILE/pid" 2>/dev/null || echo "nepoznat")
    echo "ERROR: skripta već radi (PID: $pid)" >&2
    exit 1
  fi
  echo $$ > "$LOCK_FILE/pid"
}

release_lock() {
  rm -rf "$LOCK_FILE"
}

# U cleanup funkciji uvijek oslobodi lock
cleanup() {
  release_lock
  # ...ostali cleanup
}

trap cleanup EXIT
acquire_lock
```

---

## Vjezba

Napiši skriptu `deploy-with-recovery.sh`:
- Pravi temp direktorij na početku, briše ga na kraju (uvijek, i na grešci)
- Kopira `deployment.yaml` u temp dir, updateuje image tag
- `DEPLOYMENT_STARTED` flag — postavi na `true` tek kad pozoveš kubectl apply
- Ako kubectl apply ili rollout status pukne: automatski uradi `kubectl rollout undo`
- Koristi `wait_for_healthy` da provjeri `$HEALTH_URL` nakon deploya (3 pokušaja, 30s timeout)
- Na svakom koraku jasna poruka šta se dešava
