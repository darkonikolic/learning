# Nginx Reverse Proxy — Produkciona konfiguracija

## Kompletna produkciona konfiguracija za REST API

```nginx
# /etc/nginx/sites-available/api.mojapp.com

upstream nodejs_api {
    least_conn;
    server 127.0.0.1:3000  max_fails=3  fail_timeout=30s;
    server 127.0.0.1:3001  max_fails=3  fail_timeout=30s;
    server 127.0.0.1:3002  backup;
    keepalive 16;
}

# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name api.mojapp.com;
    return 301 https://$host$request_uri;
}

# Glavni HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.mojapp.com;

    # SSL
    ssl_certificate     /etc/letsencrypt/live/api.mojapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.mojapp.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headeri
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options           "DENY" always;
    add_header X-Content-Type-Options    "nosniff" always;
    add_header Referrer-Policy           "strict-origin-when-cross-origin" always;

    # Logovi
    access_log /var/log/nginx/api.mojapp.com.access.log main;
    error_log  /var/log/nginx/api.mojapp.com.error.log  warn;

    # Upload limit
    client_max_body_size 10M;

    # Rate limiting zone (definisano u http bloku)
    limit_req_zone $binary_remote_addr zone=api_zone:10m rate=30r/s;

    location / {
        limit_req        zone=api_zone  burst=50  nodelay;
        limit_req_status 429;

        proxy_pass         http://nodejs_api;
        proxy_http_version 1.1;

        proxy_set_header  Host               $host;
        proxy_set_header  X-Real-IP          $remote_addr;
        proxy_set_header  X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header  X-Forwarded-Proto  $scheme;
        proxy_set_header  Connection         "";

        proxy_connect_timeout  5s;
        proxy_send_timeout     30s;
        proxy_read_timeout     30s;

        proxy_buffering  on;
    }

    # Zabrani pristup skrivenim fajlovima
    location ~ /\. {
        deny all;
        return 404;
    }
}
```

## Kompletna konfiguracija za web aplikaciju sa statičkim fajlovima

```nginx
# /etc/nginx/sites-available/mojapp.com

upstream django_app {
    server unix:/run/gunicorn/mojapp.sock  max_fails=3  fail_timeout=30s;
    keepalive 4;
}

server {
    listen 80;
    listen [::]:80;
    server_name mojapp.com www.mojapp.com;
    return 301 https://mojapp.com$request_uri;
}

# www → non-www redirect
server {
    listen 443 ssl http2;
    server_name www.mojapp.com;
    ssl_certificate     /etc/letsencrypt/live/mojapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mojapp.com/privkey.pem;
    return 301 https://mojapp.com$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name mojapp.com;

    ssl_certificate     /etc/letsencrypt/live/mojapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mojapp.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;

    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options    "nosniff" always;
    add_header X-Frame-Options           "SAMEORIGIN" always;

    access_log /var/log/nginx/mojapp.access.log main;
    error_log  /var/log/nginx/mojapp.error.log  warn;

    client_max_body_size 25M;

    # Django statički fajlovi — direktno sa diska, bez backend-a
    location /static/ {
        alias /var/www/mojapp/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Korisnički upload fajlovi
    location /media/ {
        alias /var/www/mojapp/media/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
    }

    # Sve ostalo → Django
    location / {
        proxy_pass         http://django_app;
        proxy_http_version 1.1;

        proxy_set_header  Host               $host;
        proxy_set_header  X-Real-IP          $remote_addr;
        proxy_set_header  X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header  X-Forwarded-Proto  $scheme;
        proxy_set_header  Connection         "";

        proxy_connect_timeout  5s;
        proxy_read_timeout     60s;
    }

    location ~ /\. {
        deny all;
    }
}
```

## Dijagnostika proxy konekcije

```bash
# Provjeri da li backend uopšte odgovara
curl -v http://127.0.0.1:3000/health

# Testiraj kroz Nginx sa detaljima
curl -v -H "Host: api.mojapp.com" http://127.0.0.1/

# Provjeri upstream konekcije
ss -tn | grep ':3000'

# Prati 502/503 greške u logu
sudo tail -f /var/log/nginx/error.log | grep -E "upstream|connect"

# Provjeri cache status
curl -I https://api.mojapp.com/ | grep X-Cache

# Simuliraj 429 (rate limit test)
for i in $(seq 1 60); do curl -s -o /dev/null -w "%{http_code}\n" https://api.mojapp.com/; done
```

## Česte greške u reverse proxy konfiguraciji

| Greška | Uzrok | Rešenje |
|--------|-------|---------|
| `502 Bad Gateway` | Backend ne radi ili pogrešan port | `curl http://127.0.0.1:3000` direktno |
| `504 Gateway Timeout` | Backend spor, `proxy_read_timeout` premali | Povećaj `proxy_read_timeout` |
| Redirect loop | Backend redirectuje na HTTP, Nginx na HTTPS | Postavi `X-Forwarded-Proto`, provjeri app config |
| CSS/JS 404 | Pogrešan `proxy_pass` trailing slash | Provjeri trailing slash pravilo |
| WebSocket 400 | Nedostaju Upgrade headeri | Dodaj `Upgrade` i `Connection` headere |
| Session gubi se | Load balancer bez sticky sessions | Koristi `ip_hash` ili Redis za session store |
