# Networking through attacker eyes — ports, services, and misconfigs

Attackers ask five questions about every host: What ports are open? What services? What versions? Default creds? Known CVEs?

## Core recon commands

```bash
# Basic scan — top 1000 ports
nmap 192.168.56.101

# Service + version detection with default scripts
nmap -sV -sC 192.168.56.101

# All ports, aggressive
nmap -p- -T4 -A 192.168.56.101

# UDP scan (slower — common services: DNS/53, SNMP/161, NTP/123)
nmap -sU --top-ports 20 192.168.56.101
```

Run these against your own lab VMs only. Never scan hosts you don't own.

## Trust boundaries attackers think about

- Internet-facing (DMZ): web servers, mail servers, VPNs — directly reachable
- Internal network: databases, AD controllers, file shares — reached after pivot
- Localhost: services bound to 127.0.0.1 — visible only from the machine itself

## Common misconfigurations to look for

| Misconfiguration | Command to check |
|---|---|
| Anonymous FTP login | `ftp 192.168.56.101` → user: anonymous |
| Telnet instead of SSH | `telnet 192.168.56.101 23` |
| SMB null session | `smbclient -N -L //192.168.56.101` |
| Default web creds | browse to port 80/8080, try admin/admin |
| Open Redis no auth | `redis-cli -h 192.168.56.101 ping` |

## Key ports to know

| Port | Service | Why attackers care |
|---|---|---|
| 21 | FTP | anonymous login, cleartext |
| 22 | SSH | brute force, key reuse |
| 23 | Telnet | cleartext credentials |
| 80/443 | HTTP/HTTPS | web attacks |
| 445 | SMB | EternalBlue, pass-the-hash |
| 3389 | RDP | brute force, BlueKeep |
| 3306 | MySQL | direct DB access if exposed |

## Practice

TryHackMe "Network Fundamentals" rooms: https://tryhackme.com/module/network-fundamentals
