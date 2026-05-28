# Nginx Reverse Proxy — Osnovna konfiguracija i headeri

## Minimalna konfiguracija

```nginx
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
    }
}
```

Ovo radi, ali backend ne zna pravi IP klijenta, protokol, ni originalni domen.

## Proxy headeri — kompletna konfiguracija

```nginx
server {
    listen 80;
    server_name app.example.com;

    location / {
        proxy_pass  http://127.0.0.1:3000;

        # Originalni Host header (ne "localhost" ili IP)
        proxy_set_header  Host               $host;

        # Pravi IP klijenta (ne Nginx IP)
        proxy_set_header  X-Real-IP          $remote_addr;

        # Lanac proksija — lista svih IP-ova
        proxy_set_header  X-Forwarded-For    $proxy_add_x_forwarded_for;

        # Originalni protokol — "http" ili "https"
        proxy_set_header  X-Forwarded-Proto  $scheme;

        # HTTP/1.1 za keep-alive konekcije
        proxy_http_version  1.1;
        proxy_set_header    Connection  "";   # resetuj za keepalive (ne "upgrade")
    }
}
```

## Zašto su ovi headeri važni?

Backend aplikacija mora znati ko je stvarno poslao zahtev:

```
Klijent (1.2.3.4) → Nginx (10.0.0.1) → Backend

Backend vidi konekciju sa 10.0.0.1 (Nginx IP).
Bez X-Real-IP: backend misli da je korisnik 10.0.0.1.
Sa X-Real-IP: 1.2.3.4 → backend zna pravog korisnika.
```

Primeri gde je ovo kritično:
- **Logovi** — ko je stvarno posetio sajt
- **Rate limiting** u aplikaciji — ograniči po pravom IP-u
- **Geo-blokiranje** — korisnikova lokacija
- **Fraud detection** — prepoznavanje sumnjivih IP-ova
- **SSL redirect** — aplikacija zna da je zahtev stigao preko HTTPS

## Čitanje proxy headera u backend aplikacijama

```python
# Python / Flask
from flask import request

real_ip = request.headers.get('X-Real-IP')
forwarded_for = request.headers.get('X-Forwarded-For')
proto = request.headers.get('X-Forwarded-Proto')

# Generiši ispravne URL-ove za HTTPS redirect
if proto != 'https':
    return redirect('https://' + request.host + request.path)
```

```javascript
// Node.js / Express
app.set('trust proxy', 1);  // veruj prvom proxy-ju

app.get('/', (req, res) => {
    const realIP = req.ip;                         // iz X-Real-IP
    const protocol = req.protocol;                 // iz X-Forwarded-Proto
    res.json({ ip: realIP, protocol: protocol });
});
```

## Timeout direktive

```nginx
location / {
    proxy_pass  http://127.0.0.1:3000;

    proxy_connect_timeout  10s;  # max čekanje na uspostavljanje konekcije sa backend-om
    proxy_send_timeout     30s;  # max čekanje na slanje request-a backend-u
    proxy_read_timeout     60s;  # max čekanje na odgovor od backend-a (kritično!)

    # Buffering
    proxy_buffering         on;    # Nginx čeka ceo odgovor, pa šalje klijentu
    proxy_buffer_size       4k;    # veličina jednog bafera
    proxy_buffers           8 16k; # broj i veličina bafera za telo odgovora
    proxy_busy_buffers_size 32k;
}
```

### Buffering on vs off

| | Buffering ON | Buffering OFF |
|-|-------------|--------------|
| Backend | Brzo završi i zatvori konekciju | Čeka dok klijent ne preuzme sve |
| Spori klijenti | Backend slobodan odmah | Backend zauzet za sve vreme |
| Streaming | Ne radi dobro | Odlično |
| WebSocket | Ne koristiti | Obavezno isključiti |

```nginx
# Za streaming / SSE (Server-Sent Events)
location /stream/ {
    proxy_pass          http://127.0.0.1:3000;
    proxy_buffering     off;
    proxy_read_timeout  3600s;   # dugi timeout za stream
}
```

## SSL terminacija sa proxy-jem

```nginx
server {
    listen 80;
    server_name app.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name app.example.com;

    ssl_certificate     /etc/letsencrypt/live/app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/app.example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;

    location / {
        proxy_pass  http://127.0.0.1:3000;   # plain HTTP ka backend-u!

        proxy_set_header  Host               $host;
        proxy_set_header  X-Real-IP          $remote_addr;
        proxy_set_header  X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header  X-Forwarded-Proto  $scheme;   # "https"
        proxy_http_version  1.1;
        proxy_set_header    Connection  "";
    }
}
```

Backend prima HTTP ali zna (iz `X-Forwarded-Proto: https`) da je originalni zahtev bio HTTPS.
