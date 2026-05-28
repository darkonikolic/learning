# LAB: Kontejnerizuj app

## Cilj

Na kraju ovog laba imaš:
- `app/index.html` i `app/nginx.conf` na disku
- Dockerfile koji ih pakuje u nginx image
- Running kontejner dostupan na `http://localhost:8080`
- Docker Compose setup za development workflow
- Razumevanje šta se desilo na svakom koraku

Vreme: ~30-45 minuta.

## Provjera preduslova

```bash
docker --version
# Docker version 25.x.x ili noviji

docker compose version
# Docker Compose version 2.x.x

docker run --rm hello-world
# Hello from Docker!
```

> **Podman:** `podman --version` / `podman compose version` / `podman run --rm hello-world`

Ako nešto od ovoga ne radi, ne nastavljaj. Popravi Docker instalaciju.

## Korak 1 — Struktura projekta

Napravi folder i inicijalizuj git:

```bash
mkdir -p ~/projects/project-a/app
cd ~/projects/project-a
git init
```

## Korak 2 — index.html

Napravi `app/index.html`:

```html
<!DOCTYPE html>
<html lang="sr">
  <head>
    <meta charset="UTF-8">
    <title>Project A</title>
    <style>
      body {
        font-family: sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 100vh;
        margin: 0;
        background: #f0f4f8;
      }
      .box {
        text-align: center;
        padding: 2rem;
        background: white;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      }
    </style>
  </head>
  <body>
    <div class="box">
      <h1>Hello World</h1>
      <p>Project A — running in Docker</p>
    </div>
  </body>
</html>
```

## Korak 3 — nginx.conf

Napravi `app/nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;

    # Logging
    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;

    location / {
        root  /usr/share/nginx/html;
        index index.html;
    }

    # Healthcheck endpoint za K8s (koristićemo u modulu 03)
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

`/health` endpoint sada ne koristimo, ali biće potreban za Kubernetes liveness probe.

## Korak 4 — Dockerfile

Napravi `Dockerfile` u root-u projekta:

```dockerfile
FROM nginx:1.25.3-alpine
COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

## Korak 5 — .dockerignore

```
.git
.gitignore
*.md
.DS_Store
.env
.env.*
```

## Korak 6 — Build image

```bash
docker build -t helloworld:local .
```

> **Podman:** `podman build -t helloworld:local .`

Očekivani output:
```
[+] Building 2.1s (8/8) FINISHED
 => [internal] load build definition from Dockerfile
 => [internal] load .dockerignore
 => [internal] load metadata for docker.io/library/nginx:1.25.3-alpine
 => CACHED [1/3] FROM docker.io/library/nginx:1.25.3-alpine
 => [2/3] COPY app/index.html /usr/share/nginx/html/
 => [3/3] COPY app/nginx.conf /etc/nginx/conf.d/default.conf
 => exporting to image
 => naming to docker.io/library/helloworld:local
```

Provjeri da image postoji:
```bash
docker image ls helloworld
# REPOSITORY   TAG     IMAGE ID       CREATED          SIZE
# helloworld   local   abc123def456   10 seconds ago   42MB
```

> **Podman:** `podman image ls helloworld`

## Korak 7 — Pokreni kontejner

```bash
docker run --rm -p 8080:80 helloworld:local
```

> **Podman:** `podman run --rm -p 8080:80 helloworld:local`

`--rm` znači: obriši kontejner kada se zaustavi (nema "mrtvih" kontejnera).

Otvori browser: **http://localhost:8080**

Treba da vidiš "Hello World" stranicu.

Zaustavi kontejner: `Ctrl+C`

## Korak 8 — Inspekcija

Pokreni kontejner u background-u:

```bash
docker run -d --name helloworld-test -p 8080:80 helloworld:local
```

> **Podman:** `podman run -d --name helloworld-test -p 8080:80 helloworld:local`

