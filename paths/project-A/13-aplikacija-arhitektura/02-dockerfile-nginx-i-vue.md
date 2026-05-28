# 02 — Dockerfile: nginx i Vue.js

## Arhitekturalna odluka: Vue u ISTI nginx image

Vue.js build artefakt (statični HTML/CSS/JS) ide u isti nginx image koji radi kao reverse proxy. Alternativa je zasebni "static files" kontejner kojeg nginx poziva kao upstream — to je nepotreban network hop za statični sadržaj.

Prednosti objedinjenog pristupa:
- nginx servira fajlove direktno iz filesystema, nema network-a
- Jedan Deployment u K8s-u, jedan image tag za release
- Nema potrebe za shared volume između dva kontejnera

Jedini razlog za odvajanje bi bio ako statični sadržaj treba CDN edge caching (Cloudflare, CloudFront) — tada se Vue build uploaduje direktno na CDN, a nginx se uopće ne koristi za statiku.

---

## Vue.js multi-stage Dockerfile

```dockerfile
# ---- Build stage ----
FROM node:20-alpine AS builder

WORKDIR /app

# Kopiraj package fajlove prvo — Docker cache layer optimizacija
# npm install se rerunuje samo ako se package.json promijeni
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

# Kopiraj source i buildi
COPY . .
RUN npm run build
# Output: /app/dist/

# ---- Runtime stage ----
FROM nginx:1.25-alpine

# Ukloni default nginx konfiguraciju
RUN rm /etc/nginx/conf.d/default.conf

# Kopiraj custom konfiguraciju
COPY nginx.conf /etc/nginx/nginx.conf

# Kopiraj Vue build artefakt
COPY --from=builder /app/dist /usr/share/nginx/html

# nginx radi na portu 80 (HTTP) i 443 (HTTPS u produkciji)
EXPOSE 80

# nginx:alpine ima non-root user opciju, ali standardno radi kao root
# Za produkciju razmotriti rootless nginx pattern
CMD ["nginx", "-g", "daemon off;"]
```

`npm ci` umjesto `npm install`: `ci` koristi `package-lock.json` tačno kako je snimljen, bez resolving verzija. Reproducibilni build je neophodan za produkciju.

---

## nginx.conf — potpuna konfiguracija

```nginx
user nginx;
worker_processes auto;  # Broj CPU core-ova
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;  # Linux event model, bolje od select
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Log format sa request timing
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" rt=$request_time';

    access_log /var/log/nginx/access.log main;

    # Performansne optimizacije
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    client_max_body_size 10m;

    # Gzip kompresija
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/xml
        image/svg+xml;

    # Upstream: PHP-FPM servis
    # U Docker Compose: "php-service" je ime kontejnera
    # U K8s: "php-service.namespace.svc.cluster.local"
    upstream php_fpm {
        server php-service:9000;
        keepalive 16;  # Persistent konekcije na PHP-FPM pool
    }

    server {
        listen 80;
        server_name _;
        root /usr/share/nginx/html;
        index index.html;

        # Security headers — dodati na svaki response
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        # CSP treba biti prilagođen aplikaciji — ovo je minimalni primjer
        # add_header Content-Security-Policy "default-src 'self'" always;

        # API requests → PHP-FPM proxy
        location /api/ {
            # FastCGI proxy na PHP-FPM
            fastcgi_pass php_fpm;
            fastcgi_index index.php;
            fastcgi_param SCRIPT_FILENAME /var/www/html/public/index.php;
            include fastcgi_params;

            # Timeout za duže operacije (upload, report generisanje)
            fastcgi_read_timeout 30s;
            fastcgi_connect_timeout 5s;

            # Buffer settings za PHP response
            fastcgi_buffer_size 128k;
            fastcgi_buffers 4 256k;
        }

        # Health check endpoint — ne loguj da ne zagušiš log fajlove
        location /nginx-health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Statični assets sa hashovanim imenima (Vue Vite output: app.abc123.js)
        # Dugi cache TTL je siguran jer se ime fajla mijenja sa sadržajem
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }

        # index.html — NIKAD ne keširati, mora biti svjež
        # Browser mora uvijek dobiti najnoviji za nove hash-ove asseta
        location = /index.html {
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            expires 0;
        }

        # SPA fallback — sve ostale rute vraćaju index.html
        # Vue Router handles routing na klientu
        location / {
            try_files $uri $uri/ /index.html;
        }
    }
}
```

---

## Cache strategija za assete

Ovo je production-kritičan detalj koji se često pogrešno radi.

**Hashirani asseti** (`app.a1b2c3.js`, `style.x9y8z7.css`): Vite automatski generira hashirano ime na osnovu sadržaja fajla. Ako se sadržaj nije promijenio, hash je isti. Može se cachirati na godinu dana (`immutable` znači "nikad ponovo provjeravaj").

**index.html**: Ovaj fajl referencira hashirana imena. Mora biti `no-cache` — browser mora uvijek dobiti svježu verziju da bi znao koji hashirani asset učitati. Ako se index.html kešira, korisnik može dobiti stari index koji referencira nepostojeće (promijenjene) asset fajlove.

Greška: keširati index.html s dugim TTL-om. Rezultat: korisnici dobijaju stare bundle-ove, app se "lomi" jer `app.oldHash.js` ne postoji više na serveru.

---

## .dockerignore za Vue projekat

```
node_modules/
dist/
.git/
.gitignore
.env
.env.*
*.log
.DS_Store
coverage/
.nyc_output/
.vite/
README.md
```

`node_modules` je najvažniji. Bez `.dockerignore`, Docker context kopira `node_modules` u build context (može biti 500MB+) i to ubija build performance. `npm ci` instalira zavisnosti unutar kontejnera, tako da lokalni `node_modules` nije potreban.

`.env` fajlovi ne smiju ući u image — čak ni u build stage. Environment varijable se prosljeđuju kao build arguments za Vite:

```dockerfile
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build
```

U produkciji, API URL koji Vue.js koristi treba biti relativan (`/api/`) da bi radio na bilo kojem domenu — apsolutni URL koji se "bake-a" u build je anti-pattern za multi-environment deployment.
