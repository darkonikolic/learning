# Best practices i bezbednost

## Zašto je bezbednost važna već u fazi Docker image-a

Napadač ne čeka produkciju. Kompromitovani image u registry-ju znači kompromitovanu produkciju čim se deploy pokrene. Mnogi napadi počinju upravo ovde: loše konfigurisani image, stare biblioteke sa poznatim CVE-jima, root procesi koji imaju sve privilegije.

Dobra vijest: ove prakse su jednostavne kad ih ugradiš od početka.

## Non-root user

Po defaultu, procesi u kontejneru se izvršavaju kao `root` (UID 0). Ako napadač pronađe RCE (Remote Code Execution) ranjivost u tvojoj aplikaciji, dobija root pristup unutar kontejnera.

Kontejner root nije isto što i host root — namespace izolacija pruža zaštitu — ali ipak nije zanemarivo, posebno u misconfigured okruženjima.

nginx:alpine image dolazi sa predefinisanim `nginx` korisnikom:

```dockerfile
FROM nginx:1.25.3-alpine

COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf

# nginx worker procesi rade kao nginx korisnik
# Master process mora biti root da bi bindao port 80, ali workers ne moraju
USER nginx

EXPOSE 80
```

Za vlastite aplikacije, dodaj korisnika eksplicitno:

```dockerfile
FROM python:3.11-alpine

# Kreiraj non-root korisnika
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Prebaci se na non-root korisnika
USER appuser

CMD ["python", "app.py"]
```

## Read-only filesystem

Ako aplikacija ne treba pisati na disk (a nginx koji servira statički HTML ne treba), postavi filesystem kao read-only:

```bash
docker run --read-only --rm -p 8080:80 helloworld:local
```

nginx treba pisati u `/tmp` i `/var/run` za pid fajlove. Montiraj te direktorijume kao tmpfs:

```bash
docker run --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  --tmpfs /var/cache/nginx \
  -p 8080:80 \
  helloworld:local
```

U docker-compose.yml:
```yaml
services:
  web:
    image: helloworld:local
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
      - /var/cache/nginx
```

Napadač koji dobije shell unutar kontejnera ne može instalirati alate ni pisati malware na filesystem.

## Resource limits

Bez limita, jedan kontejner može konzumirati sve CPU i RAM na hostu — namjerno ili zbog buga.

```yaml
services:
  web:
    image: nginx:1.25.3-alpine
    deploy:
      resources:
        limits:
          cpus: '0.5'      # max 50% jednog CPU core-a
          memory: 64M      # max 64 megabajta RAM-a
        reservations:
          cpus: '0.1'
          memory: 32M
```

U Kubernetes-u (modul 03) ovo se zove `requests` i `limits` i obavezno je za svaki pod.

## Secrets — ne u environment variables

Environment varijable nisu sigurne za secrets. Svako ko može pokrenuti `docker inspect` ili `docker exec env` vidi ih. Logovi aplikacije često ispisuju environment varijable. Kubernetes dashboard ih prikazuje.

```bash
# Vidi sve env varijable u running kontejneru
docker exec mycontainer env
docker inspect mycontainer  # env je u JSON outputu
```

Pravilo: environment variables su za konfiguraciju, ne za secrets.

Gdzie onda idu secrets?

```
Development:
├── .env fajl (ne ide u git, .gitignore)
└── docker secrets (za Docker Swarm, komplicovano za dev)

Produkcija (K8s):
├── Kubernetes Secrets (base64 encoded, ne šifrovani po defaultu)
├── AWS Secrets Manager + External Secrets Operator
└── HashiCorp Vault + Vault Agent injector
```

Za naš project-A: AWS credentials za Terraform idu kao CI/CD variables u GitLab (encrypted), ne u Dockerfile niti `docker-compose.yml`.

## Image scanning sa Trivy

Trivy skenira image-e na poznate ranjivosti (CVE) u:
- OS paketima (Alpine apk, Debian apt)
- Application dependencies (npm packages, pip packages, go modules)

```bash
# Skeniraj lokalni image
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest \
  image --severity HIGH,CRITICAL \
  helloworld:local
```

Primer output-a:
```
nginx:1.25.3-alpine (alpine 3.18.4)
Total: 0 (HIGH: 0, CRITICAL: 0)
```

Stariji base image bi mogao pokazati:
```
nginx:1.20-alpine (alpine 3.13.12)
Total: 23 (HIGH: 15, CRITICAL: 8)

┌──────────────┬────────────────┬──────────┬────────────────┐
│   Library    │ Vulnerability  │ Severity │ Fixed Version  │
├──────────────┼────────────────┼──────────┼────────────────┤
│ libssl1.1    │ CVE-2023-0215  │ HIGH     │ 1.1.1t-r0      │
│ libcrypto1.1 │ CVE-2023-0216  │ CRITICAL │ 1.1.1t-r0      │
└──────────────┴────────────────┴──────────┴────────────────┘
```

U GitLab CI pipeline-u (modul 07) Trivy scan je obavezan korak koji blokira deploy ako nađe CRITICAL ranjivosti.

## Minimalni base image

Veći base image = veća attack surface = više potencijalnih ranjivosti.

Hijerarhija po veličini (od manjeg ka većem):

```
scratch           → 0MB  — prazno, samo za binarne executable-e
distroless        → ~2MB — Google's minimal, bez shell-a
alpine            → ~5MB — minimalan Linux, ima sh i apk
alpine-based apps → 10-50MB
debian-slim       → ~70MB
ubuntu            → ~80MB
debian/ubuntu     → ~120MB
```

Za naš nginx: `nginx:alpine` (~23MB) umesto `nginx:latest` (nginx na Debian, ~140MB).

`distroless` je ekstreman ali moćan pristup — nema shell-a, nema package managera. Napadač koji dobije shell access nema čime da radi.

## Pin verzije — uvek

```dockerfile
# NIKAD OVAKO
FROM nginx:latest
FROM node:alpine
FROM python:3-slim

# UVEK OVAKO
FROM nginx:1.25.3-alpine
FROM node:20.11.0-alpine3.19
FROM python:3.11.7-slim-bookworm
```

`latest` tag nije verzija — to je pointer koji se pomera. Jednog dana `docker pull nginx:latest` povuče breaking change i tvoj CI/CD pipeline počne fail-ovati u produkciji bez da si ičta promenio.

Pin-uj čak i SHA digest za maksimalnu determinizam:

```dockerfile
FROM nginx:1.25.3-alpine@sha256:a0d0a0d46f8b984...
```

## .dockerignore je bezbjednosna mjera

```
# .dockerignore
.git
.env
.env.*
*.pem
*.key
*secret*
*credential*
secrets/
.aws/
node_modules
```

Bez `.dockerignore`, `COPY . .` može ubaciti `.env` fajl, SSH ključeve, AWS credentials — sve u image koji ide u registry.

## Sažetak checklist-e

Pri svakom Dockerfile pregledu:

- [ ] Base image je pinned na specifičnu verziju
- [ ] Non-root USER je postavljen
- [ ] `.dockerignore` postoji i pokriva secrets i .git
- [ ] Nema `ENV` ili `ARG` sa secrets vrijednostima
- [ ] Multi-stage build se koristi gdje ima smisla
- [ ] Trivy scan prolazi bez CRITICAL ranjivosti
- [ ] Resource limits su definisani (barem u Compose/K8s manifestima)
