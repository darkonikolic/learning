# Nginx Reverse Proxy — Upstream i Load Balancing

## Upstream blok

`upstream` definiše grupu backend servera kojoj Nginx prosleđuje zahteve.

```nginx
http {
    upstream ime_grupe {
        server 127.0.0.1:3000;
        server 127.0.0.1:3001;
        server 127.0.0.1:3002;
    }

    server {
        listen 80;
        location / {
            proxy_pass http://ime_grupe;  # koristi upstream grupu
        }
    }
}
```

## Algoritmi load balancinga

### Round Robin (default)

Redom šalje zahteve na svaki server — svaki dobija isti broj zahteva.

```nginx
upstream backend {
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
    # Zahtev 1 → server1, zahtev 2 → server2, zahtev 3 → server3, zahtev 4 → server1...
}
```

### Weighted Round Robin

Server sa većim weight-om dobija proporcionalno više zahteva.

```nginx
upstream backend {
    server 10.0.0.1:3000 weight=1;  # dobija ~20% zahteva
    server 10.0.0.2:3000 weight=1;  # dobija ~20% zahteva
    server 10.0.0.3:3000 weight=3;  # dobija ~60% zahteva (moćniji server)
}
```

### Least Connections

Šalje zahtev serveru koji ima najmanje aktivnih konekcija.

```nginx
upstream backend {
    least_conn;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
    # Dobar za zahteve različitog trajanja (npr. file upload + brzi API)
}
```

### IP Hash

Isti klijent (po IP adresi) uvek ide na isti server — "sticky sessions".

```nginx
upstream backend {
    ip_hash;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    # Korisno kada aplikacija čuva session u memoriji servera
}
```

## Failover i health check parametri

```nginx
upstream backend {
    server 10.0.0.1:3000  max_fails=3  fail_timeout=30s;
    # Ako server ima 3 greške unutar 30s → isključi ga na 30s

    server 10.0.0.2:3000  max_fails=3  fail_timeout=30s;

    server 10.0.0.3:3000  backup;
    # Backup server — koristi se SAMO ako su ostali nedostupni

    server 10.0.0.4:3000  down;
    # Trajno isključen (maintenance mod)

    keepalive  32;
    # Održavaj 32 keep-alive konekcije ka svakom serveru (connection pooling)
}
```

### Kako Nginx detektuje pad servera?

Pasivni health check (default):
- Nginx šalje zahtev
- Ako dobije grešku konekcije ili timeout → `max_fails` counter++
- Kada dostigne `max_fails` → server označen kao nezdrav na `fail_timeout` sekundi
- Posle `fail_timeout` → Nginx proba ponovo

Aktivni health check je dostupan u Nginx Plus (komercijalna verzija).

## Unix socket kao upstream

Brži od TCP/IP za lokalne konekcije (nema network stack overhead).

```nginx
upstream php_fpm {
    server unix:/run/php/php8.1-fpm.sock;
}

upstream gunicorn {
    server unix:/run/gunicorn.sock;
}

server {
    location ~ \.php$ {
        fastcgi_pass php_fpm;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }
}
```

## Routing po putanji na različite upstream grupe

```nginx
upstream api_servers {
    least_conn;
    server 10.0.1.1:3000;
    server 10.0.1.2:3000;
}

upstream static_servers {
    server 10.0.2.1:80;
    server 10.0.2.2:80;
}

upstream legacy_app {
    server 10.0.3.1:8080;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    location /api/ {
        proxy_pass http://api_servers;
    }

    location /static/ {
        proxy_pass http://static_servers;
    }

    location /stari-modul/ {
        proxy_pass http://legacy_app;
    }
}
```

## Primer — Node.js klaster sa load balancingom

```bash
# Pokrni 3 instance Node.js aplikacije na različitim portovima
node app.js --port 3000 &
node app.js --port 3001 &
node app.js --port 3002 &
```

```nginx
upstream nodejs_cluster {
    least_conn;

    server 127.0.0.1:3000  max_fails=3  fail_timeout=30s;
    server 127.0.0.1:3001  max_fails=3  fail_timeout=30s;
    server 127.0.0.1:3002  max_fails=3  fail_timeout=30s;

    keepalive 16;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate     /etc/letsencrypt/live/api.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.example.com/privkey.pem;

    location / {
        proxy_pass         http://nodejs_cluster;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Connection        "";  # keepalive, ne upgrade

        proxy_connect_timeout  5s;
        proxy_read_timeout     30s;
    }
}
```
