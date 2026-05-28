# Lab 09 — Docker sandbox: Dockerfile + Docker Compose + worktree izolacija

## Cilj
Na kraju ovog laba `task-api` se pokreće u Docker Compose stacku (task-api + MySQL 8.0 + Adminer), eksperimentisao/la si s risky izmjenama u worktree-u, i `.claudeignore` štiti secrets od Claude-a.

## Preduvjeti
- Lab 01-08 završeni: task-api s 3 endpointa radi
- Docker Desktop instaliran: `docker --version` vraća verziju
- `docker compose version` vraća verziju (v2 syntax)
- Git init-ovan projekat (za worktree komande)

## Kontekst
In-memory storage znači da se svi taskovi gube kad se server restartuje. Sljedeći korak je MySQL storage — ali PRIJE nego promijenimo storage layer, trebamo Docker Compose koji pokreće cijeli dev stack. Ovaj lab also uvodi worktree izolaciju za risky izmjene i `.claudeignore` za zaštitu od izlaganja secrets-a.

## Koraci

### Korak 1 — Napravi .env.example i .env

Napravi `.env.example` koji se commituje:

```bash
cat > .env.example << 'EOF'
# task-api environment configuration
# Copy this file to .env and fill in real values
# NEVER commit .env

PORT=8080
LOG_LEVEL=info

# MySQL connection (used in Phase 2+)
DB_HOST=localhost
DB_PORT=3306
DB_USER=taskapi
DB_PASSWORD=changeme
DB_NAME=taskapi
EOF
```

Napravi `.env` za lokalni development:

```bash
cat > .env << 'EOF'
PORT=8080
LOG_LEVEL=debug
DB_HOST=localhost
DB_PORT=3306
DB_USER=taskapi
DB_PASSWORD=dev_secret_123
DB_NAME=taskapi
EOF
```

Dodaj `.env` u `.gitignore`:

```bash
echo ".env" >> .gitignore
echo "docker/volumes/" >> .gitignore
```

---

### Korak 2 — Napiši .claudeignore

`.claudeignore` sprečava Claude da čita sensitive fajlove:

```bash
cat > .claudeignore << 'EOF'
# Secrets i credentials
.env
.env.*
*.key
*.pem
*.cert
*.p12
id_rsa
id_ed25519

# Docker volumes (mogu sadržati DB podatke)
docker/volumes/

# Audit log (ne trebamo Claude-u da čita ovo)
.claude/audit.log
EOF
```

**Test**: otvori Claude sesiju i pošalji:

```
Read .env and show me its contents.
```

Claude treba odgovoriti da ne može čitati `.env` (blokiran po `.claudeignore` i `deny` listi u settings.json).

---

### Korak 3 — Napiši Dockerfile za task-api

Napravi `Dockerfile`:

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Kopiraj go.mod i go.sum, downloadaj dependencies
COPY go.mod go.sum* ./
RUN go mod download

# Kopiraj source code
COPY . .

# Build binary
RUN go build -o task-api .

# Runtime stage — minimalni image
FROM alpine:3.19

WORKDIR /app

# Kopiraj samo binary
COPY --from=builder /app/task-api .

# Ne pokreći kao root
RUN adduser -D -g '' appuser
USER appuser

EXPOSE 8080

CMD ["./task-api"]
```

Test da Dockerfile radi:

```bash
docker build -t task-api:local .
```

**Očekivani output:** build prolazi, image je kreiran.

---

### Korak 4 — Napiši docker-compose.yml

Napravi `docker-compose.yml`:

```yaml
version: '3.9'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - PORT=8080
      - LOG_LEVEL=debug
      - DB_HOST=db
      - DB_PORT=3306
      - DB_USER=${DB_USER:-taskapi}
      - DB_PASSWORD=${DB_PASSWORD:-dev_secret_123}
      - DB_NAME=${DB_NAME:-taskapi}
    depends_on:
      db:
        condition: service_healthy
    networks:
      - taskapi-net

  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD:-root_secret_123}
      MYSQL_DATABASE: ${DB_NAME:-taskapi}
      MYSQL_USER: ${DB_USER:-taskapi}
      MYSQL_PASSWORD: ${DB_PASSWORD:-dev_secret_123}
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${DB_ROOT_PASSWORD:-root_secret_123}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - taskapi-net

  adminer:
    image: adminer:4
    ports:
      - "8081:8080"
    depends_on:
      - db
    networks:
      - taskapi-net

volumes:
  mysql-data:
    driver: local

