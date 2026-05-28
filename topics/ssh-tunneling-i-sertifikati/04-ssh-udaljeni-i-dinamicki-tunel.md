# SSH — Udaljeni tunel i dinamički tunel (SOCKS proxy)

## Udaljeni tunel (Remote Port Forwarding)

Udaljeni tunel radi **obrnuto** od lokalnog — izlaže servis sa **tvog računara** na **SSH serveru**, dostupan spoljnom svetu.

```
Spoljni korisnik      SSH Server             Tvoj računar
────────────────      ──────────             ────────────
                      server:8080  ◄──────── localhost:3000
                      [javno dostupan]       [tvoja lokalna app]
```

Sintaksa:
```
ssh -R [udaljeni_port]:[lokalni_host]:[lokalni_port] korisnik@ssh_server
```

---

### Primeri

```bash
# Izloži svoju lokalnu app (port 3000) na serveru na portu 8080
ssh -R 8080:localhost:3000 darko@server.example.com

# Neko sa interneta može da pristupi:
# http://server.example.com:8080 → tvoj localhost:3000

# Testiranje webhooka sa lokalnog razvoja
# GitHub/Stripe šalje webhook na tvoj server, ti hvatasz lokalno
ssh -R 9000:localhost:3000 darko@server.example.com
```

---

### GatewayPorts — dostupnost sa mreže

Po defaultu, udaljeni tunel sluša samo na `127.0.0.1` servera.
Da bude dostupan sa cele mreže:

```bash
# /etc/ssh/sshd_config na serveru
GatewayPorts yes
# ili za veću kontrolu:
GatewayPorts clientspecified

# Klijent tada specificira:
ssh -R 0.0.0.0:8080:localhost:3000 darko@server.example.com
#     ↑ sluša na svim interfejsima servera
```

---

### Reverse SSH — pristup NAT-ovanom računaru

Scenarijo: server (S) je iza NAT-a (nema javni IP), a treba ti pristup sa svog računara (A).

```
A (tvoj računar)          S (iza NAT-a)
─────────────────         ─────────────
                          S → ssh -R 2222:localhost:22 darko@jump.example.com
                          (S se konektuje PREMA van)

A → ssh -p 2222 localhost -J darko@jump.example.com
    (A prolazi kroz jump server)
```

```bash
# Na S (serveru iza NAT-a) — uspostavi stalni tunel
autossh -M 0 -N -f \
    -o "ServerAliveInterval=30" \
    -R 2222:localhost:22 \
    darko@jump.example.com

# Sa A — spoji se na S kroz jump server
ssh -J darko@jump.example.com -p 2222 korisnik@localhost
```

---

## Dinamički tunel — SOCKS5 proxy

Dinamički tunel pretvara SSH vezu u **SOCKS5 proxy** — sav browser saobraćaj ide kroz SSH server.

```
Browser/aplikacija     Tvoj računar          SSH Server
──────────────────     ────────────          ──────────
HTTP/HTTPS zahtev ──► SOCKS:1080 ──────────► server.example.com
                       [tunel]               │
                                             └──► internet
```

Sintaksa:
```
ssh -D [lokalni_socks_port] korisnik@ssh_server
```

```bash
# Otvori SOCKS5 proxy na portu 1080
ssh -D 1080 -N -f darko@server.example.com

# Provjeri
ss -tlnp | grep 1080
```

---

### Podešavanje browser-a za SOCKS proxy

**Firefox:**
- Settings → Network Settings → Manual proxy → SOCKS Host: `127.0.0.1`, Port: `1080`
- SOCKS v5, "Proxy DNS when using SOCKS v5" → obavezno!

**Chrome (sa komandne linije):**
```bash
google-chrome --proxy-server="socks5://127.0.0.1:1080" --proxy-bypass-list="localhost"
```

---

### Korišćenje curl/wget sa SOCKS proxy-jem

```bash
# curl
curl --socks5 127.0.0.1:1080 https://api.example.com

# curl sa DNS kroz proxy (sprečava DNS leak)
curl --socks5-hostname 127.0.0.1:1080 https://api.example.com

# wget
wget -e "https_proxy=socks5://127.0.0.1:1080" https://example.com
```

---

### Proxychains — sav CLI saobraćaj kroz proxy

```bash
sudo apt install proxychains4
sudo nano /etc/proxychains4.conf
# Na dnu:
# socks5 127.0.0.1 1080

# Pokreni bilo koji alat kroz proxy
proxychains ssh korisnik@internal-server.internal
proxychains nmap -sT -p 80,443 10.0.0.0/24
proxychains curl https://api.example.com
```

---

## Jump host (ProxyJump)

Pristup serveru koji nije direktno dostupan — preskočiti ga kroz međuserver.

```bash
# Jedan jump host
ssh -J darko@bastion.example.com admin@db.internal

# Više jump hostova
ssh -J user@hop1,user@hop2 admin@final-server.internal

# U ~/.ssh/config
Host db-interno
    HostName db.internal
    User admin
    ProxyJump darko@bastion.example.com

# Korišćenje
ssh db-interno
```

---

## Pregled SSH tunneling tipova

| Tip | Opcija | Smer | Tipična upotreba |
|-----|--------|------|-----------------|
| Lokalni | `-L local:host:remote` | Server → tvoj PC | Pristup internim servisima |
| Udaljeni | `-R remote:host:local` | Tvoj PC → Server | Expose lokalne app na internet |
| Dinamički | `-D port` | SOCKS proxy | Bezbedno browsanje kroz SSH server |
| Jump | `-J bastion host` | Prolazni server | Višestepeni pristup |
