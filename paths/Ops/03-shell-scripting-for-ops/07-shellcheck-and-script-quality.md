# Shell — `07` ShellCheck i kvalitet skripti

**Zasto:** ShellCheck je statički analizator koji hvata klasu grešaka prije nego ih uopće pokreneš. Na poslu, svaka skripta koja ide u CI ili na server mora proći shellcheck — isto kao što kod mora proći linter.

---

## ShellCheck — instaliraj i pokreni

```bash
# Instalacija
apt-get install shellcheck        # Debian/Ubuntu
brew install shellcheck           # Mac

# Pokretanje
shellcheck deploy.sh

# U CI (GitLab)
shellcheck_job:
  script:
    - shellcheck scripts/*.sh
```

---

## Najčešće greške koje ShellCheck hvata

**SC2086 — unquoted variable**
```bash
# ShellCheck: SC2086: Double quote to prevent globbing and word splitting
rm $file           # GREŠKA
rm "$file"         # OK
```

**SC2046 — command substitution bez navodnika**
```bash
# ShellCheck: SC2046
for f in $(ls *.log); do    # GREŠKA — ls output ima probleme s razmacima
for f in *.log; do           # OK — direktni glob
```

**SC2006 — stari backtick syntax**
```bash
result=`command`     # ShellCheck preporučuje $(command)
result=$(command)    # OK
```

**SC2164 — cd bez provjere**
```bash
cd /some/path        # GREŠKA — šta ako dir ne postoji?
cd /some/path || exit 1   # OK
# Ili još bolje:
cd /some/path || { echo "Ne mogu ući u /some/path" >&2; exit 1; }
```

**SC2181 — provjera $? direktno**
```bash
command
if [ $? -eq 0 ]; then    # GREŠKA — antipattern
  
if command; then          # OK — direktna provjera
```

---

## Čitki stil koji olakšava review

```bash
#!/usr/bin/env bash
set -euo pipefail

# Konstante UPPERCASE
readonly MAX_RETRIES=3
readonly DEPLOY_TIMEOUT=120

# Lokalne varijable lowercase
deploy() {
  local env="$1"
  local tag="$2"
  local namespace="${3:-default}"

  # Duge komande — lom linija sa \
  kubectl set image deployment/myapp \
    "app=registry.example.com/myapp:${tag}" \
    --namespace "$namespace"
}

# Jedna funkcija — jedna odgovornost
verify_deploy() {
  local namespace="$1"
  kubectl rollout status deployment/myapp \
    --namespace "$namespace" \
    --timeout "${DEPLOY_TIMEOUT}s"
}

main() {
  : "${APP_ENV:?}"
  : "${IMAGE_TAG:?}"
  
  deploy "$APP_ENV" "$IMAGE_TAG"
  verify_deploy "$APP_ENV"
  echo "Deploy uspješan: $IMAGE_TAG na $APP_ENV"
}

main "$@"
```

---

## Pre-commit hook za shellcheck

```bash
# .git/hooks/pre-commit
#!/usr/bin/env bash
set -euo pipefail

changed_scripts=$(git diff --cached --name-only --diff-filter=ACM | grep '\.sh$' || true)

if [[ -n "$changed_scripts" ]]; then
  echo "Pokrećem shellcheck..."
  # shellcheck disable=SC2086
  shellcheck $changed_scripts
fi
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## Vjezba

Uzmi bilo koju skriptu iz prethodnih lekcija i:
1. Pokreni `shellcheck` — zabilježi sve warningove
2. Popravi svaki warning — razumij zašto je to bila greška
3. Dodaj pre-commit hook koji blokira commit ako shellcheck ne prođe
4. Provjeri da skripte iz lekcija 01-06 sve prolaze shellcheck bez ikakvih warningova
