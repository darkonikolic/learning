# Developer Onboarding

## Cilj

Novi developer clone-uje repo → `make setup` → lokalno okruženje radi za manje od 15 minuta. Bez usmene predaje, bez "pita starijeg kolegu šta je sljedeći korak".

**Preduvjeti koje developer mora imati unaprijed:**
- Docker Desktop instaliran i pokrenut
- Git konfigurisan (`git config --global user.email`)
- GitLab SSH key (za clone)

Sve ostalo se rješava kroz `make` komande.

---

## Makefile

Makefile je jedina komanda-dokumentacija koja se ne zastarijeva jer je izvršna. Ako Makefile radi, onboarding radi.

```makefile
# Makefile u root-u projekta

.PHONY: setup dev down test lint clean help

# Defaultni target — ispiši help
.DEFAULT_GOAL := help

help:
	@echo ""
	@echo "Project-A — dostupne komande:"
	@echo ""
	@echo "  make setup   Inicijalni setup (prvi put)"
	@echo "  make dev     Pokreni development okruženje"
	@echo "  make down    Zaustavi development okruženje"
	@echo "  make test    Pokreni sve testove"
	@echo "  make lint    Linting (Go + PHP)"
	@echo "  make clean   Ukloni sve kontejnere i volumene (brisanje podataka!)"
	@echo ""

setup:
	@echo ""
	@echo "=== Project-A Setup ==="
	@echo ""
	@command -v docker >/dev/null 2>&1 || { \
		echo "ERROR: Docker nije instaliran."; \
		echo "Instaliraj Docker Desktop: https://www.docker.com/products/docker-desktop/"; \
		exit 1; \
	}
	@docker info >/dev/null 2>&1 || { \
		echo "ERROR: Docker nije pokrenut."; \
		echo "Pokreni Docker Desktop i pokušaj ponovo."; \
		exit 1; \
	}
	@[ -f .env.local ] || { \
		cp .env.example .env.local; \
		echo "Kreiran .env.local iz .env.example"; \
	}
	@echo ""
	@echo "Sljedeći korak:"
	@echo "  1. Otvori .env.local i promijeni passworde (MYSQL_PASSWORD, REDIS_PASSWORD, itd.)"
	@echo "  2. Pokušaj: make dev"
	@echo ""

dev:
	@[ -f .env.local ] || { echo "ERROR: Fali .env.local — pokreni 'make setup' prvo"; exit 1; }
	docker compose up --build -d
	@echo "Čekam da servisi budu zdravi..."
	@bash scripts/wait-healthy.sh 60
	@docker compose exec go-service /server migrate 2>/dev/null || true
	@docker compose exec go-service /server seed 2>/dev/null || true
	@echo ""
	@echo "=== Development okruženje je spremno ==="
	@echo ""
	@echo "  App:       http://localhost"
	@echo "  Adminer:   http://localhost:8081  (samo sa 'tools' profileom)"
	@echo "  Go API:    http://localhost:8080"
	@echo ""
	@echo "  Test login: test@firma.com / TestPass123!"
	@echo ""

down:
	docker compose down

test:
	@echo "--- Go testovi ---"
	docker compose run --rm go-service go test ./... -race -count=1 -timeout 60s
	@echo ""
	@echo "--- PHP testovi ---"
	docker compose run --rm php-service ./vendor/bin/pest --ci
	@echo ""
	@echo "Svi testovi prošli."

lint:
	@echo "--- Go lint ---"
	docker compose run --rm go-service golangci-lint run ./...
	@echo ""
	@echo "--- PHP lint (Pint) ---"
	docker compose run --rm php-service ./vendor/bin/pint --test
	@echo ""
	@echo "Linting završen."

clean:
	@echo "UPOZORENJE: Ovo briše sve kontejnere, slike i volumene (uključujući DB podatke)."
	@read -p "Jesi li siguran? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose down -v --remove-orphans
	@echo "Sve obrisano."
```

**scripts/wait-healthy.sh** (koristi se u `make dev`):

