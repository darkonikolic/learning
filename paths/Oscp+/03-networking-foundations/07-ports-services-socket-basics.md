# Ports, services, and socket basics

Every pentest starts with port scanning. Know what runs where and how to interact with raw sockets.

## Check what is listening locally

```bash
ss -tulpn                        # TCP+UDP listeners with process names (modern)
netstat -tulpn                   # same, older syntax (may need net-tools installed)
sudo lsof -i -P -n | grep LISTEN # via lsof
sudo nmap -sV localhost           # version scan of local services
```

## Common ports reference

| Port | Service | Notes |
|------|---------|-------|
| 21 | FTP | Often anonymous login, check |
| 22 | SSH | Version matters for exploits |
| 23 | Telnet | Plaintext — capture credentials |
| 25 | SMTP | Mail relay, user enumeration |
| 53 | DNS | UDP+TCP, zone transfer on TCP |
| 80 | HTTP | Start web enum here |
| 110 | POP3 | Email retrieval |
| 139/445 | SMB | File shares, EternalBlue, null sessions |
| 443 | HTTPS | Same as 80 + TLS |
| 3306 | MySQL | Direct DB access if exposed |
| 3389 | RDP | Windows remote desktop |
| 5985 | WinRM | Windows remote management |
| 8080 | HTTP-alt | Dev servers, proxies |

## Netcat — raw socket tool

```bash
# Listen on a port
nc -lvnp 4444                    # listen, verbose, no DNS, port 4444

# Connect to a port
nc 10.10.10.1 80                 # connect to host:port

# Banner grabbing — identify service version
nc -w 3 10.10.10.1 22            # -w 3: timeout 3s; SSH banner appears
nc -w 3 10.10.10.1 21            # FTP banner
nc -w 3 10.10.10.1 80
  GET / HTTP/1.0
  (press Enter twice)

# Send file
nc -lvnp 4444 > received.txt     # receiver
nc 10.10.10.1 4444 < file.txt    # sender
```

## nmap — service fingerprinting

```bash
nmap -sV 10.10.10.1              # version detection
nmap -sV -p 21,22,80,443 target  # specific ports only
nmap -sV --open 10.10.10.0/24    # scan subnet, show only open ports
nmap -sC -sV target              # default scripts + version
sudo nmap -sS target             # SYN scan (stealth, requires root)
sudo nmap -sU -p 53,161 target   # UDP scan (DNS, SNMP)
```

## Lab exercise — banner grab three services

```bash
# Start services locally for practice
sudo systemctl start ssh
python3 -m http.server 80 &

# Banner grab
nc -w 3 localhost 22    # SSH banner: SSH-2.0-OpenSSH_8.9...
nc -w 3 localhost 80    # HTTP server response

# Cross-reference with nmap
nmap -sV -p 22,80 localhost
```

## Practice

- TryHackMe "Nmap": https://tryhackme.com/room/furthernmap
- TryHackMe "Network Services": https://tryhackme.com/room/networkservices
- GTFOBins for netcat privesc: https://gtfobins.github.io/gtfobins/nc/

## Completion bar

From memory: check local listeners with `ss -tulpn`, banner-grab a service with `nc`, run an nmap version scan, identify a service from its banner — without looking up flags.
