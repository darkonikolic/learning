# Nginx — Load Balancer

## Šta je load balancer?

Load balancer (raspoređivač opterećenja) prima sve zahteve i distribuira ih na više backend servera kako nijedan ne bi bio preopterećen.

```
Bez load balancera:
  1000 korisnika ────────────────────► Server (pada pod opterećenjem)

Sa load balancerom:
  1000 korisnika ──► Nginx LB ───────► Server 1 (~333 korisnika)
                              ├──────► Server 2 (~333 korisnika)
                              └──────► Server 3 (~334 korisnika)
```

---

## Zašto više servera?

| Razlog | Objašnjenje |
|--------|-------------|
| **Visoka dostupnost** | Ako jedan server padne, ostali preuzimaju |
| **Horizontalno skaliranje** | Dodaj novi server umesto kupovine jačeg |
| **Zero-downtime deploy** | Deploy na jedan server, preusmeri saobraćaj |
| **Performanse** | Paralelna obrada zahteva |

---

## Osnovna konfiguracija load balancera

```nginx
http {
    upstream backend_servers {
        server 10.0.0.1:3000;
        server 10.0.0.2:3000;
        server 10.0.0.3:3000;
    }

    server {
        listen 80;
        server_name example.com;

        location / {
            proxy_pass http://backend_servers;
        }
    }
}
```

---

## Algoritmi raspoređivanja

### Round Robin (default)

Zahtevi idu redom — server1, server2, server3, server1, server2...

```nginx
upstream backend {
    server 10.0.0.1:3000;  # dobija 1/3 zahteva
    server 10.0.0.2:3000;  # dobija 1/3 zahteva
    server 10.0.0.3:3000;  # dobija 1/3 zahteva
}
```

Dobar kada su svi serveri iste snage i svi zahtevi sličnog trajanja.

### Weighted (ponderisano)

Server sa većim `weight` dobija proporcionalno više zahteva.

```nginx
upstream backend {
    server 10.0.0.1:3000 weight=1;  # ~17% zahteva
    server 10.0.0.2:3000 weight=2;  # ~33% zahteva
    server 10.0.0.3:3000 weight=3;  # ~50% zahteva
}
```

Dobar kada serveri imaju različite kapacitete.

### Least Connections

Sledeći zahtev ide na server koji trenutno ima najmanji broj aktivnih konekcija.

```nginx
upstream backend {
    least_conn;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
}
```

Dobar kada zahtevi imaju različito trajanje (npr. file upload + kratki API pozivi).

### IP Hash (sticky sessions)

Isti klijent (po IP adresi) uvek ide na isti server.

```nginx
upstream backend {
    ip_hash;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
}
```

Dobar kada aplikacija čuva session u memoriji servera (ne u Redis-u). Mana: neravnomerna distribucija ako mnogo korisnika ima isti IP (NAT, proxy).

### Hash po URL (za cache konzistenciju)

```nginx
upstream backend {
    hash $request_uri consistent;
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
    server 10.0.0.3:3000;
}
```

Isti URL uvek ide na isti server — dobro za server-side caching.

---

## Failover i health check

```nginx
upstream backend {
    # max_fails=3: ako server ima 3 greške unutar fail_timeout sekundi
    # fail_timeout=30s: isključi ga na 30 sekundi, onda probaj ponovo
    server 10.0.0.1:3000  max_fails=3  fail_timeout=30s;
    server 10.0.0.2:3000  max_fails=3  fail_timeout=30s;

    # Backup — koristi se SAMO ako su svi ostali nedostupni
    server 10.0.0.3:3000  backup;

    # Down — trajno isključen (maintenance)
    server 10.0.0.4:3000  down;

    keepalive 32;  # connection pool prema backend-u
}
```

### Šta se smatra greškom?

Nginx označava server kao nezdrav ako dobije:
- TCP grešku konekcije (server ne odgovara)
- HTTP 500, 502, 503, 504 odgovor

```nginx
upstream backend {
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
}

server {
    location / {
        proxy_pass http://backend;

        # Automatski pokušaj sledeći server u slučaju greške
        proxy_next_upstream error timeout http_500 http_502 http_503;
        proxy_next_upstream_tries 3;        # max 3 pokušaja
        proxy_next_upstream_timeout 10s;    # ukupno max 10s za pokušaje
    }
}
```