```bash
#!/usr/bin/env bash
# Čekaj da svi kontejneri budu healthy
TIMEOUT=${1:-60}
ELAPSED=0

while [ $ELAPSED -lt $TIMEOUT ]; do
    UNHEALTHY=$(docker compose ps --format json 2>/dev/null | \
        jq -r 'select(.Health != "healthy" and .Health != "") | .Name' 2>/dev/null | wc -l)
    
    if [ "$UNHEALTHY" -eq "0" ]; then
        echo "Svi servisi su zdravi."
        exit 0
    fi
    
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

echo "UPOZORENJE: Neki servisi nisu postali zdravi za ${TIMEOUT}s"
docker compose ps
exit 0  # Ne faila — korisnik vidi status
```

---

## .env.example

Commit-uje se u git. Sadrži placeholder vrijednosti. Nikad stvarne passworde.

```bash
# .env.example
# Kopiraj u .env.local i promijeni vrijednosti
# .env.local je u .gitignore — nikad ga ne commit-uj

# ===========================
# Database
# ===========================
MYSQL_ROOT_PASSWORD=change-me-locally
MYSQL_DATABASE=project_a
MYSQL_USER=app
MYSQL_PASSWORD=change-me-locally
MYSQL_REPLICATION_USER=replicator
MYSQL_REPLICATION_PASSWORD=change-me-locally

# ===========================
# Redis
# ===========================
REDIS_PASSWORD=change-me-locally

# ===========================
# Aplikacija
# ===========================
APP_ENV=development
APP_DEBUG=true
APP_KEY=base64:change-me-run-php-artisan-key-generate

# JWT ključevi — generiši lokalno, vidi README
JWT_PRIVATE_KEY_PATH=/app/certs/jwt-private.pem
JWT_PUBLIC_KEY_PATH=/app/certs/jwt-public.pem

# ===========================
# Go service
# ===========================
GO_SERVICE_PORT=8080
DB_HOST=mysql-master
DB_PORT=3306
DB_NAME=project_a
DB_USER=app
DB_PASSWORD=change-me-locally
REDIS_HOST=redis-master
REDIS_PORT=6379
LOG_LEVEL=debug

# ===========================
# PHP service
# ===========================
PHP_GO_SERVICE_URL=http://go-service:8080
PHP_GO_SERVICE_TIMEOUT=10

# ===========================
# Debug (opcionalno)
# ===========================
XDEBUG_ENABLED=false
XDEBUG_IDE_KEY=PHPSTORM
XDEBUG_CLIENT_HOST=host.docker.internal
```

---

## README.md u root-u

Jedini README koji treba. Kratko, samo bitno.

```markdown
# Project-A

## Quick start

Preduvjeti: Docker Desktop, Git

```bash
git clone git@gitlab.firma.com:project-a/project-a.git
cd project-a
make setup          # Kreira .env.local
# Uredi .env.local (promijeni passworde)
make dev            # Podiže sve, migrira, seeduje
```

Otvori http://localhost — login: `test@firma.com` / `TestPass123!`

## Stack

- Vue.js 3 frontend (nginx)
- PHP 8.3 API (Laravel)
- Go 1.22 backend service
- MySQL 8.0 (master + replica)
- Redis 7

## Komande

| Komanda | Opis |
|---------|------|
| `make dev` | Pokreni sve servise |
| `make down` | Zaustavi servise |
| `make test` | Pokreni Go + PHP testove |
| `make lint` | Go + PHP linting |
| `make clean` | Ukloni sve (briše podatke!) |

## Dokumentacija

| Tema | Lokacija |
|------|---------|
| Arhitektura | `paths/project-A/01-uvod/` |
| Lokalni setup detalji | `paths/project-A/02-lokalni-setup/` |
| Debugging (XDebug + Delve) | `paths/project-A/19b-xdebug-i-delve/` |
| Deployment | `paths/project-A/08-gitlab-pipelines-advanced/` |
| DR i backup | `paths/project-A/07b-shutdown-i-resume/` |

## Pristup

- GitLab: zatraži od tech leada
- AWS: zatraži od DevOps tima (read-only za dev okruženje)
- Produkcija: samo senior developeri i DevOps
```

---

## JWT ključevi za lokalni razvoj

JWT ključevi nisu u .env.example (ne mogu biti placeholder stringovi). Generišu se jednom lokalno.

