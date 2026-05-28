# Nginx — Instalacija

## Ubuntu / Debian

```bash
sudo apt update
sudo apt install nginx

# Pokretanje i autostart
sudo systemctl start nginx
sudo systemctl enable nginx

# Provjera statusa
sudo systemctl status nginx
```

## CentOS / RHEL / Rocky Linux

```bash
# RHEL 8+
sudo dnf install nginx

# CentOS 7
sudo yum install epel-release
sudo yum install nginx

sudo systemctl start nginx
sudo systemctl enable nginx
```

## Provjera verzije i kompajliranih modula

```bash
nginx -v            # kratka verzija
nginx -V            # verzija + svi compile-time parametri i moduli

# Korisno za provjeru koje putanje nginx koristi
nginx -V 2>&1 | grep -E 'prefix|conf-path|error-log|http-log|pid'
```

Primer izlaza:
```
--prefix=/etc/nginx
--conf-path=/etc/nginx/nginx.conf
--error-log-path=/var/log/nginx/error.log
--http-log-path=/var/log/nginx/access.log
--pid-path=/run/nginx.pid
```

## Struktura instaliranih fajlova

```
/etc/nginx/               ← konfiguracija
/var/log/nginx/           ← logovi
/var/www/html/            ← default web root
/usr/share/nginx/html/    ← alternativni default root (CentOS)
/run/nginx.pid            ← PID master procesa
/usr/sbin/nginx           ← binary
```

## Upravljanje servisom

```bash
# Testiranje konfiguracije (UVEK pre reload-a!)
sudo nginx -t

# Reload bez prekida (graceful)
sudo nginx -s reload
# ili
sudo systemctl reload nginx

# Restart (kratkotrajni prekid)
sudo systemctl restart nginx

# Stop
sudo nginx -s stop        # forsirani
sudo nginx -s quit        # graceful (čeka kraj aktivnih konekcija)
```

## Firewall podešavanje

```bash
# UFW (Ubuntu)
sudo ufw allow 'Nginx Full'   # HTTP + HTTPS
sudo ufw allow 'Nginx HTTP'   # samo HTTP
sudo ufw allow 'Nginx HTTPS'  # samo HTTPS
sudo ufw status

# firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

## Let's Encrypt SSL sertifikat

```bash
# Instalacija certbot-a
sudo apt install certbot python3-certbot-nginx

# Automatsko dobijanje i konfigurisanje SSL-a
sudo certbot --nginx -d example.com -d www.example.com

# Provjera automatskog obnavljanja
sudo certbot renew --dry-run
```
