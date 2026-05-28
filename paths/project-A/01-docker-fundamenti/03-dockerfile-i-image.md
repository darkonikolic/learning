# Dockerfile i image

## Dockerfile je recept

Dockerfile je tekstualni fajl koji opisuje kako se gradi Docker image. Svaka linija je instrukcija. Docker daemon izvršava instrukcije redom i za svaku kreira novi layer.

Naš Dockerfile za project-A nginx app:

```dockerfile
FROM nginx:alpine
COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

Četiri linije. Razumevanje svake je razumevanje šta image radi.

## FROM — početna tačka

```dockerfile
FROM nginx:alpine
```

Svaki image mora početi od nekog base image-a. `nginx:alpine` je zvanični nginx image baziran na Alpine Linux — minimalna Linux distribucija (~5MB umesto ~70MB za Ubuntu-based image-e).

`nginx:alpine` dolazi sa:
- Alpine Linux base (busybox, sh, apk package manager)
- nginx binary
- Default nginx konfiguracija
- Nginx već konfigurisan da pokrene pri startu kontejnera

Zbog toga nam ne treba `RUN nginx` niti `CMD nginx` — base image to već rešava.

Uvek pin-uj verziju: `FROM nginx:1.25.3-alpine` umesto `FROM nginx:alpine`. `alpine` tag prati najnoviju verziju, i jednog dana u pipeline-u možeš dobiti breaking change bez da si promenio ništa.

## COPY — fajlovi iz build konteksta u image

```dockerfile
COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
```

Format: `COPY <source-na-hostu> <destination-u-image-u>`

Source je relativan u odnosu na **build context** — folder koji prosleduješ `docker build` komandi (tipično `.`).

`/usr/share/nginx/html/` je default nginx web root. Fajlovi tu su dostupni kao web stranice.

`/etc/nginx/conf.d/default.conf` je nginx konfiguracija. Zamenimo default sa našom verzijom koja definiše kako nginx servira fajlove.

## EXPOSE — dokumentacija porta

```dockerfile
EXPOSE 80
```

`EXPOSE` **ne otvara** port na host mašini. To je dokumentacija — govori korisniku image-a koji port kontejner sluša. Stvarno mapiranje porta radi se pri pokretanju:

```bash
docker run -p 8080:80 helloworld:local
#               ↑    ↑
#          host port  container port
```

> **Podman:** `podman run -p 8080:80 helloworld:local`

Sada `http://localhost:8080` ide na port 80 unutar kontejnera, gde nginx sluša.

## RUN — izvršavanje komandi

Nema ga u našem Dockerfilu, ali razumevanje je neophodno:

```dockerfile
RUN apk add --no-cache curl
RUN mkdir -p /var/log/myapp
```

`RUN` izvršava komandu **tokom build faze** i kreira novi layer. Koristiš ga za instalaciju paketa, kreiranje direktorijuma, postavljanje permissions.

Svaki `RUN` je zasebni layer. Kombinuj ih sa `&&` kad logički idu zajedno:

```dockerfile
# Loše — 3 layera, svaki sadrži apk cache
RUN apk update
RUN apk add curl
RUN apk add vim

# Dobro — 1 layer, cache se čisti unutar istog layera
RUN apk update && apk add --no-cache curl vim
```

## CMD i ENTRYPOINT — šta se pokreće

```dockerfile
# Nije u našem Dockerfile, ali nginx:alpine ima:
CMD ["nginx", "-g", "daemon off;"]
```

`CMD` definiše default komandu kada pokrenemo kontejner. Može se override-ovati pri `docker run`.

`daemon off` znači: nginx radi u foreground-u, ne u background-u. Ovo je kritično za kontejnere — kada main proces završi, kontejner staje. Nginx u background-u bi odmah vratio exit 0 i kontejner bi nestao.

Razlika `CMD` vs `ENTRYPOINT`:
- `CMD` je default, može se override-ovati: `docker run myimage /bin/sh`
- `ENTRYPOINT` je fiksno, argument se dodaje na njega

## Layer caching — redosled direktiva je bitan

Docker kešira svaki layer. Ako se layer nije promenio od poslednjeg build-a, Docker ga ne gradi ponovo — koristi keš.

Ali: ako se bilo koji layer promeni, svi layeri **posle njega** se moraju ponovo graditi.

```dockerfile
# Loše po keširanju:
FROM node:20-alpine
COPY . /app           # ← svaka promena source koda invalidira ovaj layer
WORKDIR /app
RUN npm install       # ← i ovaj, pa npm install radi uvek iznova
```

```dockerfile
# Dobro po keširanju:
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./  # ← menja se retko
RUN npm install                          # ← ostaje u kešu dok se deps ne mene
COPY . .                                 # ← source code, menja se često
```

Za naš nginx projekat ovo nije problem — nemamo build koraka, jedino kopiramo fajlove.

## .dockerignore

Kad pokreneš `docker build .`, Docker šalje **ceo folder** daemonu kao build context, pre nego što pročita Dockerfile. `.dockerignore` govori šta da isključi.

```
# .dockerignore
.git
.gitignore
node_modules
*.log
.env
.DS_Store
README.md
```

Bez ovoga, Docker šalje `.git` folder (može biti stotine MB), `node_modules` (stotine hiljada fajlova), `.env` fajlove sa secrets-ima. To usporava build i može kompromitovati sigurnost.

## Praktičan primer — naš project-A Dockerfile

Struktura projekta:

```
project-a/
├── app/
│   ├── index.html
│   └── nginx.conf
├── Dockerfile
└── .dockerignore
```

`app/index.html`:
```html
<!DOCTYPE html>
<html>
  <head><title>Project A</title></head>
  <body><h1>Hello World</h1></body>
</html>
```

`app/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html;
    }
}
```

`Dockerfile`:
```dockerfile
FROM nginx:1.25.3-alpine
COPY app/index.html /usr/share/nginx/html/
COPY app/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

`.dockerignore`:
```
.git
.gitignore
*.md
.DS_Store
```

Build i pokretanje:
```bash
docker build -t helloworld:local .
docker run --rm -p 8080:80 helloworld:local
# http://localhost:8080 → Hello World
```

> **Podman:** `podman build -t helloworld:local .` / `podman run --rm -p 8080:80 helloworld:local`

## AI workflow

Kada pišeš Dockerfile za novu aplikaciju, dobra startna tačka:

```
Imam [tip aplikacije, npr. Python Flask app].
Treba mi Dockerfile za produkcijsku upotrebu.
Zahtevi: minimalni image size, ne-root user, no secrets.
Pokaži mi Dockerfile i objasni svaku direktivu.
```

Kada optimizuješ postojeći Dockerfile:

```
Ovaj Docker build traje 4 minute. Analiziraj Dockerfile
i predloži optimizacije za layer caching:
[Dockerfile sadržaj]
```
