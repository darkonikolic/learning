# Nginx — Struktura konfiguracije

## Raspored fajlova

```
/etc/nginx/
├── nginx.conf                  ← glavni config (entry point)
├── conf.d/                     ← site konfiguracije (CentOS stil)
│   └── default.conf
├── sites-available/            ← svi sajtovi (Debian/Ubuntu stil)
│   ├── example.com
│   └── another.com
├── sites-enabled/              ← symlinks ka aktivnim sajtovima
│   └── example.com -> ../sites-available/example.com
├── snippets/                   ← delovi config-a za reuse
│   ├── fastcgi-php.conf
│   └── ssl-params.conf
└── mime.types                  ← mapiranje ekstenzija na MIME tipove
```

## Hijerarhija blokova

Nginx konfiguracija je hijerarhijska — direktive nasledjuju vrednosti od roditeljskih blokova.

```
main (globalni nivo)
  ├── events { }
  └── http { }
        └── server { }          ← jedan virtuelni host
              └── location { }  ← pravila za URL putanje
```

## nginx.conf — struktura

```nginx
# ── MAIN blok ─────────────────────────────────────────────────
user  nginx;
worker_processes  auto;            # jedan worker po CPU jezgru
error_log  /var/log/nginx/error.log  warn;
pid  /run/nginx.pid;

# ── EVENTS blok ───────────────────────────────────────────────
events {
    worker_connections  1024;      # max konekcija po workeru
    use  epoll;                    # Linux event model (najbrži)
    multi_accept  on;              # prihvati više konekcija odjednom
}

# ── HTTP blok ─────────────────────────────────────────────────
http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    log_format  main  '$remote_addr - $remote_user [$time_local] '
                      '"$request" $status $body_bytes_sent '
                      '"$http_referer" "$http_user_agent"';

    access_log  /var/log/nginx/access.log  main;

    sendfile    on;    # OS sendfile() — brži transfer fajlova
    tcp_nopush  on;    # šalje header i početak fajla zajedno
    tcp_nodelay on;    # smanjuje latenciju za keep-alive

    keepalive_timeout  65;

    gzip  on;

    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}
```

## Aktivacija sajta (Debian/Ubuntu stil)

```bash
# Kreira symlink koji "aktivira" sajt
sudo ln -s /etc/nginx/sites-available/example.com \
           /etc/nginx/sites-enabled/example.com

# Test i reload
sudo nginx -t && sudo systemctl reload nginx

# Deaktivacija
sudo rm /etc/nginx/sites-enabled/example.com
sudo systemctl reload nginx
```

## Bitne globalne direktive

```nginx
# Maksimalna veličina upload fajla (default: 1M)
client_max_body_size  50M;

# Timeout za čitanje request body
client_body_timeout  30s;

# Timeout za slanje response klijentu
send_timeout  30s;

# Broj keep-alive zahteva po konekciji
keepalive_requests  1000;

# Veličina hash tabele za server_name
server_names_hash_bucket_size  64;
```

## Nasledjivanje i override direktiva

Direktive se nasledjuju od roditeljskog bloka, ali ih dete može override-ovati:

```nginx
http {
    gzip  on;             # važi za sve server blokove

    server {
        gzip  off;        # override samo za ovaj server

        location /api/ {
            gzip  on;     # override nazad za ovu putanju
        }
    }
}
```

## Promenljive koje Nginx uvek ima

| Promenljiva | Sadržaj |
|-------------|---------|
| `$host` | Host header (domen) |
| `$request_uri` | URI + query string |
| `$uri` | URI bez query stringa |
| `$args` | Query string |
| `$remote_addr` | IP adresa klijenta |
| `$scheme` | `http` ili `https` |
| `$server_name` | Matchovani server_name |
| `$http_user_agent` | User-Agent header klijenta |
| `$status` | HTTP status kod odgovora |
| `$body_bytes_sent` | Broj bajtova u response body |
| `$request_time` | Vreme obrade zahteva (sekunde) |
| `$binary_remote_addr` | IP u binarnom obliku (za rate limit zone) |
