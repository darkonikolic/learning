# Let's Encrypt — Besplatni SSL sertifikati

## Šta je Let's Encrypt?

Let's Encrypt je besplatna, automatizovana, otvorena sertifikaciona ustanova (CA) koja izdaje DV sertifikate. Pokrenuta 2016. od strane Linux Foundation i Mozilla-e.

| | Let's Encrypt | Komercijalni CA |
|-|--------------|-----------------|
| Cena | Besplatno | $10 - $500/god |
| Tip | DV | DV / OV / EV |
| Trajanje | **90 dana** | 1-2 godine |
| Obnavljanje | **Automatski** | Ručno |
| Wildcard | Da (DNS challenge) | Da (uz naknadu) |
| Browser poverenje | Da (svi moderni) | Da |

90-dnevno trajanje je dizajn odluka — forsira automatizaciju i smanjuje štetu od kompromitovanog ključa.

---

## ACME protokol i Certbot

Let's Encrypt koristi **ACME** protokol za verifikaciju vlasništva domena. **Certbot** je referentni ACME klijent.

### Verifikacija domena — HTTP-01 challenge

```
1. Certbot traži sertifikat za example.com
2. Let's Encrypt: "Dokaži da kontrolišeš example.com"
3. Certbot kreira fajl na: http://example.com/.well-known/acme-challenge/TOKEN
4. Let's Encrypt preuzme TOKEN fajl
5. Potvrđeno → izdaje sertifikat
```

```
Zahteva: server mora biti dostupan na portu 80 sa interneta
Nije moguće za: lokalne servere, privatne IP-ove, wildcard sertifikate
```

### Verifikacija domena — DNS-01 challenge

```
1. Certbot traži wildcard sertifikat za *.example.com
2. Let's Encrypt: "Postavi TXT DNS zapis"
3. Certbot postavi: _acme-challenge.example.com → TOKEN
4. Let's Encrypt provjeri DNS
5. Potvrđeno → izdaje wildcard sertifikat
```

```
Može za: wildcard, interni serveri, serveri bez javnog porta 80
Zahteva: DNS API ili ručno podešavanje DNS-a
```

---

## Instalacija Certbota

```bash
# Ubuntu/Debian
sudo apt install certbot python3-certbot-nginx

# CentOS/RHEL
sudo dnf install certbot python3-certbot-nginx
```

---

## Dobijanje sertifikata

### Nginx plugin (najjednostavnije)

Certbot automatski izmeni Nginx konfiguraciju i doda SSL.

```bash
sudo certbot --nginx -d example.com -d www.example.com

# Certbot:
# 1. Verifikuje domene putem HTTP-01
# 2. Generiše ključ i sertifikat
# 3. Izmeni nginx config (dodaje ssl_certificate direktive)
# 4. Reload nginx
```

### Standalone (bez web servera)

```bash
# Zaustavi Nginx privremeno (Certbot koristi port 80)
sudo systemctl stop nginx
sudo certbot certonly --standalone -d example.com
sudo systemctl start nginx
```

### Webroot (bez zaustavljanja servera)

```bash
# Nginx mora servirati /.well-known/
# /etc/nginx/sites-available/example.com:
# location /.well-known/acme-challenge/ {
#     root /var/www/certbot;
# }

sudo certbot certonly --webroot \
    -w /var/www/certbot \
    -d example.com -d www.example.com
```

### Wildcard sertifikat (DNS challenge)

```bash
# Interaktivno — traži ručno postavljanje DNS zapisa
sudo certbot certonly --manual \
    --preferred-challenges dns \
    -d "*.example.com" -d "example.com"

# Certbot prikazuje TXT vrednost za _acme-challenge.example.com
# Postavi u DNS panel, pričekaj propagaciju (~1 min), press Enter
```

---

## Lokacija sertifikata

```
/etc/letsencrypt/
├── live/
│   └── example.com/
│       ├── cert.pem       ← samo server sertifikat
│       ├── chain.pem      ← intermediate CA sertifikati
│       ├── fullchain.pem  ← cert + chain (ovo koristi Nginx)
│       └── privkey.pem    ← privatni ključ
├── archive/
│   └── example.com/       ← svi stari sertifikati (backup)
└── renewal/
    └── example.com.conf   ← konfiguracija za obnavljanje
```

---

## Nginx konfiguracija sa Let's Encrypt

```nginx
server {
    listen 80;
    server_name example.com www.example.com;

    # Potrebno za Certbot webroot i obnavljanje
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    ssl_protocols        TLSv1.2 TLSv1.3;
    ssl_session_cache    shared:SSL:10m;
    ssl_session_timeout  1d;

    add_header Strict-Transport-Security "max-age=31536000" always;

    root  /var/www/example.com;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

---

## Automatsko obnavljanje

Certbot instalira cron job ili systemd timer koji automatski obnavlja sertifikate.

```bash
# Provjeri da li timer postoji
sudo systemctl status certbot.timer
# ili
sudo crontab -l | grep certbot

# Ručni test obnavljanja (ne obnavlja stvarno)
sudo certbot renew --dry-run

# Ručno obnavljanje
sudo certbot renew

# Obnovi samo jedan domen
sudo certbot renew --cert-name example.com

# Provjeri koji sertifikati su instalirani
sudo certbot certificates
```

### Manuelni cron za obnavljanje (ako nema automatskog)

```bash
# /etc/cron.d/certbot
0 3 * * * root certbot renew --quiet --post-hook "systemctl reload nginx"
```

---

## Hook-ovi — akcije pre/posle obnavljanja

```bash
# Reload nginx nakon obnavljanja
sudo certbot renew --post-hook "systemctl reload nginx"

# Trajno konfigurisanje hook-ova
# /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
#!/bin/bash
systemctl reload nginx

chmod +x /etc/letsencrypt/renewal-hooks/post/reload-nginx.sh
```

---

## Česte greške

| Greška | Uzrok | Rešenje |
|--------|-------|---------|
| `Connection refused` | Port 80 nije otvoren | Provjeri firewall |
| `DNS problem` | DNS ne upućuje na server | `dig +short example.com` |
| `Too many certificates` | Rate limit (5 cert/sedmici po domenu) | Koristi `--staging` za testiranje |
| `Certificate not yet due for renewal` | Još ima > 30 dana | `--force-renewal` ili čekaj |

```bash
# Let's Encrypt staging (beskonačni testovi, bez rate limita)
sudo certbot --nginx --staging -d example.com
# Staging sertifikati ne važe u browseru — samo za testiranje
```
