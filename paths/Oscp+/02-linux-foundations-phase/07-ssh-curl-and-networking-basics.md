# SSH, curl, and networking basics

Connect to remote hosts, make HTTP requests, and understand your network interfaces. Daily tooling in every lab environment.

## SSH — connect and configure

```bash
ssh user@10.10.10.1                          # basic connect
ssh user@10.10.10.1 -p 2222                  # non-default port
ssh -i ~/.ssh/id_rsa user@host               # use specific private key
ssh -L 8080:localhost:80 user@host           # local port forward (tunnel)
ssh -D 1080 user@host                        # SOCKS proxy

# Generate a key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/lab_key  # creates lab_key + lab_key.pub
chmod 600 ~/.ssh/lab_key                     # required permission

# Copy public key to remote host
ssh-copy-id -i ~/.ssh/lab_key.pub user@host
# Or manually: cat ~/.ssh/lab_key.pub >> ~/.ssh/authorized_keys (on remote)
```

## SCP — transfer files

```bash
scp file.txt user@host:/tmp/                 # upload
scp user@host:/etc/passwd /tmp/passwd        # download
scp -r ~/loot/ user@host:/tmp/loot/          # recursive directory
scp -i ~/.ssh/lab_key file.txt user@host:/tmp/
```

## curl — make HTTP requests

```bash
curl https://example.com                     # GET request
curl -s https://example.com                  # silent (no progress bar)
curl -I https://example.com                  # headers only (HEAD request)
curl -v https://example.com 2>&1 | head -30  # verbose, see TLS + headers
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"test"}' \
     http://target/api/login
curl -b "session=abc123" http://target/admin # send cookie
curl -o /tmp/file.zip http://host/file.zip   # download to file
```

## Network interface and routing

```bash
ip a                             # all interfaces and IP addresses
ip route                         # routing table, find default gateway
ip neigh                         # ARP cache (neighbor table)
ss -tulpn                        # listening ports and their processes
```

## tmux basics — required for lab sessions

```bash
tmux new -s lab                  # start named session
# Inside tmux:
Ctrl+B %                         # split vertical
Ctrl+B "                         # split horizontal
Ctrl+B arrow                     # move between panes
Ctrl+B d                         # detach (session keeps running)
tmux attach -t lab               # reattach
```

## Lab exercise — set up SSH key auth between two VMs

```bash
# On VM1 (attacker):
ssh-keygen -t rsa -b 4096 -f ~/.ssh/lab_key -N ""
ssh-copy-id -i ~/.ssh/lab_key.pub user@VM2_IP

# Test passwordless login:
ssh -i ~/.ssh/lab_key user@VM2_IP "id && hostname"
```

## Practice

- TryHackMe "SSH" room: https://tryhackme.com/room/sshlog
- TryHackMe Linux Fundamentals Part 3: https://tryhackme.com/room/linuxfundamentalspart3

## Completion bar

Connect via SSH with a key, transfer a file with SCP, make a POST request with curl, check listening ports with `ss -tulpn` — without looking up flags.
