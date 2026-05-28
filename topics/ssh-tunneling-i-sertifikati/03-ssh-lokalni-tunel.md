# SSH — Lokalni tunel (Local Port Forwarding)

## Kako funkcioniše lokalni tunel?

Lokalni tunel pravi siguran kanal od **tvog računara** do nekog servisa koji je dostupan sa **SSH servera**, ali ne direktno sa tvog računara.

```
Tvoj računar          SSH Server           Cilj
───────────           ──────────           ────
localhost:8080  ────► server:22 ──────────► baza:5432
                      [SSH tunel]
```

Sintaksa:
```
ssh -L [lokalni_port]:[cilj_host]:[cilj_port] korisnik@ssh_server
```

---

## Primeri

### Pristup bazi podataka na udaljenom serveru

Baza sluša samo na `localhost` servera — ne možeš direktno da se povežeš.

```bash
# Otvori tunel: localhost:5432 → server:5432
ssh -L 5432:localhost:5432 darko@server.example.com

# U drugom terminalu — povežeš se na "lokalnu" bazu
psql -h localhost -p 5432 -U admin mojabaza

# Redis
ssh -L 6379:localhost:6379 darko@server.example.com
redis-cli -h localhost -p 6379

# MySQL
ssh -L 3306:localhost:3306 darko@server.example.com
mysql -h 127.0.0.1 -P 3306 -u root -p
```

### Pristup internoj web aplikaciji

```bash
# Intranet je dostupan samo sa office mreže, ali imaš SSH na bastion
ssh -L 8080:intranet.intern:80 darko@bastion.example.com

# Browser: http://localhost:8080 → intranet.intern:80
```

### Pristup servisu na trećem serveru (ne na SSH serveru)

```bash
# Cilj ne mora biti sam SSH server — može biti bilo koji host do kog server ima pristup
ssh -L 5432:db-server.internal:5432 darko@bastion.example.com
#                ↑
#         baza nije na bastionу, ali bastion može da je dosegne
```

### Pristup admin panelima

```bash
# Kubernetes dashboard (sluša samo interno)
ssh -L 8001:localhost:8001 darko@k8s-master.example.com

# Grafana na internom serveru
ssh -L 3000:monitoring.internal:3000 darko@bastion.example.com
# Browser: http://localhost:3000

# RabbitMQ management
ssh -L 15672:localhost:15672 darko@mq-server.example.com
# Browser: http://localhost:15672
```

---

## Background mod i trajni tuneli

```bash
# -N — ne izvršavaj komande (samo tunel)
# -f — idi u background
# -T — ne alocira TTY

ssh -N -f -T -L 5432:localhost:5432 darko@server.example.com

# Provjeri da li tunel radi
ss -tlnp | grep 5432
# ili
lsof -i :5432

# Zatvori tunel
kill $(lsof -t -i:5432)
```

---

## Tunel sa ~/.ssh/config

```
# ~/.ssh/config

Host db-tunel
    HostName server.example.com
    User darko
    LocalForward 5432 localhost:5432
    LocalForward 6379 localhost:6379
    ServerAliveInterval 30
    ExitOnForwardFailure yes
```

```bash
# Otvori oba tunela odjednom
ssh -N db-tunel &

# Zatvori
kill %1
```

---

## autossh — automatsko ponovo uspostavljanje tunela

```bash
sudo apt install autossh

# Automatski restart tunela ako pukne
autossh -M 0 -N -f \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    -L 5432:localhost:5432 \
    darko@server.example.com
```

### SystemD servis za trajni tunel

```ini
# /etc/systemd/system/ssh-db-tunnel.service
[Unit]
Description=SSH tunel za bazu podataka
After=network.target

[Service]
User=darko
ExecStart=/usr/bin/autossh -M 0 -N \
    -o "ServerAliveInterval=30" \
    -o "ServerAliveCountMax=3" \
    -o "ExitOnForwardFailure=yes" \
    -i /home/darko/.ssh/id_ed25519 \
    -L 5432:localhost:5432 \
    darko@server.example.com
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now ssh-db-tunnel
sudo systemctl status ssh-db-tunnel
```

---

## Bezbednosne napomene

- Lokalni tunel je dostupan samo na tvom računaru (127.0.0.1) — nije javno izložen
- Da biste dozvolili pristup i sa mreže: `-L 0.0.0.0:5432:localhost:5432` (oprez!)
- SSH server mora imati `AllowTcpForwarding yes` u sshd_config
