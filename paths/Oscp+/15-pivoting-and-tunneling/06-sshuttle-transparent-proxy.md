# sshuttle — Transparent VPN Over SSH

Easiest pivoting tool — no proxychains, no route management. Just works.

## Install

```bash
sudo apt install sshuttle -y
# Or: pip3 install sshuttle
```

## Basic Usage

```bash
# Route all traffic to 10.10.10.0/24 through pivot
sshuttle -r user@pivot_host 10.10.10.0/24

# Multiple subnets
sshuttle -r user@pivot_host 10.10.10.0/24 172.16.0.0/24

# Route everything (default gateway) through pivot — full VPN mode
sshuttle -r user@pivot_host 0.0.0.0/0
```

## With SSH Key

```bash
sshuttle -r user@pivot_host --ssh-cmd 'ssh -i ~/.ssh/id_rsa' 10.10.10.0/24
```

## Background Mode

```bash
# Run in background, write PID to file
sshuttle -r user@pivot_host 10.10.10.0/24 --daemon --pidfile /tmp/sshuttle.pid

# Kill it later
kill $(cat /tmp/sshuttle.pid)
```

## Use Without Root (limited)

```bash
# Uses --method=tproxy — requires some setup but avoids sudo
sshuttle --method=tproxy -r user@pivot_host 10.10.10.0/24
```

## After sshuttle is Running

No proxychains needed — all tools just work:

```bash
# Direct nmap including SYN scan
nmap -sV -p- 10.10.10.100

# Browser — navigate directly to internal app
firefox http://10.10.10.100/

# All standard tools work natively
nxc smb 10.10.10.0/24
curl http://10.10.10.100/
ssh user@10.10.10.200
```

## Requirements and Limitations

- Requires Python 3 on the pivot host (most Linux systems have it)
- TCP only — UDP and ICMP are not tunneled
- Requires SSH access to pivot (password or key)
- Slightly slower than ligolo-ng for large-scale scanning

## When to Use sshuttle vs Ligolo-ng

| Scenario | Use |
|---|---|
| Quick one-subnet access | sshuttle |
| Multi-hop complex networks | ligolo-ng |
| No SSH available | chisel |
| OSCP exam (time pressure) | sshuttle for speed |

## Practice

- TryHackMe "Wreath" — sshuttle used in early stages
- Any HTB machine with an internal network segment
