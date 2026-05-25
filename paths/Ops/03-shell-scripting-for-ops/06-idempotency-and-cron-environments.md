# Shell — `06` Idempotentnost i cron okruženje

**Zasto:** Ops skripte se pokreću više puta — iz CI, iz crona, ručno tokom incidenta. Skripta koja pukne na drugom pokretanju, ili koja radi lokalno ali ne u cronu, je skoro beskorisna u produkciji.

---

## Idempotentnost — check before act

Idempotentna skripta daje isti rezultat bez obzira koliko puta je pokreneš.

```bash
# NIJE idempotentno — dodaje duplikate svaki put
echo "192.168.1.10 db.internal" >> /etc/hosts

# JEST idempotentno — dodaje samo ako ne postoji
if ! grep -qF "db.internal" /etc/hosts; then
  echo "192.168.1.10 db.internal" >> /etc/hosts
fi

# mkdir — uvijek koristiti -p, tiho ako postoji
mkdir -p /opt/app/config /opt/app/logs /opt/app/data

# Instalacija paketa — idempotentno
if ! command -v nginx &>/dev/null; then
  apt-get install -y nginx
fi
# Ili jednostavnije (apt je idempotentan):
apt-get install -y nginx   # ne radi ništa ako je već instaliran

# Kreiranje usera
if ! id "appuser" &>/dev/null; then
  useradd --system --no-create-home appuser
fi

# Kopiranje config fajla — samo ako se promijenio
if ! cmp -s /tmp/nginx.conf /etc/nginx/nginx.conf; then
  cp /tmp/nginx.conf /etc/nginx/nginx.conf
  systemctl reload nginx
fi
```

---

## Cron okruženje — zašto "radi lokalno, ne u cronu"

Cron startuje minimalnu ljusku. Nema tvoj `.bashrc`, `.bash_profile`, `nvm`, `pyenv`, ni ništa što si dodao u PATH.

```bash
# Cron PATH je samo:
/usr/bin:/bin

# Tvoj interaktivni PATH može biti:
/home/user/.nvm/versions/node/v18/bin:/usr/local/bin:/usr/bin:/bin:...
```

**Rješenje 1: Postavi PATH na vrhu skripte**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Eksplicitno postavi PATH koji trebas
export PATH="/usr/local/bin:/usr/bin:/bin"

# Za docker, kubectl, helm koji su u /usr/local/bin:
export PATH="/usr/local/bin:$PATH"
```

**Rješenje 2: Koristi apsolutne putanje za kritične komande**

```bash
readonly DOCKER="/usr/bin/docker"
readonly KUBECTL="/usr/local/bin/kubectl"
readonly JQ="/usr/bin/jq"

$KUBECTL get pods    # umjesto: kubectl get pods
```

---

## Logovanje iz crona

Cron obično šalje output na email (koji niko ne čita). Uvijek preusmjeri na fajl:

```bash
# U crontabu:
0 2 * * * /opt/scripts/cleanup.sh >> /var/log/cleanup.log 2>&1

# Ili sa timestamp u logu:
0 2 * * * /opt/scripts/cleanup.sh >> /var/log/cleanup.log 2>&1; echo "Exit: $?" >> /var/log/cleanup.log
```

Unutar skripte, dodaj timestamp svim porukama:

```bash
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

log "Počinjem cleanup..."
log "Obrisano $count fajlova"
```

---

## systemd timer — moderni cron

Systemd timeri su bolji od crona jer: loguju u journald, podržavaju `Persistent=true` za propuštene pokretaje, i lakše se debuguju.

```ini
# /etc/systemd/system/cleanup.timer
[Unit]
Description=Dnevni cleanup logova

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true          # pokreni ako je propušten (server bio ugašen)

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/cleanup.service
[Unit]
Description=Log cleanup

[Service]
Type=oneshot
ExecStart=/opt/scripts/cleanup.sh
User=appuser
```

```bash
systemctl enable --now cleanup.timer
systemctl list-timers          # vidi status
journalctl -u cleanup.service  # vidi logove
```

---

## Debugging "radi lokalno, ne u CI/cronu"

```bash
# Simuliraj čisto okruženje da reproduciraš problem
env -i HOME=/root PATH=/usr/bin:/bin /bin/bash /opt/scripts/myscript.sh

# Ili u CI doda set -x da vidiš svaku komandu
bash -x /opt/scripts/myscript.sh 2>&1 | head -50
```

---

## Vjezba

Napiši skriptu `log-cleanup.sh` za cron:
- Briše log fajlove starije od `RETENTION_DAYS` (default: 7) u `LOG_DIR` (default: `/var/log/app`)
- Svaka provjera i brisanje je idempotentno — pokreni dva puta, drugi put ne radi ništa
- Na početku eksplicitno postavlja PATH
- Loguje sa timestampom: broj nađenih fajlova, broj obrisanih, ukupno oslobođen prostor
- Izlazi s kodom 0 uvijek (greška na jednom fajlu ne smije ubiti cijeli cleanup)
- Crontab linija koja ga pokreće u 3:00 svake noći i loguje output
