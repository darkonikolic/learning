# Docker Compose za lokalni razvoj

## Zašto Compose

Jednom kada imaš više od jednog kontejnera, `docker run` postaje nepraktičan.

Za lokalni razvoj možda trebaš: nginx kao frontend, backend API, PostgreSQL bazu, Redis cache. To su četiri `docker run` komande sa desetak argumenata svaka — network flags, volume flags, environment variables, port mappings. Pamtiti ih sve i pokretati redom je nepraktično i error-prone.

Docker Compose rešava ovo sa jednim YAML fajlom koji opisuje ceo stack, i jednom komandom koja sve pokreće:

```bash
docker compose up
```

> **Podman:** `podman compose up`

I jednom komandom koja sve zaustavlja i čisti:

```bash
docker compose down
```

> **Podman:** `podman compose down`

> **Napomena za Podman Compose:**
> - macOS: `brew install podman-compose`
> - Linux: `pip3 install podman-compose`
> - Podman 4.x+ uključuje `podman compose` koji interno poziva podman-compose
> - Sintaksa je identična: `docker compose up -d` → `podman compose up -d`

Ovo je posebno moćno jer možeš imitirati produkcijski stack lokalno. Isti servisi, iste verzije, ista mrežna topologija. "Radi na mom računaru" više nije izgovor.

## Anatomija docker-compose.yml

```yaml
services:
  web:
    image: nginx:1.25.3-alpine
    ports:
      - "8080:80"
    volumes:
      - ./app:/usr/share/nginx/html:ro
    networks:
      - frontend

  api:
    build:
      context: .
      dockerfile: Dockerfile.api
    environment:
      - DB_HOST=db
      - DB_PORT=5432
    depends_on:
      db:
        condition: service_healthy
    networks:
      - frontend
      - backend

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: appdb
      POSTGRES_USER: appuser
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appuser -d appdb"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - backend

networks:
  frontend:
  backend:

volumes:
  pgdata:
```

**services** — svaki servis je jedan kontejner (ili više replika). Ime servisa postaje DNS ime na mreži.

**image vs build** — ili koristiš gotov image sa registry-ja, ili build-uješ lokalno iz Dockerfile-a.

**ports** — `"host:container"` mapiranje. Samo oni portovi koje eksplicitno mapiraš su dostupni sa hosta.

**volumes** — bind mountovi (./relativna/putanja) ili named volumes (pgdata). Named volumesi se deklarišu pod `volumes:` na dnu.

**networks** — servisi koji dele mrežu mogu međusobno komunicirati po imenu. `api` može dosegnuti `db` na `db:5432`. `web` ne može direktno dosegnuti `db` jer nisu na istoj mreži — dobra sigurnosna praksa.

**depends_on** — Compose čeka da `db` bude healthy pre nego što pokrene `api`. Bez zdravstvenog provjere, `api` bi se pokrenuo dok se DB još inicijalizuje i dobio connection error.

## Environment variables i .env fajl

Nikad ne stavljaj secrets u `docker-compose.yml`. Compose automatski čita `.env` fajl iz istog direktorijuma:

`.env`:
```
DB_PASSWORD=mojasuperlozinka
API_KEY=dev-key-ne-ide-u-git
```

`docker-compose.yml` referencira ih sa `${VAR_NAME}`:
```yaml
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD}
```

`.env` ide u `.gitignore`. Commitaš `docker-compose.yml`, ne commitaš `.env`. Novi developer kopira `.env.example` u `.env` i popunjava vrednosti.

`.env.example` (commitati u git):
```
DB_PASSWORD=changeme
API_KEY=your-dev-api-key-here
```

## Compose za project-A

Naš hello-world je jednostavan — samo nginx. Ali Compose nam daje live reload u development-u:

```yaml
# docker-compose.yml
services:
  web:
    image: nginx:1.25.3-alpine
    ports:
      - "8080:80"
    volumes:
      - ./app/index.html:/usr/share/nginx/html/index.html:ro
      - ./app/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
```

Pokreni:
```bash
docker compose up
```

> **Podman:** `podman compose up`

Sada edituj `app/index.html`, refresh browser — promjena je vidljiva bez restart kontejnera.

## Korisne Compose komande

```bash
# Pokreni sve servise (foreground, vidis logove)
docker compose up

# Pokreni u background-u
docker compose up -d

# Zaustavi i ukloni kontejnere (volumes ostaju)
docker compose down

# Zaustavi i ukloni kontejnere I volumes
docker compose down -v

# Logovi svih servisa
docker compose logs

# Logovi konkretnog servisa, pratiti live
docker compose logs -f web

# Uđi u running kontejner (exec)
docker compose exec web sh

# Restart jednog servisa
docker compose restart web

# Rebuild image-a (kada menjaš Dockerfile)
docker compose build

# Rebuild i pokreni
docker compose up --build

# Status
docker compose ps
```

> **Podman:** Sve gore navedene komande rade identično s `podman compose` umjesto `docker compose`.
> Primjeri: `podman compose up -d`, `podman compose logs -f web`, `podman compose down -v`
>
> **Podman Compose instalacija:**
> - macOS: `brew install podman-compose`
> - Linux: `pip3 install podman-compose`
> - Podman 4.x+ uključuje `podman compose` koji interno poziva podman-compose
> - Sintaksa je identična: `docker compose up -d` → `podman compose up -d`

## depends_on i health checks

Ovo je izvor mnogih bug-ova početnika:

```yaml
# PROBLEMATIČNO — depends_on bez condition čeka samo da kontejner KRENE
# ne čeka da servis bude SPREMAN
depends_on:
  - db

# ISPRAVNO — čeka da healthcheck prođe
depends_on:
  db:
    condition: service_healthy
```

PostgreSQL treba nekoliko sekundi da inicijalizuje bazu i počne prihvatati konekcije. Bez `service_healthy`, aplikacija se spoji pre nego što DB sluša, dobija connection refused, pada. Ovo je race condition.

Healthcheck je komanda koja se izvršava unutar kontejnera i vraća 0 (healthy) ili ne-nula (unhealthy):

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U appuser"]
  interval: 5s    # provjeravaj svakih 5 sekundi
  timeout: 3s     # smatra se failed ako ne odgovori za 3s
  retries: 10     # 10 neuspelih znači unhealthy
  start_period: 30s  # čekaj 30s pre prve provjere
```

Za nginx je jednostavno:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost/"]
  interval: 10s
  timeout: 3s
  retries: 3
```

## AI workflow

Kada Compose stack ne radi:

```
docker compose up izbacuje ovaj error:
[error output]

Moj docker-compose.yml:
[sadržaj]

Koji servis pada i zašto? Koji su sledeći koraci za debug?
```

Kada imaš networking problem između servisa:

```
Servis "api" ne može dosegnuti servis "db" na adresi db:5432.
Oba su u istom docker-compose.yml.

Evo network konfiguracije:
[relevantan deo yaml-a]

Zašto ne rade i kako da popravim?
```
