# Nginx — Šta je SSL, TLS i HTTPS?

## Problem bez šifrovanja

HTTP je plain text protokol. Sve što pošalješ vidljivo je svakome na mreži:

```
Browser → [GET /login HTTP/1.1 \n username=darko&password=tajna123] → Server
               ↑
       Svako na WiFi-u, ISP, router — može ovo da vidi!
```

---

## SSL i TLS — šta je razlika?

| | SSL | TLS |
|-|-----|-----|
| Pun naziv | Secure Sockets Layer | Transport Layer Security |
| Status | **Zastareo i nesiguran** | Aktivan standard |
| Verzije | SSL 2.0, 3.0 | TLS 1.0, 1.1, 1.2, **1.3** |
| Ko koristi danas | Niko (zabranjen) | Svi |

U svakodnevnom govoru: "SSL sertifikat", "SSL/HTTPS" — ali stvarni protokol je uvek TLS.
Nginx u konfiguraciji: `ssl_protocols TLSv1.2 TLSv1.3` (starije verzije se isključuju).

---

## HTTPS = HTTP + TLS

```
HTTP:  Browser ──[plain text]──────────────────────────────► Server
HTTPS: Browser ──[TLS šifrovan kanal]──────────────────────► Server
                     └── HTTP unutar šifrovanog kanala
```

HTTPS pruža tri garancije:

| Garancija | Opis |
|-----------|------|
| **Šifrovanje** | Niko osim tebe i servera ne može pročitati podatke |
| **Integritet** | Niko nije izmenio podatke tokom prenosa |
| **Autentičnost** | Server je zaista onaj za koga se predstavlja (ne napadač) |

---

## Kako TLS handshake funkcioniše?

```
Browser                             Server
   │                                   │
   │──── ClientHello ─────────────────►│  "Podržavam TLS 1.3, evo mojih cipher suite-ova"
   │                                   │
   │◄─── ServerHello ──────────────────│  "Koristimo TLS 1.3 + AES-256-GCM"
   │◄─── Sertifikat ───────────────────│  "Evo mog sertifikata (javni ključ)"
   │                                   │
   │  Browser verifikuje sertifikat:   │
   │  - Da li je istekao?              │
   │  - Da li je domen tačan?          │
   │  - Da li lanac vodi do CA kome verujem?
   │                                   │
   │──── Razmena ključeva ────────────►│  Ephemeral ključ, Diffie-Hellman
   │                                   │  Oba sada imaju isti session key
   │                                   │
   │◄════ Šifrovani HTTP saobraćaj ═══►│  Sve šifrovano AES-256
   │  GET /login                       │
   │  password=tajna123               │
   └───────────────────────────────────┘
   (niko na mreži ne može ovo pročitati)
```

---

## Asimetrično vs simetrično šifrovanje u TLS-u

TLS kombinuje oba tipa:

```
1. Asimetrično (Diffie-Hellman / ECDH):
   ─────────────────────────────────────
   Javni ključ servera svi vide.
   Privatni ključ servera samo server zna.
   Browser i server matematički izvode ISTI tajni session key
   — bez da ga ikad pošalju mrežom!
   (Čak i ako neko snimi sve pakete, ne može izračunati session key)

2. Simetrično (AES-256-GCM):
   ─────────────────────────
   Session key se koristi za šifrovanje svih podataka.
   Brže od asimetričnog — idealno za bulk enkripciju.
   Session key se baca na kraju sesije (Forward Secrecy).
```

---

## Šta je SSL sertifikat (u praksi)?

SSL sertifikat je **datoteka** koja sadrži:
- Domen za koji važi (`CN=example.com`, `SAN=www.example.com`)
- Javni ključ servera
- Potpis CA-a (ko garantuje da sertifikat pripada tom domenu)
- Datum izdavanja i isteka

```bash
# Prikaži sertifikat koji Nginx šalje
openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
    | openssl x509 -text -noout | grep -E "Subject|Not|DNS"
```

---

## Nginx i SSL terminacija

Nginx prima HTTPS zahtev od browsera, dešifruje ga, i prosleđuje internoj aplikaciji kao plain HTTP:

```
Browser ──[HTTPS]──► Nginx ──[HTTP]──► App :3000
                       │
                  dešifruje TLS
                  šalje plain HTTP
                  (sigurno jer je localhost)
```

```nginx
server {
    listen 443 ssl http2;
    server_name example.com;

    # Fajlovi koje generiše Let's Encrypt ili openssl
    ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # Zabrani stare, nesigurne verzije protokola
    ssl_protocols  TLSv1.2 TLSv1.3;

    location / {
        proxy_pass http://127.0.0.1:3000;   # plain HTTP lokalno
        proxy_set_header X-Forwarded-Proto $scheme;  # app zna da je bio HTTPS
    }
}
```

---

## HTTP/2

HTTP/2 je nova verzija HTTP protokola — dostupna samo uz HTTPS.

| | HTTP/1.1 | HTTP/2 |
|-|----------|--------|
| Konekcije | Jedna zahtev po konekciji | Multipleksing — više zahteva odjednom |
| Headeri | Plain text, ponavljaju se | Binarni, kompresovani (HPACK) |
| Server Push | Ne | Da |
| Brzina | Spora za mnogo fajlova | Značajno brža |

```nginx
listen 443 ssl http2;   # dodaj "http2" — to je sve što treba
```

---

## Zašto browser prikazuje upozorenje za neki HTTPS?

```
Vaš sertifikat nije pouzdan  ← self-signed ili nepoznati CA
NET::ERR_CERT_DATE_INVALID   ← sertifikat je istekao
NET::ERR_CERT_COMMON_NAME    ← sertifikat je za drugi domen
NET::ERR_SSL_PROTOCOL_ERROR  ← server koristi stari TLS (1.0/1.1)
```

Svi ovi slučajevi su **sigurnosni problemi** — TLS kanal se uspostavlja, ali identitet nije verifikovan.
