# Nginx — Gzip, Caching i Rate Limiting

## Gzip kompresija

Nginx kompresuje odgovore pre slanja klijentu — smanjuje veličinu i ubrzava učitavanje.

```nginx
http {
    gzip  on;
    gzip_vary         on;      # dodaje "Vary: Accept-Encoding" header
    gzip_proxied      any;     # kompresuj i za proxy zahteve
    gzip_comp_level   6;       # 1 (najbrže) do 9 (najmanji fajl) — 6 je balans
    gzip_min_length   1000;    # kompresuj samo fajlove veće od 1KB
    gzip_buffers      16 8k;
    gzip_http_version 1.1;

    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/xml
        application/rss+xml
        image/svg+xml
        font/woff2
        font/woff;

    # image/jpeg, image/png, image/gif se NE stavljaju — već su kompresovani
}
```

### Provjera gzip-a

```bash
curl -H "Accept-Encoding: gzip" -I https://example.com
# Tražiti: Content-Encoding: gzip
```

---

## Browser cache (expires direktiva)

Govori browseru koliko dugo sme da kešira fajl lokalno.

```nginx
server {
    # Statički assets — dugi cache (koristiti content hashing u imenima fajlova)
    location ~* \.(css|js|woff2|woff|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Slike
    location ~* \.(jpg|jpeg|png|gif|ico|svg|webp)$ {
        expires 6M;
        add_header Cache-Control "public";
    }

    # HTML — kraći cache jer se sadržaj menja
    location ~* \.html$ {
        expires 1h;
        add_header Cache-Control "public, must-revalidate";
    }

    # API — bez cache-a
    location /api/ {
        add_header Cache-Control "no-store, no-cache, must-revalidate, private";
        expires -1;
    }
}
```

---

## Nginx proxy cache

Nginx čuva odgovore backend-a na disku — backend ne mora da odgovori za svaki zahtev.

```nginx
http {
    # Definiši cache zonu
    proxy_cache_path  /var/cache/nginx
                      levels=1:2               # hijerarhija direktorijuma
                      keys_zone=app_cache:10m  # 10MB za ključeve u RAM-u
                      max_size=1g              # max veličina cache na disku
                      inactive=60m             # briši ako nije korišten 60 min
                      use_temp_path=off;

    server {
        location / {
            proxy_pass   http://127.0.0.1:3000;
            proxy_cache  app_cache;

            proxy_cache_valid  200 301  10m;  # kešira uspešne odgovore 10 min
            proxy_cache_valid  404      1m;   # kešira 404 odgovore 1 min

            # Header koji pokazuje da li je cache hit ili miss
            add_header  X-Cache-Status  $upstream_cache_status;

            # Ne kešira za ulogovane korisnike (sa session cookie)
            proxy_cache_bypass  $cookie_session;
            proxy_no_cache      $cookie_session;
        }
    }
}
```

Vrednosti `$upstream_cache_status`: `HIT`, `MISS`, `BYPASS`, `EXPIRED`, `STALE`

---

## Rate Limiting — ograničavanje broja zahteva

Štiti od brute-force napada, scraperа i preopterećenja.

```nginx
http {
    # Definiši zone (u http bloku)
    limit_req_zone  $binary_remote_addr  zone=global:10m    rate=100r/s;
    limit_req_zone  $binary_remote_addr  zone=api:10m       rate=30r/s;
    limit_req_zone  $binary_remote_addr  zone=login:10m     rate=5r/m;

    server {
        # Globalni limit za sve zahteve
        limit_req  zone=global  burst=200  nodelay;

        # API endpoint
        location /api/ {
            limit_req        zone=api  burst=50  nodelay;
            limit_req_status 429;         # HTTP 429 Too Many Requests
            proxy_pass http://127.0.0.1:3000;
        }

        # Login — strogo ograničenje za brute-force zaštitu
        location /api/auth/login {
            limit_req        zone=login  burst=3;
            limit_req_status 429;

            # Opciono: dodaj Retry-After header
            limit_req_log_level  warn;
            proxy_pass http://127.0.0.1:3000;
        }
    }
}
```

### burst i nodelay

- `burst=20` — dozvoli kratki nalet do 20 zahteva iznad rate limite
- `nodelay` — obradi burst odmah (bez čekanja), ali prekrši gornji limit → 429
- Bez `nodelay` — zahtevi čekaju u redu (usporava, ali ne odbija)

---

## Ograničavanje konekcija

```nginx
http {
    # Max simultanih konekcija po IP-u
    limit_conn_zone  $binary_remote_addr  zone=conn_limit:10m;

    server {
        limit_conn  conn_limit  20;    # max 20 istovremenih konekcija po IP

        location /download/ {
            limit_conn  conn_limit  5;  # max 5 za download endpoint
            limit_rate  500k;           # max 500KB/s po konekciji
        }
    }
}
```

---

## Primer — produkcijski server sa svim funkcijama

```nginx
http {
    gzip on;
    gzip_types text/plain text/css application/javascript application/json image/svg+xml;
    gzip_comp_level 6;
    gzip_min_length 1000;

    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=main:20m max_size=2g inactive=60m;

    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_conn_zone $binary_remote_addr zone=conn:10m;

    server {
        listen 443 ssl http2;
        server_name api.example.com;

        ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;
        ssl_protocols       TLSv1.2 TLSv1.3;

        limit_conn conn 50;

        location / {
            limit_req  zone=api  burst=60  nodelay;
            limit_req_status 429;

            proxy_pass  http://127.0.0.1:3000;
            proxy_cache main;
            proxy_cache_valid 200 5m;
            add_header X-Cache-Status $upstream_cache_status;

            proxy_set_header Host              $host;
            proxy_set_header X-Real-IP         $remote_addr;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location ~* \.(css|js|png|jpg|webp|svg|woff2)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            access_log off;
        }
    }
}
```
