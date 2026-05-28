# Nginx — Uvod i arhitektura

## Šta je Nginx?

Nginx (čita se "engine-x") je visoko-performansni web server, reverse proxy, load balancer i HTTP cache. Napravljen je 2004. od strane Igora Sysoeva sa ciljem da reši C10k problem — istovremena obrada 10.000 konekcija.

Za razliku od Apache-a koji koristi **thread-per-connection** model, Nginx koristi **event-driven, asinhroni, neblokirajući** model — jedan worker proces može da obradi hiljade konekcija bez kreiranja novih procesa ili niti.

## Šta Nginx može da uradi?

| Uloga | Opis |
|-------|------|
| Web server | Servira statičke fajlove (HTML, CSS, slike) |
| Reverse proxy | Prosleđuje zahteve ka backend aplikaciji |
| Load balancer | Distribucija saobraćaja na više servera |
| HTTP cache | Kešira odgovore i smanjuje opterećenje backend-a |
| SSL terminator | Obrađuje HTTPS, backend prima plain HTTP |
| API gateway | Rate limiting, autentifikacija, routing |

## Event-driven arhitektura

```
Apache (thread-per-connection):
  Zahtev 1 → Thread 1 (blokira dok čeka I/O)
  Zahtev 2 → Thread 2 (blokira dok čeka I/O)
  Zahtev 3 → Thread 3 (blokira dok čeka I/O)
  ... 1000 zahteva = 1000 threadova (memorija!)

Nginx (event loop):
  Worker → Event loop → Zahtev 1 (čeka I/O, pređe na sledeći)
                      → Zahtev 2 (čeka I/O, pređe na sledeći)
                      → Zahtev 3 (odgovor spreman, pošalji)
  ... 1000 zahteva = 1 worker, ~1MB memorije
```

## Struktura procesa

```
┌─────────────────────────────────┐
│         Master Process          │
│  - pokreće se kao root          │
│  - čita konfiguraciju           │
│  - upravlja worker procesima    │
│  - PID: /run/nginx.pid          │
└──────────────┬──────────────────┘
               │  fork()
   ┌───────────┼───────────┐
   │           │           │
┌──▼──┐    ┌──▼──┐    ┌──▼──┐
│ W1  │    │ W2  │    │ W3  │
│event│    │event│    │event│
│loop │    │loop │    │loop │
└─────┘    └─────┘    └─────┘
Worker procesi — jedan po CPU jezgru
```

- **Master process** — pokreće se kao root, kreira sokete, pokreće worker-e
- **Worker procesi** — obrađuju zahteve, ne zahtevaju root privilegije
- Broj workera = broj CPU jezgara (`worker_processes auto`)

## Nginx vs Apache — kada koji?

| Scenario | Nginx | Apache |
|----------|-------|--------|
| Mnogo statičkih fajlova | Odlično | Dobro |
| Mnogo istovremenih konekcija | Odlično | Loše (thread overhead) |
| PHP aplikacije | Dobro (FPM) | Odlično (mod_php) |
| .htaccess po direktorijumu | Ne podržava | Da |
| Memorijska efikasnost | Odlično | Slabije |
| Reverse proxy / LB | Odlično | Dobro |