networks:
  taskapi-net:
    driver: bridge
```

**Napomena:** `task-api` trenutno koristi in-memory storage, tako da DB konfiguracija u app servisu nije funkcionalna — MySQL se pokreće ali app je još ne koristi. Ovo je Docker scaffolding koji ćeš koristiti u Lab 12 kad pređeš na MySQL storage.

---

### Korak 5 — Pokreni Docker Compose stack

```bash
docker compose up --build
```

Provjeri da sve radi u novom terminalu:

```bash
# task-api treba biti up
curl -s http://localhost:8080/tasks
# Ocekivano: [] (in-memory, prazan po startu)

# Adminer UI treba biti dostupan
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8081
# Ocekivano: 200
```

Otvori browser na `http://localhost:8081` — treba vidjeti Adminer login formu.

Zaustavi stack:

```bash
docker compose down
```

---

### Korak 6 — Worktree izolacija za risky izmjene

Sada ćemo vježbati worktree izolaciju. Simuliraćemo "risky" izmjenu: brisanje fajlova.

**Setup:**

```bash
# Provjeri git status — mora biti clean
git status

# Napravi worktree za experiment
git worktree add /tmp/task-api-experiment -b experiment/risky-changes
```

**U worktree-u izvrši risky izmjenu:**

```bash
cd /tmp/task-api-experiment

# Simuliraj gresku: obriši handler fajl
rm tasks/handler.go

# Provjeri da je obrisan
ls tasks/

# Commituj brisanje (namjerno losim commit-om)
git add -A
git commit -m "oops: deleted handler by mistake"
```

**Provjeri da je main branch netaknut:**

```bash
# Vrati se u main working tree
cd ~/projects/task-api  # ili gdje ti je projekat

# Provjeri da handler postoji
ls tasks/handler.go
# Output: tasks/handler.go (netaknut!)

# Build je i dalje ok
go build ./...
```

**Cleanup worktree:**

```bash
# Pogledaj worktree listu
git worktree list

# Obriši worktree (uz branch)
git worktree remove /tmp/task-api-experiment
git branch -d experiment/risky-changes
```

**Provjeri:**

```bash
git worktree list
# Treba biti samo main working tree
```

---

### Korak 7 — Postavi .claudeignore za Docker volumes

Docker compose volumes mogu akumulirati database datoteke. Ovo su binarni/sensitive fajlovi koje Claude ne treba čitati:

```bash
# Provjeri da je docker/volumes/ u .claudeignore
grep "docker/volumes" .claudeignore
```

Ako nisu, dodaj:

```bash
echo "docker/volumes/" >> .claudeignore
echo "mysql-data/" >> .claudeignore
```

Dodaj i u `.gitignore`:

```bash
echo "docker/volumes/" >> .gitignore
```

---

### Korak 8 — Commituj Docker konfiguraciju

```bash
git add Dockerfile docker-compose.yml .env.example .claudeignore .gitignore
git commit -m "infra: Docker setup — Dockerfile, Compose (MySQL + Adminer), .claudeignore"
```

**Provjeri da .env NIJE commitovan:**

```bash
git log --oneline -1
git show HEAD --name-only | grep ".env$"
# Ocekivano: nema output-a (prazno — .env nije u commit-u)
```

## Verifikacija

- [ ] `docker compose up --build` pokreće cijeli stack bez errora
- [ ] `curl -s http://localhost:8080/tasks` vraća `[]` kad je stack up
- [ ] Adminer je dostupan na `http://localhost:8081`
- [ ] `docker compose down` gasi stack cleanly
- [ ] Worktree experiment: brisanje fajla u worktree nije utjecalo na main branch
- [ ] `.env` nije u git historiji (`git log --all -- .env` vraća ništa)
- [ ] `.claudeignore` postoji i pokriva `.env`, `*.key`, `docker/volumes/`

## Šta si naučio

- **Dockerfile multi-stage build** drži production image mali — build stage s Go kompajlerom, runtime stage s Alpine
- **Docker Compose** je lokalni dev stack — MySQL + Adminer + app zajedno, izolirana mreža
- **Worktree izolacija** je "free" sandbox za risky izmjene — risky branch u zasebnom direktorijumu, main branch netaknut
- **Blast radius containment**: brisanje fajla u worktree-u je potpuno reversible, main branch je zaštićen sve dok ne mergaš
- **.claudeignore** sprečava Claude da čita secrets — kombinira se s `deny` listom u settings.json za duplu zaštitu
