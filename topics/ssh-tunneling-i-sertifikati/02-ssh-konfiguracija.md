# SSH — Konfiguracija klijenta i servera

## SSH klijent konfiguracija (~/.ssh/config)

Umesto kucanja dugih komandi, definišu se aliasi za servere.

```
# ~/.ssh/config

# Globalne opcije za sve konekcije
Host *
    ServerAliveInterval 60       # šalje keepalive svakih 60s
    ServerAliveCountMax 3        # 3 neodgovorena → prekini
    AddKeysToAgent yes           # automatski dodaj ključ u agent
    IdentityFile ~/.ssh/id_ed25519

# Produkcioni server
Host prod
    HostName server.example.com  # pravi hostname ili IP
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_prod_server

# Development server (nestandardni port)
Host dev
    HostName 10.0.0.50
    User darko
    Port 2222

# Jump host (bastion) — pristup internom serveru
Host interno
    HostName 192.168.1.100
    User admin
    ProxyJump bastion

Host bastion
    HostName bastion.example.com
    User jumpuser
    IdentityFile ~/.ssh/id_bastion
```

```bash
# Bez config:
ssh -i ~/.ssh/id_prod_server -p 22 deploy@server.example.com

# Sa config:
ssh prod
```

---

## SSH server konfiguracija (/etc/ssh/sshd_config)

```bash
sudo nano /etc/ssh/sshd_config
```

### Ključne bezbednosne opcije

```
# ── Autentifikacija ──────────────────────────────────────────
# Dozvoli/zabrani autentifikaciju lozinkom
PasswordAuthentication no           # ISKLJUČI kad postaviš ključeve!
PubkeyAuthentication yes            # Dozvoli key-based auth
AuthorizedKeysFile .ssh/authorized_keys

# Zabrani root login (koristiti sudo)
PermitRootLogin no
# Ako mora root pristup — dozvoli samo sa ključem:
# PermitRootLogin prohibit-password

# ── Mrežne opcije ────────────────────────────────────────────
Port 22                             # promeni na nestandardni (npr. 2222)
ListenAddress 0.0.0.0               # IP na kom sluša (0.0.0.0 = sve)
AddressFamily inet                  # inet = IPv4, inet6 = IPv6, any = oba

# ── Sesija ───────────────────────────────────────────────────
LoginGraceTime 30                   # sekundi za unos kredencijala
MaxAuthTries 3                      # max pokušaji autentifikacije
MaxSessions 10                      # max sesija po konekciji

# ── Keep-alive ───────────────────────────────────────────────
ClientAliveInterval 300             # šalje keepalive svakih 5 min
ClientAliveCountMax 2               # 2 bez odgovora → prekini

# ── Restrikcije ──────────────────────────────────────────────
AllowUsers darko deploy             # samo ovi korisnici smeju SSH
# DenyUsers baduser
# AllowGroups sshusers admins

# ── Forwarding ───────────────────────────────────────────────
AllowTcpForwarding yes              # potrebno za tunele!
X11Forwarding no                    # GUI prosleđivanje — obično nije potrebno
```

```bash
# Testiraj konfiguraciju pre restarta!
sudo sshd -t

# Primeni izmene
sudo systemctl reload sshd
```

---

## Zabrana login lozinkom (preporučeni redosled)

```bash
# 1. Prvo postavi ključeve i provjeri da radi
ssh korisnik@server  # mora da se poveže bez lozinke

# 2. Tek onda isključi lozinke
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no

# 3. Reload
sudo systemctl reload sshd

# 4. U NOVOM terminalu provjeri da možeš login sa ključem
ssh korisnik@server

# Tek kad si siguran — zatvori staru sesiju
```

---

## Dozvola samo određenim korisnicima iz grupe

```bash
# Kreiraj grupu za SSH pristup
sudo groupadd sshusers
sudo usermod -aG sshusers darko
sudo usermod -aG sshusers deploy

# /etc/ssh/sshd_config
# AllowGroups sshusers
```

---

## Two-Factor autentifikacija (2FA)

```bash
sudo apt install libpam-google-authenticator

# Za svakog korisnika koji želi 2FA
google-authenticator
# Skenira QR kod u Google Authenticator aplikaciji

# /etc/pam.d/sshd — dodaj na vrh
# auth required pam_google_authenticator.so

# /etc/ssh/sshd_config
# KbdInteractiveAuthentication yes
# AuthenticationMethods publickey,keyboard-interactive
```

---

## Prenos fajlova

```bash
# SCP — kopiranje fajlova
scp fajl.txt darko@server:/tmp/
scp -r /lokalni/folder darko@server:/udaljeni/folder/
scp darko@server:/etc/nginx/nginx.conf ~/nginx-backup.conf

# Koristi config alias
scp fajl.txt prod:/tmp/

# SFTP — interaktivni transfer
sftp darko@server
sftp> ls
sftp> get remote-file.txt
sftp> put local-file.txt /remote/path/
sftp> exit

# rsync — sinhronizacija (brži, prenosi samo promene)
rsync -avz /lokalni/dir/ darko@server:/udaljeni/dir/
rsync -avz --delete /lokalni/ darko@server:/udaljeni/  # briši stare fajlove
rsync -avz -e "ssh -i ~/.ssh/id_ed25519 -p 2222" /lokalni/ darko@server:/udaljeni/
```
