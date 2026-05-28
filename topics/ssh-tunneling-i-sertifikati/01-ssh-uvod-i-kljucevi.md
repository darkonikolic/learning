# SSH — Uvod i ključevi

## Šta je SSH?

**SSH** (Secure Shell) je kriptografski mrežni protokol za bezbednu komunikaciju sa udaljenim sistemima. Zamenjuje nesigurne protokole: Telnet, rsh, rcp.

```
Bez SSH (Telnet):
  Klijent ──[plain text: lozinka, komande, podaci]──► Server
  (svako na mreži može da vidi sve!)

Sa SSH:
  Klijent ──[šifrovano: TLS + asimetična kriptografija]──► Server
```

Port: **22** (TCP)

## Dva načina autentifikacije

| Način | Opis | Bezbednost |
|-------|------|------------|
| **Lozinka** | Korisnik unosi lozinku | Slabija — podložna brute-force napadima |
| **SSH ključevi** | Par privatni/javni ključ | Mnogo jača — matematički nemoguće pogoditi |

---

## Generisanje SSH ključeva

```bash
# ED25519 — preporučeno (moderni, brži, manji, bezbedniji)
ssh-keygen -t ed25519 -C "darko@firma.rs"

# RSA 4096 — za starije sisteme koji ne podržavaju ED25519
ssh-keygen -t rsa -b 4096 -C "darko@firma.rs"

# Sa custom imenom fajla (npr. za specifičan server)
ssh-keygen -t ed25519 -f ~/.ssh/id_prod_server -C "produkcioni server"
```

Tokom generisanja pita za **passphrase** — dodatna zaštita privatnog ključa. Preporučeno koristiti, posebno za ključeve koji pristupaju produkciji.

## Gde se čuvaju ključevi?

```
~/.ssh/
├── id_ed25519          ← PRIVATNI ključ (NIKAD ne deliti!)
├── id_ed25519.pub      ← Javni ključ (kopira se na server)
├── id_rsa              ← RSA privatni ključ (stariji format)
├── id_rsa.pub          ← RSA javni ključ
├── authorized_keys     ← Javni ključevi koji smeju da se loguju
├── known_hosts         ← Fingerprinti poznatih servera
└── config              ← SSH klijent konfiguracija
```

## Kopiranje javnog ključa na server

```bash
# Automatski (preporučeno)
ssh-copy-id -i ~/.ssh/id_ed25519.pub korisnik@server.example.com

# Ručno (kad ssh-copy-id nije dostupan)
cat ~/.ssh/id_ed25519.pub | ssh korisnik@server.example.com \
    "mkdir -p ~/.ssh && chmod 700 ~/.ssh && \
     cat >> ~/.ssh/authorized_keys && \
     chmod 600 ~/.ssh/authorized_keys"

# Provjera da li ključ radi
ssh -i ~/.ssh/id_ed25519 korisnik@server.example.com
```

## Struktura javnog ključa

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBhW... darko@firma.rs
│           │                               │
tip ključa  ključ (base64)                  komentar
```

Sadržaj `~/.ssh/authorized_keys` — jedan ključ po redu:
```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBhW... darko@firma.rs
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDkX... darko@laptop
```

## Prava fajlova — kritično!

SSH odbija rad ako su prava preširoka.

```bash
chmod 700 ~/.ssh                      # direktorijum
chmod 600 ~/.ssh/id_ed25519           # privatni ključ
chmod 644 ~/.ssh/id_ed25519.pub       # javni ključ
chmod 600 ~/.ssh/authorized_keys      # authorized_keys
chmod 600 ~/.ssh/config               # config fajl

# Proveri prava
ls -la ~/.ssh/
```

## SSH Agent — ne kucaj passphrase stalno

SSH agent čuva otključane ključeve u memoriji za trajanje sesije.

```bash
# Pokreni agent
eval "$(ssh-agent -s)"

# Dodaj ključ (pita passphrase jednom)
ssh-add ~/.ssh/id_ed25519

# Prikaži učitane ključeve
ssh-add -l

# Ukloni ključ iz agenta
ssh-add -d ~/.ssh/id_ed25519

# Ukloni sve ključeve
ssh-add -D
```

### Automatski pokretanje agenta (~/.bashrc ili ~/.zshrc)

```bash
# Pokreni agent samo ako već ne radi
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)"
    ssh-add ~/.ssh/id_ed25519 2>/dev/null
fi
```

## Fingerprint servera

Prilikom prvog spajanja na server, SSH prikazuje fingerprint:

```
The authenticity of host 'server.example.com (1.2.3.4)' can't be established.
ED25519 key fingerprint is SHA256:abc123...
Are you sure you want to continue connecting (yes/no)?
```

Fingerprint se pamti u `~/.ssh/known_hosts`. Ako se promeni → SSH upozorenje (potencijalni MITM napad).

```bash
# Prikaži fingerprint servera
ssh-keygen -l -f /etc/ssh/ssh_host_ed25519_key.pub

# Ukloni stari fingerprint (npr. nakon reinstalacije servera)
ssh-keygen -R server.example.com
```
