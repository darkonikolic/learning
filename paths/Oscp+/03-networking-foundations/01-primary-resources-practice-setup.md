# Networking foundations — resources and lab setup

Networking for security: focus on what you need to enumerate, pivot, and understand traffic — not CCNA exam prep.

## Install tools first

```bash
sudo apt update
sudo apt install -y wireshark tcpdump nmap traceroute dnsutils netcat-openbsd curl ipcalc mtr
# Add your user to wireshark group (capture without root)
sudo usermod -aG wireshark $USER
newgrp wireshark
```

## Resources

| Resource | What it covers | URL |
|----------|---------------|-----|
| Practical Networking | OSI, TCP/IP, subnetting, routing — best free content | https://www.practicalnetworking.net |
| TryHackMe Pre-Security path | Network fundamentals with hands-on rooms | https://tryhackme.com/path/outline/presecurity |
| TryHackMe Network Fundamentals | Deeper dive with packet analysis | https://tryhackme.com/module/network-fundamentals |
| NetworkChuck YouTube | Visual explanations of subnetting, routing, DNS | https://www.youtube.com/@NetworkChuck |
| Wireshark docs | Filter reference | https://www.wireshark.org/docs/wsug_html_chunked/ |
| Subnetting practice | Daily drill | https://subnettingpractice.com |

## Lab environment options

Option A — local VM (recommended):
- Ubuntu 22.04 or Kali Linux VM in VirtualBox/VMware
- Two VMs on host-only network for traffic capture between them

Option B — TryHackMe browser:
- No local setup needed
- Covers all rooms in this phase

## Verify your tools work

```bash
ping -c 2 8.8.8.8
traceroute google.com
nmap -sV localhost
dig google.com
sudo tcpdump -i any -c 5
wireshark &   # opens GUI
```

## Phase exit goal

By the end of this phase you can: read a Wireshark capture and identify what happened, subnet a /24 without a calculator, explain DNS query flow, run nmap and interpret results.
