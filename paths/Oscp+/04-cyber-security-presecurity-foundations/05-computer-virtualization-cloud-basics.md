# VMs, containers, and cloud — lab setup and security context

VMs isolate your attack lab. Containers let you spin up vulnerable apps in seconds.

## VirtualBox setup

1. Download VirtualBox: https://www.virtualbox.org/wiki/Downloads
2. Download Ubuntu 22.04 ISO: https://ubuntu.com/download/desktop
3. New VM → Linux → Ubuntu 64-bit → 2GB RAM → 20GB disk → NAT + Host-Only adapters
4. Boot from ISO → install → take snapshot named "Clean install"

Always snapshot before anything destructive. Revert with: Machine → Restore Snapshot.

## Docker — run vulnerable apps instantly

```bash
# Install Docker on Ubuntu
sudo apt install -y docker.io
sudo usermod -aG docker $USER  # log out and back in

# Juice Shop — OWASP vulnerable web app (covers all OWASP Top 10)
docker run -d -p 3000:3000 bkimminich/juice-shop
# Browse to http://localhost:3000

# DVWA — Damn Vulnerable Web Application
docker run -d -p 80:80 vulnerables/web-dvwa
# Browse to http://localhost → admin/password → setup DB

# nginx — test a normal server
docker run -d -p 8080:80 nginx

# Useful docker commands
docker ps                           # list running containers
docker exec -it <container_id> bash # shell inside container
docker stop <container_id>          # stop container
docker rm <container_id>            # remove container
```

## Cloud basics — AWS free tier

AWS free tier gives 750 hours/month of t2.micro EC2: https://aws.amazon.com/free

Security groups in AWS = firewall rules. Inbound rule `0.0.0.0/0 port 22` = anyone can try to SSH in.
Default mistake: leaving security groups wide open. Always restrict to your IP.

```bash
# Check which IP AWS thinks you are
curl ifconfig.me

# Harden SSH — disable password auth, use keys only
# /etc/ssh/sshd_config:
# PasswordAuthentication no
# PubkeyAuthentication yes
```

## Snapshots vs containers — when to use what

- Snapshot (VM): full OS state saved, expensive in disk space, great for lab rollback
- Docker container: app-level isolation, fast spin-up, no kernel isolation, fine for vulnerable app labs
