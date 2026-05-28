# 04 — Delve Go konfiguracija

## Zašto Delve zahtijeva poseban build

Go compiler standardno primjenjuje dvije optimizacije koje sprečavaju ispravno debuggovanje:

**Compiler optimizacije (`-N` disable):**
- Dead code elimination: compiler uklanja kod koji smatra nepotrebnim
- Constant folding: `x = 2 + 2` postaje `x = 4` → varijabla `x` možda ne postoji u runtime-u
- Register allocation: varijable žive u CPU registrima, ne na stack-u → Delve ne može čitati njihove vrijednosti

**Inlining (`-l` disable):**
- Compiler kopira tijelo male funkcije direktno u caller
- Rezultat: call stack u debuggeru ne prikazuje inlined funkcije
- Breakpoint na inlined funkciji se nikad ne aktivira

Bez `-gcflags="all=-N -l"`, Delve može prikazivati netačne vrijednosti varijabli ili preskakati breakpoint-e.

---

## `docker/go/Dockerfile.debug`

```dockerfile
# docker/go/Dockerfile.debug

# Stage 1: Build sa Delve
FROM golang:1.22-alpine AS debug-builder

# Instaliraj Delve u builder stage
# Fiksirana verzija za reproduktibilnost
RUN go install github.com/go-delve/delve/cmd/dlv@v1.22.1

WORKDIR /app

# Kopiraj dependency fajlove posebno da iskoristimo layer cache
# Ako se go.mod i go.sum ne mijenjaju, RUN go mod download se ne ponavlja
COPY go.mod go.sum ./
RUN go mod download

# Kopiraj ostatak koda
COPY . .

# Build sa debug flagovima
# -gcflags="all=-N -l":
#   all=   → primijeni na sve pakete (uključujući dependencies)
#   -N     → disables optimizations
#   -l     → disables inlining
# CGO_ENABLED=0 → statički linked binary, radi u alpine bez glibc
# -o /app/server → output putanja
RUN CGO_ENABLED=0 go build \
    -gcflags="all=-N -l" \
    -o /app/server \
    ./cmd/server/

# Stage 2: Runtime debug image
FROM golang:1.22-alpine AS debug
# Koristimo golang:1.22-alpine umjesto scratch/distroless jer Delve
# treba shell i proc filesystem za ptrace operacije

# Kopiraj Delve binary iz buildera
COPY --from=debug-builder /go/bin/dlv /dlv

# Kopiraj aplikacijski binary
COPY --from=debug-builder /app/server /app/server

# CA certificates za HTTPS pozive prema vanjskim API-jima
COPY --from=debug-builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# API port aplikacije i Delve debug port
EXPOSE 8080 40000

# Delve pokreće aplikaciju i sluša na debug portu
# --headless: server mode, čeka VS Code konekciju (ne interaktivni terminal)
# --listen=:40000: sluša na svim interfejsima na portu 40000
# --api-version=2: VS Code Go ekstenzija zahtijeva API v2
# --accept-multiclient: dozvoli ponovnu konekciju bez restart-a servera
#                       Korisno kad zatvoriš VS Code debug session i rekonektuješ
# --continue: odmah nastavi izvršavanje umjesto čekanja na debugger
#             Bez ovoga server ne prima requestove dok se VS Code ne konektuje
CMD ["/dlv", "exec", "/app/server", \
     "--headless", \
     "--listen=:40000", \
     "--api-version=2", \
     "--accept-multiclient", \
     "--continue"]
```

### Alternativni CMD za sporiji start (čeka na debugger)

Ako hoćeš da server čeka dok se VS Code ne konektuje (korisno za debuggovanje init koda):

```dockerfile
# BEZ --continue: server čeka na konekciju debuggera
CMD ["/dlv", "exec", "/app/server", \
     "--headless", \
     "--listen=:40000", \
     "--api-version=2", \
     "--accept-multiclient"]
```

Ovo je korisno ako imaš bug u startup sekvenci koji se desi prije nego što request stigne.

---

## `docker-compose.override.yml` za Go

```yaml
# docker-compose.override.yml
version: "3.9"

services:
  go-service:
    build:
      context: ./services/go-service
      # Koristimo poseban Dockerfile za debug
      dockerfile: ../../docker/go/Dockerfile.debug
    ports:
      - "8080:8080"    # Aplikacijski HTTP port
      - "40000:40000"  # Delve debug port
    security_opt:
      # Ukloni seccomp restrikcije za ptrace syscall
      # Docker defaultno blokira ptrace via seccomp profil
      # Bez ovoga Delve ne može inspectovati Go process
      # SAMO za development!
      - "seccomp:unconfined"
    cap_add:
      # Dodaj SYS_PTRACE capability
      # Linux kernel zahtijeva ovu capability za ptrace()
      # Delve koristi ptrace za: breakpoints, single-step, memory inspection
      - SYS_PTRACE
    environment:
      - APP_ENV=development
      - LOG_LEVEL=debug
    volumes:
      # Opcionalno: mount source koda ako koristiš dlv s live rebuild
      # Za standardni dlv exec workflow ovo nije potrebno
      - ./services/go-service:/app/src
```

