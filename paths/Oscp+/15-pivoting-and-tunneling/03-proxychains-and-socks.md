# Proxychains and SOCKS Routing

Route your tools through a SOCKS proxy into an internal network segment.

## Configure Proxychains

```bash
sudo nano /etc/proxychains4.conf

# At the bottom, set your proxy (replace or add):
socks5  127.0.0.1  1080

# Optional: comment out proxy_dns if causing issues
# proxy_dns
```

## Set Up the SOCKS Proxy

```bash
# SSH dynamic forwarding — creates SOCKS5 on port 1080
ssh -N -D 1080 user@pivot_host

# Or use chisel (see 04-chisel-tunneling.md) — same result
```

## Route Tools Through Proxychains

```bash
# Nmap — MUST use -sT (TCP connect) and -Pn — raw sockets don't work
proxychains nmap -sT -Pn -p 22,80,443,445,3389 10.10.10.100

# Subnet sweep (slow but works)
proxychains nmap -sT -Pn -p 80,443,445 10.10.10.0/24

# NetExec / CME through proxy
proxychains nxc smb 10.10.10.5 -u admin -p 'Password123'

# curl to verify internal web app
proxychains curl http://172.16.0.100/

# Evil-WinRM through proxy
proxychains evil-winrm -i 10.10.10.100 -u Administrator -p 'Pass123'

# SSH through proxy (hop again)
proxychains ssh user@172.16.0.200
```

## Verify the Chain is Working

```bash
# Should show internal target's response
proxychains curl -s http://10.10.10.100 | head -20

# Test DNS resolution through proxy
proxychains nslookup internal.corp 10.10.10.1
```

## Proxychains4 Config Options

```bash
# Dynamic chain — skips dead proxies
dynamic_chain

# Strict chain — every proxy must work (good for multi-hop)
strict_chain

# Chain multiple SOCKS proxies for multi-hop
socks5  127.0.0.1  1080   # first hop
socks5  127.0.0.1  2080   # second hop
```

## Key Limitations

- ICMP (ping) does not work through proxychains — always use `-Pn` with nmap
- `-sS` (SYN scan) does not work — use `-sT` only
- UDP is unreliable through SOCKS5
- Speed is slow — target specific ports, not full port ranges

## Practice

- TryHackMe "Wreath" — proxychains used throughout
- HTB Academy Pivoting module — exercises use proxychains with nmap and nxc