```bash
# Generiši JWT ključeve za lokalni razvoj
mkdir -p certs
openssl genrsa -out certs/jwt-private.pem 2048
openssl rsa -in certs/jwt-private.pem -pubout -out certs/jwt-public.pem

echo "JWT ključevi generirani u certs/"
echo "certs/ je u .gitignore — ne commit-uj ih"
```

```bash
# .gitignore — provjeri da su tu
.env.local
certs/
*.pem
```

Ovo se može dodati kao korak u `make setup`:

```makefile
setup:
    # ... (Docker provjere)
    @[ -f certs/jwt-private.pem ] || { \
        mkdir -p certs; \
        openssl genrsa -out certs/jwt-private.pem 2048 2>/dev/null; \
        openssl rsa -in certs/jwt-private.pem -pubout -out certs/jwt-public.pem 2>/dev/null; \
        echo "JWT ključevi generirani u certs/"; \
    }
    # ...
```

---

## VS Code preporučene ekstenzije

```json
// .vscode/extensions.json — commit-uj u repo
{
    "recommendations": [
        "golang.go",
        "vue.volar",
        "xdebug.php-debug",
        "bmewburn.vscode-intelephense-client",
        "ms-azuretools.vscode-docker",
        "hashicorp.terraform",
        "redhat.vscode-yaml",
        "eamodio.gitlens",
        "usernamehw.errorlens"
    ]
}
```

VS Code će automatski predložiti instalaciju ovih ekstenzija kada developer otvori projekt.

---

## Checklist za novog developera

```
PRIPREMA (jednom)
[ ] Docker Desktop instaliran i pokrenut
[ ] Git konfigurisan (user.name, user.email)
[ ] SSH ključ dodan u GitLab profil

SETUP
[ ] git clone git@gitlab.firma.com:project-a/project-a.git
[ ] make setup
[ ] Urediti .env.local (promijeniti sve "change-me-locally" vrijednosti)
[ ] make dev
[ ] http://localhost se otvara
[ ] Login sa test@firma.com / TestPass123! radi

PROVJERA OKRUŽENJA
[ ] make test prolazi (svi testovi zeleni)
[ ] Adminer dostupan na http://localhost:8081 (pokrenuti sa 'tools' profileom)
[ ] VS Code ekstenzije instalirane (prompt se pojavljuje automatski)

PRISTUP
[ ] GitLab pristup (zatraži od tech leada)
[ ] AWS read-only pristup za dev (zatraži od DevOps tima)
[ ] Slack/Teams poziv u relevantne kanale

UČENJE (preporučeni redosljed)
[ ] Pročitati paths/project-A/01-uvod/
[ ] Pregledati docker-compose.yml i razumjeti servise
[ ] Pokriti paths/project-A/02-lokalni-setup/
[ ] Pregledati GitLab CI/CD pipeline (.gitlab-ci.yml)
```

---

## Troubleshooting

**`make dev` stane na "Čekam da servisi budu zdravi":**

```bash
# Provjeri koji servis nije zdrav
docker compose ps

# Provjeri logove problematičnog servisa
docker compose logs mysql-master
docker compose logs go-service

# Najčešći uzrok: pogrešan password u .env.local
# Provjeri: MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD
```

**Port je zauzet:**

```bash
# Provjeri šta koristi port 80
lsof -i :80
# Zaustavi konfliktni servis ili promijeni port u docker-compose.override.yml
```

**Go service ne starta — "migration failed":**

```bash
# Ručno pokreni migraciju da vidiš grešku
docker compose exec go-service /server migrate
# Najčešće: DB nije potpuno spreman, čekaj još nekoliko sekundi i ponovi
```

**Zaboravio sam šta radi koja komanda:**

```bash
make help
```

---

## Checklist

- [ ] Makefile ima `help` kao default target
- [ ] `.env.example` je u git-u, `.env.local` je u `.gitignore`
- [ ] `make setup` provjerava preduvjete (Docker) i daje jasne poruke
- [ ] `make dev` čeka health check prije nego ispiše URL-ove
- [ ] `make test` pokreće i Go i PHP testove
- [ ] JWT ključevi se generišu u `make setup`, nisu u git-u
- [ ] `.vscode/extensions.json` je u git-u
- [ ] README.md u root-u je kratak i sadrži samo quick start + link na dokumentaciju
- [ ] Onboarding checklist odrađen s novim developerom i ažuriran prema feedbacku