### Zašto `SYS_PTRACE` i `seccomp:unconfined`

ptrace je Linux syscall koji jednom procesu dozvoljava da inspectuje i kontroliše drugi. Debugger (Delve) koristi ptrace za:
- Postavljanje breakpoint-a (zamjenjuje CPU instrukciju sa `INT3`)
- Single-step izvršavanje
- Čitanje/pisanje memorije i registara debugiranog procesa

Docker defaultno primjenjuje seccomp profil koji blokira ptrace i oko 44 druga syscall-a. `seccomp:unconfined` uklanja ove restrikcije.

U produkciji, `SYS_PTRACE` i `seccomp:unconfined` su potencijalne sigurnosne rupe (container escape vektori).

---

## `.vscode/launch.json` za Go (dodati uz PHP config)

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug (PHP)",
      "type": "php",
      "request": "launch",
      "port": 9003,
      "pathMappings": {
        "/app/src": "${workspaceFolder}/services/php-service/src"
      },
      "log": true
    },
    {
      "name": "Attach to Go service (Delve)",
      "type": "go",
      "request": "attach",
      "mode": "remote",
      "host": "127.0.0.1",
      "port": 40000,
      "dlvLoadConfig": {
        "followPointers": true,
        "maxVariableRecurse": 3,
        "maxStringLen": 512,
        "maxArrayValues": 64,
        "maxStructFields": -1
      },
      "substitutePath": [
        {
          "from": "${workspaceFolder}/services/go-service",
          "to": "/app"
        }
      ]
    }
  ]
}
```

`dlvLoadConfig` detalji:
- `followPointers`: prati pokazivače automatski (bez ovoga vidiš samo memorijsku adresu)
- `maxVariableRecurse`: dubina za nested struct-ove (3 je dobar balans performanse i preglednosti)
- `maxStringLen`: maksimalna dužina prikazanog stringa (512 je OK za JWT tokene, ali ne za HTML response)
- `maxArrayValues`: koliko array/slice elemenata prikazati
- `maxStructFields`: `-1` znači sva polja (bez limita)

`substitutePath`: ekvivalent PHP `pathMappings`. Go Delve protokol koristi drugačiji ključ naziv.
- `from`: lokalna putanja (kako VS Code vidi source fajlove)
- `to`: putanja unutar kontejnera (kako Delve vidi fajlove pri kompajliranju)

---

## Korak po korak verifikacija

### Korak 1: Pokreni go-service sa debug build-om

```bash
docker compose up --build go-service
```

> **Podman:** `podman compose up --build go-service`

### Korak 2: Provjeri da Delve čeka na konekciju

```bash
docker compose logs go-service
```

> **Podman:** `podman compose logs go-service`

Mora se vidjeti:
```
go-service-1  | API server listening at: [::]:40000
go-service-1  | debugserver-@(#)PROGRAM:LLDB  PROJECT:lldb-1600.0.36 ...
```

Ili jednostavnije:
```bash
# Provjeri da je port otvoren
nc -z localhost 40000 && echo "Delve listens" || echo "Delve NOT listening"
```

### Korak 3: Attach VS Code debugger

1. VS Code → Run and Debug (`Ctrl+Shift+D`)
2. Odaberi "Attach to Go service (Delve)" iz dropdown-a
3. Klikni zelenu "Play" strelicu (ili `F5`)
4. Status bar ne mijenja boju kao za PHP — provjeri da je debug toolbar vidljiv

### Korak 4: Postavi breakpoint i testiraj

```go
// services/go-service/internal/handlers/auth.go
func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
    var req LoginRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        // Postavi breakpoint ovdje ← linija 15
        http.Error(w, "invalid request", http.StatusBadRequest)
        return
    }
    // Ili ovdje ← linija 20
    user, err := h.userService.Authenticate(req.Email, req.Password)
