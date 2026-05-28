# Multi-stage builds

## Problem sa jednostrukim build-om

Zamislimo da naš "Hello World" nije statički HTML već React aplikacija. Da bi se build-ovala, trebaš Node.js, npm, i sve dev dependencies. Ali kada je build završen i dobiješ `dist/` folder sa statičkim fajlovima — Node.js više nije potreban.

Bez multi-stage:

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install          # ~300MB node_modules
COPY . .
RUN npm run build        # generise dist/
# ... a sad svi ovi alati idu u finalni image
```

Rezultat: image od ~600MB koji sadrži Node.js, npm, sve dev dependencies, source code — od čega runtime treba samo `dist/` folder i nginx.

Ovo nije samo pitanje veličine. Veći image znači:
- Duži docker pull pri svakom deploy-u
- Veća attack surface (Node.js binary u prod može biti vektor napada)
- Više potencijalnih sigurnosnih propusta (npm packages u prod)

## Rešenje: multi-stage build

```dockerfile
# ─── Stage 1: BUILD ─────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production=false
COPY . .
RUN npm run build
# U ovom trenutku: /app/dist/ sadrži gotove fajlove

# ─── Stage 2: RUNTIME ───────────────────────────────────────
FROM nginx:1.25.3-alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

Ključna stvar: `COPY --from=builder` kopira fajlove iz prvog stage-a u drugi. Finalni image **nema** Node.js, npm, node_modules. Sadrži samo nginx binary i statičke fajlove.

## Kako Docker gradi multi-stage

Docker gradi stage-ove sekvencijalno. Možeš ih imenovati (`AS builder`) ili referencirati brojem (`--from=0`).

Finalni image je uvek zadnji `FROM` blok. Sve što nije eksplicitno kopirano iz prethodnih stage-ova ne postoji u finalnom image-u.

Docker može build-ovati samo određeni stage ako trebaš (korisno za debagovanje):
```bash
docker build --target builder -t myapp:debug .
```

> **Podman:** `podman build --target builder -t myapp:debug .`

## Merenje razlike

Za naš jednostavni nginx projekat (samo statički HTML), multi-stage nije potreban. Ali vidimo razliku na primeru sa Node.js:

```bash
# Single-stage image
docker image ls myapp:single-stage
# REPOSITORY   TAG           IMAGE ID   SIZE
# myapp        single-stage  abc123     612MB

# Multi-stage image
docker image ls myapp:multi-stage
# REPOSITORY   TAG          IMAGE ID   SIZE
# myapp        multi-stage  def456     23MB
```

> **Podman:** `podman image ls myapp:single-stage` / `podman image ls myapp:multi-stage`

23MB vs 612MB — razlika od 96%. U sistemu koji deploy-uje desete puta dnevno na više K8s nodova, ovo je značajno.

```bash
# Inspekcija slojeva image-a
docker history myapp:multi-stage
```

> **Podman:** `podman history myapp:multi-stage`

## Primer za project-A (prošireni scenario)

Naš project-A je za sada čist statički HTML bez build koraka. Ali kad bi bio React app:

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY src/ ./src/
COPY public/ ./public/
RUN npm run build

FROM nginx:1.25.3-alpine AS runtime
COPY --from=builder /app/build /usr/share/nginx/html
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

Trenutni project-A Dockerfile ostaje jednostavan:

```dockerfile
FROM nginx:1.25.3-alpine
COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

Znanje o multi-stage build-ovima koristićeš kada komplikuješ aplikaciju ili kad radite na projektima sa stvarnim build procesima.

## Nikad ne stavljaj secrets u Dockerfile

Česta greška:

```dockerfile
# NIKAD OVAKO — secret ostaje u image layeru zauvek
RUN aws configure set aws_access_key_id AKIA...
ENV DB_PASSWORD=mysecretpassword
ARG API_KEY=secret123
```

Čak i ako obriješeš secret u sledećem layeru, ostaje u image history. Svako ko ima pristup image-u može ga izvući:

```bash
docker history --no-trunc myimage  # vidi sve komande
docker save myimage | tar xO | tar xO  # raspakuje sve layere
```

> **Podman:** `podman history --no-trunc myimage` / `podman save myimage | tar xO | tar xO`

Secrets u kontejnere dolaze:
- Kao environment varijable pri pokretanju (`docker run -e DB_PASSWORD=$DB_PASSWORD`)
- Kao Kubernetes Secrets (modul 03+)
- Kao mounted volumes sa secrets fajlovima
- Kroz secret manager (AWS Secrets Manager, HashiCorp Vault)

Multi-stage build ima dodatnu prednost: `ARG` varijable postavljene u build stage-u ne proslijeđuju se u runtime stage.

## AI workflow

Kada imaš spor build i sumnjač na veličinu image-a:

```
Moj Docker image je 800MB. Evo Dockerfile-a:
[sadržaj]

1. Koliko bi trebao biti minimalni image za ovu aplikaciju?
2. Predloži multi-stage Dockerfile koji smanjuje veličinu
3. Koje od postojećih layera mogu kombinovati?
```
