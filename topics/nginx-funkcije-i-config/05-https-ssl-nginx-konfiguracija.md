# Nginx — HTTPS i SSL konfiguracija

## SSL terminacija

Nginx prima šifrovane HTTPS zahteve od klijenta, dešifruje ih, i prosleđuje backend-u kao plain HTTP.

```
Browser ──[HTTPS/TLS]──► Nginx ──[HTTP]──► App :3000
```

## Osnovna HTTPS konfiguracija

```nginx
# HTTP → HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate      /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key  /etc/letsencrypt/live/example.com/privkey.pem;

    root  /var/www/example.com;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

## Bezbedni SSL parametri

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Dozvoli samo moderne protokole (isključi SSLv3, TLS 1.0, TLS 1.1)
    ssl_protocols  TLSv1.2 TLSv1.3;

    # Moderne cipher suite
    ssl_ciphers  ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:
                 ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:
                 ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_prefer_server_ciphers  off;  # TLS 1.3 sam bira

    # Session cache — ubrzava reconnect
    ssl_session_cache    shared:SSL:10m;
    ssl_session_timeout  1d;
    ssl_session_tickets  off;  # forward secrecy

    # OCSP Stapling — brža validacija sertifikata (server preuzima status, ne browser)
    ssl_stapling         on;
    ssl_stapling_verify  on;
    ssl_trusted_certificate /etc/letsencrypt/live/example.com/chain.pem;
    resolver  1.1.1.1 8.8.8.8  valid=300s;
    resolver_timeout  5s;

    # Diffie-Hellman parametri (za PFS)
    ssl_dhparam /etc/nginx/dhparam.pem;
}
```

```bash
# Generiši DH parametre (jednom, traje duže)
sudo openssl dhparam -out /etc/nginx/dhparam.pem 2048
```

## Security headeri

```nginx
server {
    # HSTS — browser uvek koristi HTTPS (min 1 godina)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # Zaštita od clickjacking-a
    add_header X-Frame-Options "SAMEORIGIN" always;

    # Browser ne sme da "genji" MIME tip
    add_header X-Content-Type-Options "nosniff" always;

    # XSS Protection (stariji browseri)
    add_header X-XSS-Protection "1; mode=block" always;

    # Referrer — ne šalji puni URL na cross-origin zahteve
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Content Security Policy
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'" always;
}
```

## Self-signed sertifikat (za razvoj/testiranje)

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=RS/ST=Serbia/L=Beograd/O=Dev/CN=localhost"
```

```nginx
server {
    listen 443 ssl;
    server_name localhost;

    ssl_certificate     /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;
    ...
}
```

## Više domena na jednoj IP (SNI)

SNI (Server Name Indication) omogućava više SSL sertifikata na jednoj IP adresi — browser šalje domen pre TLS handshake-a.

```nginx
server {
    listen 443 ssl http2;
    server_name site1.com;
    ssl_certificate /etc/letsencrypt/live/site1.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/site1.com/privkey.pem;
    root /var/www/site1;
}

server {
    listen 443 ssl http2;
    server_name site2.com;
    ssl_certificate /etc/letsencrypt/live/site2.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/site2.com/privkey.pem;
    root /var/www/site2;
}
```

## Wildcard sertifikat

```bash
# Let's Encrypt wildcard (zahteva DNS challenge)
sudo certbot certonly --manual --preferred-challenges dns \
    -d "*.example.com" -d "example.com"
```

```nginx
ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
# Pokriva: example.com, www.example.com, api.example.com, admin.example.com...
```

## Testiranje SSL konfiguracije

```bash
# Lokalni test
openssl s_client -connect example.com:443 -servername example.com

# Provjeri koji protokoli su podržani
nmap --script ssl-enum-ciphers -p 443 example.com

# Online alat: https://www.ssllabs.com/ssltest/
```