---

## Health check endpoint

Dodaj `/health` endpoint na svaku aplikaciju, Nginx provjeri:

```nginx
upstream backend {
    server 10.0.0.1:3000;
    server 10.0.0.2:3000;
}

# Nginx Plus ima ugrađen aktivni health check
# U open-source Nginx — koristiti nginx_upstream_check_module ili pasivnu provjeru
```

```javascript
// Primer /health endpoint u Node.js
app.get('/health', (req, res) => {
    res.json({ status: 'ok', timestamp: Date.now() });
});
```

---

## Layer 4 vs Layer 7 load balancing

| | Layer 4 (TCP) | Layer 7 (HTTP) |
|-|--------------|----------------|
| Nivo | Transport | Aplikacija |
| Vidi | IP + port | HTTP metodu, URL, headere, cookie |
| Routing | Po IP/portu | Po URL-u, domenu, headeru |
| Nginx blok | `stream {}` | `http {}` |
| Brzina | Brži | Sporiji (mora parsovati HTTP) |
| Mogućnosti | Manje | Više (A/B testing, sticky sessions) |

### Layer 4 — TCP load balancing (Nginx stream)

```nginx
stream {
    upstream mysql_cluster {
        server 10.0.0.1:3306;
        server 10.0.0.2:3306;
    }

    server {
        listen 3306;
        proxy_pass mysql_cluster;
    }
}
```

---

## Kompletna produkciona konfiguracija

```nginx
upstream web_app {
    least_conn;
    server 10.0.0.1:3000  max_fails=3  fail_timeout=30s;
    server 10.0.0.2:3000  max_fails=3  fail_timeout=30s;
    server 10.0.0.3:3000  max_fails=3  fail_timeout=30s;
    server 10.0.0.4:3000  backup;
    keepalive 32;
}

server {
    listen 80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_session_cache   shared:SSL:10m;

    add_header Strict-Transport-Security "max-age=31536000" always;

    access_log /var/log/nginx/lb.access.log main;
    error_log  /var/log/nginx/lb.error.log  warn;

    location / {
        proxy_pass http://web_app;
        proxy_http_version  1.1;

        proxy_set_header  Host               $host;
        proxy_set_header  X-Real-IP          $remote_addr;
        proxy_set_header  X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header  X-Forwarded-Proto  $scheme;
        proxy_set_header  Connection         "";

        proxy_connect_timeout  5s;
        proxy_read_timeout    30s;

        # Automatski retry na sledećem serveru kod greške
        proxy_next_upstream error timeout http_502 http_503;
        proxy_next_upstream_tries 2;
    }

    # Healthcheck endpoint — izuzeti od logovanja
    location /health {
        proxy_pass http://web_app;
        access_log off;
    }
}
```

---

## Monitoring load balancera

```nginx
# Nginx status endpoint
server {
    listen 127.0.0.1:8080;
    location /nginx_status {
        stub_status;
    }
}
```

```bash
# Provjeri aktivne konekcije
curl http://127.0.0.1:8080/nginx_status

# Provjeri koji server odgovara (dodaj custom header u backend)
for i in $(seq 1 6); do
    curl -s -o /dev/null -w "%{http_code} from %{remote_ip}\n" https://example.com/
done

# Prati greške u real time
sudo tail -f /var/log/nginx/lb.error.log | grep -E "upstream|failed"
```

---

## Kada koristiti Nginx LB, a kada HAProxy?

| | Nginx | HAProxy |
|-|-------|---------|
| SSL terminacija | Odlično | Dobro |
| HTTP/2 | Da | Da |
| Statički fajlovi | Da | Ne |
| TCP LB | Da | Odlično |
| Health check | Pasivni (OSS) | Aktivni ugrađen |
| Stats dashboard | Stub Status | Detaljna web UI |
| WebSocket | Da | Da |

Za većinu scenarija Nginx je dovoljan. HAProxy je bolji izbor kada treba napredno upravljanje konekcijama na TCP nivou.