```

```bash
# Pošalji request
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass"}'
```

VS Code pauzira na breakpointu. U lijevom panelu:
- **Variables > Local**: `req` struct, `w`, `r`
- **Variables > Package**: package-level varijable
- Hover nad `req` u editoru prikazuje inline vrijednosti

### Korak 5: Goroutine debugging

Go koristi goroutine-e umjesto thread-ova. Delve prikazuje sve goroutine-e:

U VS Code Debug Console (`Ctrl+Shift+Y`):
```
dlv goroutines
# Lista svih goroutine-a, njihov status i stack trace
```

Promijeni aktivnu goroutine:
```
dlv goroutine 5
# Switch na goroutine 5
```

---

## Česte greške i rješenja

### Greška 1: "could not launch process: decoding dwarf section info"

```
Error: could not launch process: decoding dwarf section info at offset 0x...
```

**Uzrok**: Binary je kompajliran BEZ `-gcflags="all=-N -l"`, ili je strip-ovan.

**Rješenje**: Rebuild sa ispravnim flagovima.

```bash
# Provjeri da li binary ima debug simbole
docker exec go-service file /app/server
# Output mora sadržavati: "not stripped"
# Ako piše "stripped" → binary nema debug simbole

# Provjeri compose config koji Dockerfile target se koristi
docker compose config | grep dockerfile
```

> **Podman:** `podman exec go-service file /app/server`
> **Podman:** `podman compose config | grep dockerfile`

### Greška 2: "dial tcp 127.0.0.1:40000: connect: connection refused"

**Uzroci:**
- Compose override nije aktivan (koristi se base image bez Delve)
- Delve nije startovao (greška pri pokretanju aplikacije)
- Port 40000 nije mapiran

**Dijagnoza:**
```bash
# Da li port sluša na hostu?
lsof -i :40000

# Da li Delve radi unutar kontejnera?
docker exec go-service ps aux | grep dlv

# Da li je kontejner izgradjen sa debug Dockerfile-om?
docker inspect go-service | grep -A3 "Image"

# Čitaj logove od starta
docker compose logs --since=0 go-service
```

> **Podman:** `podman exec go-service ps aux | grep dlv`
> **Podman:** `podman inspect go-service | grep -A3 "Image"`
> **Podman:** `podman compose logs --since=0 go-service`

### Greška 3: "Permission denied" / ptrace failures

```
could not attach to pid 1: open /proc/1/mem: permission denied
```

**Uzrok**: Kontejner nema `SYS_PTRACE` capability ili seccomp blokira syscall.

**Rješenje**: Provjeri `docker-compose.override.yml`:
```yaml
security_opt:
  - "seccomp:unconfined"
cap_add:
  - SYS_PTRACE
```

Provjeri da override.yml se koristi:
```bash
docker compose config | grep -A5 security_opt
# Mora pokazati seccomp:unconfined
```

> **Podman:** `podman compose config | grep -A5 security_opt`

### Greška 4: Breakpoint se ne aktivira (žuta tačka)

Žuta tačka umjesto crvene = VS Code ne može mapirati breakpoint na binarni kod.

**Uzroci:**
- `substitutePath` u `launch.json` je pogrešan
- Source fajl lokalno i u kontejneru su drugačije verzije
- Funkcija je inlined (kompajlirana bez `-l`)

**Dijagnoza:**
```bash
# Gdje Delve vidi source fajlove?
# U VS Code Debug Console:
dlv sources
# Lista svih source putanja prema kojima je binary kompajliran
# Mora biti: /app/internal/handlers/auth.go itd.

# Lokalna putanja projekta mora mapirati na /app
# U launch.json substitutePath:
# "from": "${workspaceFolder}/services/go-service"  
# "to": "/app"
```

### Greška 5: Port 40000 zauzet

```bash
lsof -i :40000
# Vidiš koji process koristi port

# Promijeni port na svim mjestima:
# 1. docker-compose.override.yml: ports: "40001:40000" ili "40001:40001"
# 2. Dockerfile.debug CMD: --listen=:40001
# 3. launch.json: "port": 40001
```

---

## Multi-service debugging: PHP i Go istovremeno

Možeš imati aktivne oba debug sessiona u VS Code istovremeno.

VS Code "compounds" u `launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Listen for Xdebug (PHP)",
      "type": "php",
      "request": "launch",
      "port": 9003,
      "pathMappings": {
        "/app/src": "${workspaceFolder}/services/php-service/src"
      }
    },
    {
      "name": "Attach to Go service (Delve)",
      "type": "go",
      "request": "attach",
      "mode": "remote",
      "host": "127.0.0.1",
      "port": 40000,
      "substitutePath": [
        {
          "from": "${workspaceFolder}/services/go-service",
          "to": "/app"
        }
      ]
    }
  ],
  "compounds": [
    {
      "name": "Debug PHP + Go",
      "configurations": ["Listen for Xdebug (PHP)", "Attach to Go service (Delve)"],
      "stopAll": true
    }
  ]
}
```

Sa `compounds`, odabereš "Debug PHP + Go" i oba debugger-a se pokreću odjednom. Kad PHP pozove Go servis, možeš pratiti request od jednog do drugog postavljanjem breakpoint-a u oba servisa.