Provjeri logove:
```bash
docker logs helloworld-test
# nginx startup logove

# Prati logove live (curl iz drugog terminala pa vidiš access log)
docker logs -f helloworld-test
```

> **Podman:** `podman logs helloworld-test` / `podman logs -f helloworld-test`

Provjeri šta radi unutar kontejnera:
```bash
docker inspect helloworld-test
# JSON sa svim detaljima: IP adresa, environment, mounts, state
```

> **Podman:** `podman inspect helloworld-test`

Uđi unutra:
```bash
docker exec -it helloworld-test sh
# Otvara shell unutar running kontejnera

ls /usr/share/nginx/html/
# index.html  50x.html

cat /etc/nginx/conf.d/default.conf
# naša konfiguracija

exit
```

> **Podman:** `podman exec -it helloworld-test sh`

Zaustavi i ukloni:
```bash
docker stop helloworld-test
docker rm helloworld-test
```

> **Podman:** `podman stop helloworld-test` / `podman rm helloworld-test`

## Korak 9 — Docker Compose za development

Napravi `docker-compose.yml`:

```yaml
services:
  web:
    image: nginx:1.25.3-alpine
    ports:
      - "8080:80"
    volumes:
      - ./app/index.html:/usr/share/nginx/html/index.html:ro
      - ./app/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "-O-", "http://localhost/health"]
      interval: 10s
      timeout: 3s
      retries: 3
```

Zašto `image:` umesto `build:`? U development-u koristimo nginx direktno jer radimo samo na HTML/konfig fajlovima. Bind mountovi daju live reload. Kada idemo na registry i pipeline, koristimo `build:`.

Pokreni:
```bash
docker compose up
```

> **Podman:** `podman compose up`

Otvori `http://localhost:8080`. Sada edituj `app/index.html` — promeni "Hello World" u nešto drugo. Refresh browser — promjena je trenutna.

Zaustavi:
```bash
# Ctrl+C, ili iz drugog terminala:
docker compose down
```

> **Podman:** `podman compose down`

## Korak 10 — Provjera sa curl

```bash
# U jednom terminalu:
docker compose up -d

# Provjeri stranicu
curl http://localhost:8080
# Vraća HTML

# Provjeri health endpoint
curl http://localhost:8080/health
# healthy

# Provjeri HTTP status
curl -o /dev/null -s -w "%{http_code}" http://localhost:8080
# 200

docker compose down
```

> **Podman:** `podman compose up -d` / `podman compose down`

## Struktura na kraju laba

```
project-a/
├── app/
│   ├── index.html
│   └── nginx.conf
├── Dockerfile
├── docker-compose.yml
└── .dockerignore
```

## Šta si napravio i zašto je to važno

Ovi četiri fajla su osnova za sve što dolazi. U modulu 02 ovaj image ćeš push-nuti u GitLab Container Registry. U modulu 03 isti image ćeš deploajovati na lokalni Kubernetes. U modulu 07 GitLab CI/CD pipeline će automatski build-ovati ovaj Dockerfile na svaki `git push`.

Image je konstantan. Infrastruktura oko njega se menja (laptop → kind → EKS), ali `helloworld:local` image je uvek isti artifact.

## AI workflow — kad nešto ne radi

Ako `docker build` fail-uje:
```
docker build -t helloworld:local . daje ovaj error:
[paste celog error output-a]

Moj Dockerfile:
[sadržaj]

Struktura direktorijuma:
[ls -la output]

Šta je problem?
```

Ako kontejner pada odmah:
```
docker run -p 8080:80 helloworld:local izlazi odmah sa exit kodom 1.

docker logs helloworld-test:
[paste logova]

Šta nginx greška znači i kako da popravljam nginx.conf?
```

Ako port 8080 nije dostupan:
```
docker run radi (docker ps ga pokazuje), ali
curl http://localhost:8080 daje "Connection refused".

docker ps output:
[paste]

docker inspect helloworld output (network section):
[paste]

Zašto port nije dostupan?
```
