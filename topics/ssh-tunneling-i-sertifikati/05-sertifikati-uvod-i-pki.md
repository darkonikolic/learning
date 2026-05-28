# Sertifikati — Uvod i PKI

## Zašto postoje digitalni sertifikati?

Kada tvoj browser otvori `https://banka.rs`, kako zna da razgovara sa pravom bankom, a ne sa napadačem?

```
Problem bez sertifikata:
  Browser ──────────────────────────────────────► "banka.rs"
  Browser ne zna da li je ovo prava banka ili MITM napad!

Sa sertifikatima:
  Browser ──────────────────────────────────────► banka.rs
  Server šalje sertifikat: "Ja sam banka.rs, potpisao GlobalSign"
  Browser provjeri: "Znam GlobalSign, njemu verujem → verujem banci"
```

Digitalni sertifikat je **elektronska lična karta servera** — potvrđuje identitet i sadrži javni ključ za šifrovanje.

---

## PKI — Public Key Infrastructure

PKI je sistem poverenja koji čini da sertifikati funkcionišu.

```
Root CA (Comodo, DigiCert, GlobalSign...)
  └── Intermediate CA
        └── Sertifikat za banka.rs
              └── Browser veruje jer "lanci poverenja" vodi do Root CA
```

### Lanac poverenja (Chain of Trust)

```
Root CA sertifikat
  └── Intermediate CA sertifikat
        └── Server sertifikat (leaf certificate)
              ↓
              Ovaj sertifikat je ono što Nginx šalje browseru
              (fullchain.pem = server cert + intermediate certs)
```

Browser ima ugrađenu listu ~150 Root CA-ova kojima veruje. Ako se lanac poverenja ne može proslediti do nekog od tih, browser daje upozorenje.

---

## Šta sertifikat sadrži?

```bash
# Prikaz sadržaja sertifikata
openssl x509 -in /etc/letsencrypt/live/example.com/cert.pem -text -noout
```

```
Certificate:
    Data:
        Version: 3 (0x2)
        Serial Number: 04:51:...
        Signature Algorithm: sha256WithRSAEncryption
        Issuer: C=US, O=Let's Encrypt, CN=R3        ← Ko je potpisao (CA)
        Validity
            Not Before: Jan  1 00:00:00 2024 GMT     ← Od kad važi
            Not After : Apr  1 00:00:00 2024 GMT     ← Do kad važi (90 dana)
        Subject: CN=example.com                      ← Za koji domen
        Subject Alternative Names:
            DNS:example.com
            DNS:www.example.com                      ← SAN: svi domeni
        Public Key Algorithm: id-ecPublicKey         ← Javni ključ
```

---

## Tipovi sertifikata

| Tip | Provera | Vreme | Cena | Upotreba |
|-----|---------|-------|------|---------|
| **DV** (Domain Validated) | Samo vlasništvo domena | Minuti | Besplatno/jeftino | Većina web sajtova, API-ji |
| **OV** (Organization Validated) | Domen + firma | Dani | Srednja | B2B sajtovi |
| **EV** (Extended Validated) | Detaljno + firma | Sedmice | Visoka | Banke (stari zeleni bar) |
| **Wildcard** | Domen + subdomeni | Minuti | Srednja | `*.example.com` |
| **Multi-SAN** | Više domena | Minuti | Srednja | `site1.com + site2.com` |

---

## Formati sertifikata

| Format | Ekstenzija | Opis |
|--------|-----------|------|
| **PEM** | `.pem`, `.crt`, `.key` | Base64, čitljiv tekst, Linux standard |
| **DER** | `.der`, `.cer` | Binarni, Windows/Java |
| **PKCS#12** | `.pfx`, `.p12` | Bundle: cert + privatni ključ, Windows/Java |
| **PKCS#7** | `.p7b` | Samo sertifikati, bez ključa |

```bash
# PEM fajl izgleda ovako:
-----BEGIN CERTIFICATE-----
MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
...
-----END CERTIFICATE-----
```

---

## Ključni fajlovi (Let's Encrypt)

```
/etc/letsencrypt/live/example.com/
├── cert.pem        ← Samo tvoj sertifikat
├── chain.pem       ← Intermediate CA sertifikati
├── fullchain.pem   ← cert.pem + chain.pem (ovo šalje Nginx klijentu)
└── privkey.pem     ← PRIVATNI KLJUČ (nikad ne deliti!)
```

U Nginx konfiguraciji:
```nginx
ssl_certificate     /etc/letsencrypt/live/example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;
```

---

## Simetično vs Asimetrično šifrovanje u TLS-u

TLS koristi oba tipa šifrovanja zajedno:

```
1. TLS Handshake (asimetrično — sporo ali bezbedno):
   Browser → Server: "Zdravo, podržavam TLS 1.3"
   Server  → Browser: "Zdravo, evo mog sertifikata (javni ključ)"
   Browser → Server: "Šifrujem session key tvojim javnim ključem"
   Server dešifrovuje session key svojim privatnim ključem

2. Razmena podataka (simetrično — brzo):
   Browser ↔ Server: sav saobraćaj šifrovan session key-om (AES-256)
```

Asimetrično šifrovanje (RSA/EC) je skupo → koristi se samo za razmenu ključeva.
Simetrično (AES) je brzo → koristi se za stvarne podatke.
