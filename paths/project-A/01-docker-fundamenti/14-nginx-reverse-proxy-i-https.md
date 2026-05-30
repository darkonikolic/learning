# 14 — nginx kao reverse proxy i HTTPS lokalno

## Zašto reverse proxy — ne izlagati app direktno

App kontejner sluša na portu 8080. Taj port nije namijenjen za direktni pristup iz browsera u produkciji niti lokalno. nginx stoji ispred kao kapija:

**TLS offload:** App ne mora znati ništa o certifikatima. nginx prima HTTPS konekciju, dešifrira je, i prosljeđuje čisti HTTP na `app:8080` kroz interni Docker network. App je jednostavnija, certifikati su na jednom mjestu.

**Jedan nginx, više servisa:** nginx može routati po putanji — `/api` ide na Go servis, `/` ide na Vue app — bez da klijent zna da postoje dva backenda.

**HTTP → HTTPS redirect na jednom mjestu:** Redirect pravilo je u nginx konfiguraciji, ne u aplikacionom kodu. Kada sutra promijeniš policy, mijenjamo jedan fajl.

**Security headers na jednom mjestu:** HSTS, X-Frame-Options, X-Content-Type-Options — sve u nginx, ne razbacano po aplikacijama.

Pattern koji se ne mijenja kroz cio project-A path:

```
Browser :443
    ↓  TLS termination
  nginx (reverse proxy)
    ↓  plain HTTP, interni Docker/K8s network
  app :8080
```

---

## Dvije opcije za lokalne certifikate

### Opcija A — mkcert (preporučeno)

mkcert kreira lokalni CA i dodaje ga u browser truststore. Rezultat: browser vjeruje certifikatu bez upozorenja, ista iskustvo kao na produkciji.

```bash
# Instalacija (jednom)
brew install mkcert
mkcert -install  # dodaje lokalni CA u browser truststore — traži lozinku

# Generisanje certifikata za projekat
mkdir -p certs
mkcert -key-file certs/app.local.key -cert-file certs/app.local.crt app.local localhost 127.0.0.1
```

`mkcert -install` treba pokrenuti samo jednom po mašini. Nakon toga svi certifikati generirani s mkcert su automatski trusted.

### Opcija B — openssl self-signed

Browser prikazuje upozorenje "nije sigurno", ali certifikat tehnički radi. Korisno za automatizirano testiranje (curl -k) i CI okruženja gdje browser truststore nije relevantan.

```bash
mkdir -p certs
openssl req -x509 -nodes -days 365 \
  -keyout certs/app.local.key \
  -out certs/app.local.crt \
  -subj "/CN=app.local" \
  -addext "subjectAltName=DNS:app.local,DNS:localhost,IP:127.0.0.1"
```

`-nodes` znači "no DES" — privatni ključ nije enkriptiran lozinkom (nginx ga čita bez interakcije). `subjectAltName` je obavezan za moderne browsere — CN polje samo više nije dovoljno.

---

## nginx konfiguracija kao reverse proxy

Napravi `nginx/nginx.conf`:

```nginx
# nginx/nginx.conf
server {
    listen 80;
    server_name app.local localhost;

    # HTTP → HTTPS redirect
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name app.local localhost;

    ssl_certificate     /etc/nginx/certs/app.local.crt;
    ssl_certificate_key /etc/nginx/certs/app.local.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;

    location / {
        proxy_pass         http://app:8080;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}
```

`proxy_set_header X-Forwarded-Proto $scheme` govori app-u da je originalni protokol bio HTTPS — bitno za URL generisanje u aplikaciji (redirecti, linkovi).

---

## docker-compose.yml sa nginx ispred

```yaml
services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    restart: unless-stopped

  app:
    build: .
    # NEMA ports prema hostu — samo nginx može pristupiti app-u
    expose:
      - "8080"
    restart: unless-stopped
```

### Razlika između `ports` i `expose`

| Direktiva | Znači | Ko može pristupiti |
|-----------|-------|--------------------|
| `ports: - "8080:80"` | Mapira host port 8080 na kontejner port 80 | Browser na hostu, svi |
| `expose: - "8080"` | Dokumentuje port unutar Docker networka | Samo drugi kontejneri u istoj mreži |

`expose` bez `ports` znači: nginx kontejner može kontaktirati `app:8080`, ali `curl http://localhost:8080` s hosta dobija "Connection refused". To je željeno ponašanje — jedini ulaz je kroz nginx.

---

## /etc/hosts entry za app.local

Da bi `app.local` radio u browseru lokalno, trebaš DNS mapping:

```bash
echo "127.0.0.1 app.local" | sudo tee -a /etc/hosts
```

Provjeri:
```bash
ping app.local
# PING app.local (127.0.0.1)
```

---

## Provjera da radi

```bash
# Pokreni stack
docker compose up -d

# Provjeri redirect (HTTP → HTTPS)
curl -I http://localhost
# HTTP/1.1 301 Moved Permanently
# Location: https://localhost/

# Provjeri HTTPS sadržaj
# Sa mkcert (trusted cert) — bez -k:
curl https://localhost
curl https://app.local

# Sa openssl self-signed — potreban -k (skip cert validation):
curl -k https://localhost

# Provjeri da app nije direktno dostupan s hosta:
curl http://localhost:8080
# curl: (7) Failed to connect to localhost port 8080: Connection refused
```

`docker compose ps` treba pokazivati nginx sa portovima 0.0.0.0:80 i 0.0.0.0:443, a app bez ikakvih mapiranih portova prema hostu.

---

## Struktura fajlova

```
project-a/
├── certs/
│   ├── app.local.crt
│   └── app.local.key
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
└── Dockerfile
```

`certs/` mora biti u `.gitignore` — privatni ključevi se ne commituju:

```
# .gitignore
certs/
```

---

## Veza sa ostalim okruženjima

Ovaj nginx pattern je identičan u svim okruženjima — samo certifikat dolazi s drugog mjesta:

| Okruženje | Ko terminira TLS | Certifikat |
|-----------|-----------------|------------|
| Lokalni docker-compose | nginx kontejner | mkcert ili openssl |
| kind (lokalni K8s) | nginx-ingress controller | cert-manager self-signed ClusterIssuer |
| AWS dev/staging | AWS ALB | ACM managed |
| AWS prod | AWS ALB | ACM managed, auto-renewal |

App kontejner je uvijek isti. Mijenja se samo ko stoji ispred njega i odakle dolazi certifikat.
