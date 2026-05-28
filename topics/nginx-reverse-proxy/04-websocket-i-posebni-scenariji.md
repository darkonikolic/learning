# Nginx Reverse Proxy — WebSocket i posebni scenariji

## WebSocket proxy

WebSocket zahteva upgrade protokola sa HTTP na WS. Nginx mora da prosleđuje `Upgrade` i `Connection` headere.

```
Browser → [HTTP Upgrade Request] → Nginx → Backend
       ← [101 Switching Protocols] ←      ←
       ← [WebSocket frames] ←             ←
```

```nginx
http {
    # map direktiva dinamički postavlja Connection header
    map $http_upgrade $connection_upgrade {
        default  upgrade;   # ako klijent traži upgrade → prosleđuj upgrade
        ''       close;     # ako ne traži upgrade → zatvori
    }

    server {
        listen 80;
        server_name ws.example.com;

        location /ws/ {
            proxy_pass  http://127.0.0.1:3000;

            proxy_http_version  1.1;
            proxy_set_header    Upgrade    $http_upgrade;
            proxy_set_header    Connection $connection_upgrade;
            proxy_set_header    Host       $host;

            proxy_read_timeout  3600s;   # WebSocket konekcija može trajati satima
            proxy_send_timeout  3600s;
        }

        # Ostale putanje — normalan proxy
        location / {
            proxy_pass  http://127.0.0.1:3000;
            proxy_set_header  Host              $host;
            proxy_set_header  X-Real-IP         $remote_addr;
            proxy_set_header  X-Forwarded-Proto $scheme;
        }
    }
}
```

## Proxy ka HTTPS backend-u

Kada backend takođe koristi SSL (end-to-end encryption):

```nginx
server {
    listen 443 ssl http2;
    server_name app.example.com;

    location / {
        proxy_pass  https://10.0.0.1:443;   # HTTPS ka backend-u

        proxy_ssl_verify        on;
        proxy_ssl_trusted_certificate /etc/nginx/certs/internal-ca.crt;
        proxy_ssl_server_name   on;         # SNI za backend
        proxy_ssl_name          internal-backend.local;

        proxy_set_header  Host              $host;
        proxy_set_header  X-Forwarded-Proto $scheme;
    }
}
```

## Proxy cache

```nginx
http {
    proxy_cache_path  /var/cache/nginx
                      levels=1:2
                      keys_zone=site_cache:10m
                      max_size=1g
                      inactive=60m
                      use_temp_path=off;

    server {
        location / {
            proxy_pass   http://127.0.0.1:3000;
            proxy_cache  site_cache;

            proxy_cache_valid  200 301  10m;
            proxy_cache_valid  404      1m;

            # Preskoči cache: za ulogovane korisnike ili POST zahteve
            proxy_cache_bypass  $cookie_session  $request_method;
            proxy_no_cache      $cookie_session  $request_method;

            # Header koji pokazuje cache status
            add_header  X-Cache-Status  $upstream_cache_status;

            # Ako backend nije dostupan, koristi stari keš (grace period)
            proxy_cache_use_stale  error timeout updating;
        }
    }
}
```

## Više aplikacija po domenu

```nginx
# Node.js REST API
server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:3000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }
}

# Django admin
server {
    listen 443 ssl http2;
    server_name admin.example.com;

    ssl_certificate     /etc/letsencrypt/live/admin.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/admin.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    # Django statički fajlovi direktno sa diska
    location /static/ {
        alias /var/www/django/static/;
        expires 1y;
    }
}

# Grafana — sa WebSocket podrškom
server {
    listen 443 ssl http2;
    server_name monitoring.example.com;

    ssl_certificate     /etc/letsencrypt/live/monitoring.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitoring.example.com/privkey.pem;

    location / {
        proxy_pass         http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host       $host;
    }
}
```

## Više aplikacija po putanji (sub-path)

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # Frontend React app
    location / {
        proxy_pass  http://127.0.0.1:3000;
    }

    # REST API — /api/ putanja uklonjena pre prosleđivanja
    location /api/ {
        proxy_pass  http://127.0.0.1:8000/;  # trailing "/" kloni /api/ prefix
        # /api/users → backend prima /users
        proxy_set_header  Host              $host;
        proxy_set_header  X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /socket.io/ {
        proxy_pass         http://127.0.0.1:3002;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade    $http_upgrade;
        proxy_set_header   Connection "upgrade";
    }
}
```

**Pravilo za trailing slash:**
- `proxy_pass http://backend` — Nginx prosleđuje celu putanju uključujući `/api/`
- `proxy_pass http://backend/` — Nginx uklanja deo koji matchuje location, šalje ostatak

## Proxy sa Basic Auth zaštitom

```bash
# Generiši korisnika
sudo apt install apache2-utils
htpasswd -c /etc/nginx/.htpasswd admin
```

```nginx
server {
    listen 443 ssl http2;
    server_name protected.example.com;

    location / {
        auth_basic           "Unesite korisnicko ime i lozinku";
        auth_basic_user_file /etc/nginx/.htpasswd;

        proxy_pass  http://127.0.0.1:3000;

        # Ne prosleđuj Basic Auth header backend-u
        proxy_set_header  Authorization  "";
    }
}
```
