# Nginx — Server i Location blok

## Server blok (virtuelni host)

Svaki `server {}` blok definiše jedan virtuelni host.

```nginx
server {
    listen       80;                          # port IPv4
    listen  [::]:80;                          # port IPv6
    server_name  example.com www.example.com; # domen(i)

    root   /var/www/example.com/html;         # web root
    index  index.html index.htm;              # defaultni fajlovi

    access_log  /var/log/nginx/example.access.log  main;
    error_log   /var/log/nginx/example.error.log   warn;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

## Kako Nginx bira server blok?

1. Po IP:portu (`listen` direktiva)
2. Po `server_name` — prioritet: tačno, wildcard levo, wildcard desno, regex
3. Ako ništa ne matchuje → `default_server`

```nginx
# Default za sve zahteve koji ne matchuju nijedan sajt
server {
    listen 80 default_server;
    server_name _;      # "_" je konvencija za "bilo koji domen"
    return 444;         # zatvori konekciju (Nginx-specifičan kod)
}
```

## Location blok — prioriteti poklapanja

| Sintaksa | Tip | Prioritet |
|----------|-----|-----------|
| `location = /putanja` | Exact match | Najviši |
| `location ^~ /putanja` | Prefix, blokira regex | Drugi |
| `location ~ regex` | Regex, case-sensitive | Treći |
| `location ~* regex` | Regex, case-insensitive | Treći |
| `location /putanja` | Prefix (najduži wins) | Najniži |

```nginx
server {
    # Tačno "/" — samo root
    location = / {
        return 200 "Pocetna\n";
    }

    # Prefix match koji blokira regex pretragu
    location ^~ /static/ {
        root /var/www;
        expires 30d;
    }

    # PHP fajlovi — case-sensitive regex
    location ~ \.php$ {
        fastcgi_pass unix:/run/php/php8.1-fpm.sock;
        fastcgi_index index.php;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
    }

    # Slike — case-insensitive regex
    location ~* \.(jpg|jpeg|png|gif|ico|svg|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Sve ostalo — prefix "/" je najniži prioritet
    location / {
        try_files $uri $uri/ /index.html;  # SPA fallback
    }
}
```

## try_files — logika pronalaska fajla

```nginx
location / {
    # Pokušaj redom: fajl → direktorijum → fallback
    try_files $uri $uri/ =404;
    #          │    │     └── ako ništa nije nađeno, vrati 404
    #          │    └──────── pokušaj kao direktorijum (/index.html)
    #          └───────────── pokušaj kao fajl
}

# Za SPA (React, Vue, Angular)
location / {
    try_files $uri $uri/ /index.html;
    # Sve što nije fajl → vrati index.html (router u browseru)
}

# Za PHP
location / {
    try_files $uri $uri/ /index.php?$query_string;
}
```

## return i rewrite

```nginx
# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

# Redirect www → non-www
server {
    server_name www.example.com;
    return 301 https://example.com$request_uri;
}

# Rewrite URL (interno, bez redirecta)
location /stara-putanja/ {
    rewrite ^/stara-putanja/(.*)$ /nova-putanja/$1 last;
}

# Rewrite sa redirectom ka klijentu
location /blog {
    rewrite ^/blog$ /novosti permanent;  # 301
}
```

## root vs alias

```nginx
# root: putanja = root + location
location /slike/ {
    root /var/www;
    # zahtev /slike/foto.jpg → /var/www/slike/foto.jpg
}

# alias: putanja = alias (location se zamenjuje)
location /slike/ {
    alias /var/www/media/fotografije/;
    # zahtev /slike/foto.jpg → /var/www/media/fotografije/foto.jpg
}
```

## Praktičan primer — statički sajt

```nginx
server {
    listen 80;
    server_name mojsajt.com www.mojsajt.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mojsajt.com www.mojsajt.com;

    ssl_certificate     /etc/letsencrypt/live/mojsajt.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mojsajt.com/privkey.pem;

    root  /var/www/mojsajt.com;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \.(css|js|png|jpg|webp|svg|ico|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # Zabrani pristup skrivenim fajlovima
    location ~ /\. {
        deny all;
    }
}
```
