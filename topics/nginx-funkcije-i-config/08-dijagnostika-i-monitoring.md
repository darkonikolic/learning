# Nginx — Dijagnostika i monitoring

## Testiranje konfiguracije

```bash
# UVEK pokrenuti pre reload-a!
sudo nginx -t

# Uspešan izlaz:
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful

# Sa prikazom putanja
sudo nginx -T    # ispisuje celu konfiguraciju sa include-ovanim fajlovima
```

## Logovi

```bash
# Prati access log u realnom vremenu
sudo tail -f /var/log/nginx/access.log

# Prati error log
sudo tail -f /var/log/nginx/error.log

# Samo greške (4xx i 5xx)
sudo tail -f /var/log/nginx/access.log | grep -E '" [45][0-9]{2} '

# Posle reload-a — provjeri da nema novih grešaka
sudo journalctl -u nginx -f

# Pretraga error loga
sudo grep "upstream timed out" /var/log/nginx/error.log | tail -20
```

## Log format

```nginx
http {
    # Prošireni format sa vremenom odgovora i upstream info
    log_format  detailed  '$remote_addr - $remote_user [$time_local] '
                           '"$request" $status $body_bytes_sent '
                           'rt=$request_time '
                           'urt=$upstream_response_time '
                           'uaddr=$upstream_addr '
                           '"$http_referer" "$http_user_agent"';

    access_log /var/log/nginx/detailed.log detailed;

    # JSON format (lakši za ELK/Loki/Grafana)
    log_format  json_log  escape=json
        '{'
            '"time":"$time_iso8601",'
            '"remote_addr":"$remote_addr",'
            '"method":"$request_method",'
            '"uri":"$request_uri",'
            '"status":$status,'
            '"bytes_sent":$body_bytes_sent,'
            '"request_time":$request_time,'
            '"upstream_time":"$upstream_response_time"'
        '}';
}
```

## Stub Status — statistike konekcija

```nginx
server {
    listen 127.0.0.1:8080;  # samo lokalno dostupno!

    location /nginx_status {
        stub_status;
        allow 127.0.0.1;
        deny all;
    }
}
```

```bash
curl http://127.0.0.1:8080/nginx_status
```

Izlaz:
```
Active connections: 42
server accepts handled requests
 1000 1000 5000
Reading: 1 Writing: 5 Waiting: 36
```

| Polje | Opis |
|-------|------|
| Active connections | Ukupno aktivnih konekcija |
| accepts | Ukupno prihvaćenih konekcija od starta |
| handled | Ukupno obrađenih (obično = accepts) |
| requests | Ukupno obrađenih HTTP zahteva |
| Reading | Nginx čita request header |
| Writing | Nginx šalje odgovor klijentu |
| Waiting | Keep-alive konekcije koje čekaju sledeći zahtev |

## Provjera konekcija i portova

```bash
# Da li Nginx sluša na portu
ss -tlnp | grep nginx
# ili
netstat -tlnp | grep nginx

# Aktivne konekcije ka Nginx-u
ss -tn | grep ':443'

# Ko zauzima port 80
sudo lsof -i :80
```

## Debug mod za specifičan zahtev

```nginx
server {
    # Loguj debug info za konkretni IP
    geo $debug_this {
        default 0;
        192.168.1.100 1;   # tvoj IP za debug
    }

    access_log /var/log/nginx/debug.log combined if=$debug_this;
}
```

## Greške i dijagnoza

| Greška | Uzrok | Rešenje |
|--------|-------|---------|
| `403 Forbidden` | Pogrešna prava fajlova ili SELinux | `chmod -R 755 /var/www/`, provjeri SELinux |
| `404 Not Found` | Fajl ne postoji, pogrešan root | Provjeri `root` direktive i putanju |
| `502 Bad Gateway` | Backend ne radi | Provjeri aplikaciju: `systemctl status app` |
| `503 Service Unavailable` | Svi upstream serveri nedostupni | Provjeri upstream servere |
| `504 Gateway Timeout` | Backend spor | Povećaj `proxy_read_timeout` |
| `413 Request Entity Too Large` | Upload fajl prevelik | `client_max_body_size 50M;` |
| `connect() failed (111)` | Backend odbija konekciju | Backend ne sluša na tom portu |
| `upstream sent invalid header` | Backend šalje neispravan HTTP odgovor | Provjeri backend logove |

## Česte komande — brzi pregled

```bash
sudo nginx -t                           # test config
sudo nginx -s reload                    # reload bez prekida
sudo systemctl restart nginx            # restart (kratki prekid)
sudo tail -f /var/log/nginx/error.log   # live error log
sudo tail -f /var/log/nginx/access.log  # live access log
sudo nginx -V 2>&1 | grep prefix        # gdje su fajlovi
curl -I http://localhost                 # provjeri odgovor
```
