# Nginx Reverse Proxy — Šta je i zašto

## Forward proxy vs Reverse proxy

**Forward proxy** stoji ispred klijenata — skriva identitet korisnika od servera (VPN, corporate proxy).

**Reverse proxy** stoji ispred servera — klijenti ne znaju koji server zapravo odgovara na zahtev.

```
Forward proxy:
  Klijent → [Forward Proxy] → Internet → Server
  (server vidi proxy IP, ne klijentov)

Reverse proxy:
  Klijent → [Reverse Proxy] → App server 1
                           → App server 2
                           → App server 3
  (klijent misli da razgovara sa proxy-jem)
```

## Zašto koristiti Nginx kao reverse proxy?

| Razlog | Objašnjenje |
|--------|-------------|
| **SSL terminacija** | Nginx obrađuje HTTPS, backend prima plain HTTP |
| **Load balancing** | Distribucija saobraćaja na više instanci aplikacije |
| **Caching** | Kešira odgovore, smanjuje opterećenje backend-a |
| **Kompresija** | Gzip odgovora pre slanja klijentu |
| **Bezbednost** | Skriva internu arhitekturu, IP adrese, portove |
| **Rate limiting** | Zaštita od brute-force i DDoS napada |
| **Statički fajlovi** | Nginx servira CSS/JS/slike, backend samo API |
| **Jedan port za više servisa** | Svi servisi na :80/:443, routing po domenu ili putanji |

## Tipičan scenario

Bez reverse proxy-ja:
```
Klijent → Node.js app :3000
Klijent → Django app  :8000
Klijent → Grafana     :3001
Klijent → pgAdmin     :5050
```
Problem: korisnik mora da zna portove, nema SSL centralizovano, nema zaštite.

Sa Nginx reverse proxy-jem:
```
Klijent → Nginx :443 → api.firma.com   → Node.js :3000
                    → admin.firma.com  → Django  :8000
                    → monitor.firma.com→ Grafana :3001
                    → db.firma.com     → pgAdmin :5050
```
Jedan SSL sertifikat (wildcard), jedan firewall, jedan tačka za logove.

## Protokoli koje Nginx može da proksira

| Protokol | Direktiva | Port |
|----------|-----------|------|
| HTTP/HTTPS | `proxy_pass` | 80/443 |
| WebSocket | `proxy_pass` + Upgrade header | 80/443 |
| FastCGI (PHP) | `fastcgi_pass` | socket/9000 |
| uWSGI (Python) | `uwsgi_pass` | socket/3031 |
| gRPC | `grpc_pass` | 50051 |
| TCP/UDP | `stream {}` blok | bilo koji |
