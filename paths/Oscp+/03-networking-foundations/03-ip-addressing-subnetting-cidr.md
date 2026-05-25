# IP addressing, subnetting, and CIDR

Every nmap scan uses CIDR notation. Every network diagram has subnets. Know this cold.

## Check your own addresses

```bash
ip a                             # all interfaces, IPs, MACs
ip route                         # routing table — find default gateway
ipcalc 192.168.1.0/24            # subnet calculator (apt install ipcalc)
ipcalc 10.10.10.0/26             # shows network, broadcast, host range
```

## CIDR quick reference

| CIDR | Subnet mask | Usable hosts | Hosts count |
|------|-------------|--------------|-------------|
| /30 | 255.255.255.252 | .1 – .2 | 2 |
| /29 | 255.255.255.248 | .1 – .6 | 6 |
| /28 | 255.255.255.240 | .1 – .14 | 14 |
| /27 | 255.255.255.224 | .1 – .30 | 30 |
| /26 | 255.255.255.192 | .1 – .62 | 62 |
| /25 | 255.255.255.128 | .1 – .126 | 126 |
| /24 | 255.255.255.0 | .1 – .254 | 254 |
| /16 | 255.255.0.0 | — | 65,534 |

## RFC1918 private ranges

```
10.0.0.0/8        # 10.x.x.x — class A private
172.16.0.0/12     # 172.16.x.x – 172.31.x.x — class B private
192.168.0.0/16    # 192.168.x.x — class C private
```

## Subnet calculation exercise

For `192.168.10.0/26`:
```bash
ipcalc 192.168.10.0/26
# Network:   192.168.10.0
# Broadcast: 192.168.10.63
# First host: 192.168.10.1
# Last host:  192.168.10.62
# Hosts:     62
```

For `10.10.10.0/27`:
- Network: 10.10.10.0
- Broadcast: 10.10.10.31
- Range: 10.10.10.1 – 10.10.10.30
- Hosts: 30

## Security relevance

```bash
# Scan an entire subnet
nmap -sn 192.168.1.0/24          # ping sweep, discover live hosts
nmap -sV 10.10.10.0/24 -p 22,80,443 --open  # service scan, common ports only

# Identify your target network from VPN interface
ip a show tun0                   # HackTheBox VPN: usually 10.10.14.x
# Targets are in 10.10.10.0/24 — scan that range
```

## Practice

- Subnetting drill: https://subnettingpractice.com — do 10 problems per session
- TryHackMe "What is Networking?": https://tryhackme.com/room/whatisnetworking
- Practical Networking subnetting: https://www.practicalnetworking.net/series/subnetting/subnetting/

## Completion bar

Given any /24, /26, /27, or /28 — state the network address, broadcast, first host, last host, and host count from memory in under 30 seconds. Verify with `ipcalc`.
