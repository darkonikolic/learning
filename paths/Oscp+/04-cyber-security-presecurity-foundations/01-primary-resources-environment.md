# Resources and lab setup — pre-security foundations

Work the TryHackMe Pre-Security path completionist-style, then build a local lab.

## Primary resources

- TryHackMe Pre-Security path: https://tryhackme.com/path/outline/presecurity (free)
- HTB Academy "Security Fundamentals": https://academy.hackthebox.com/module/details/18 (free)

## Lab VMs — VirtualBox setup

Download VirtualBox: https://www.virtualbox.org/wiki/Downloads

Create two VMs:
- Ubuntu 22.04 LTS: https://ubuntu.com/download/desktop
- Windows 10 Evaluation: https://www.microsoft.com/en-us/evalcenter/evaluate-windows-10-enterprise

Network config: each VM gets two adapters — NAT (internet access) + Host-Only (VMs talk to each other).
Take a snapshot of each VM before installing tools. Revert if something breaks.

## Kali Linux (attack VM)

Pre-built VirtualBox image: https://www.kali.org/get-kali/#kali-virtual-machines

```bash
# After first boot — update and install core tools
sudo apt update && sudo apt upgrade -y
sudo apt install -y nmap gobuster curl wget python3 python3-pip git burpsuite feroxbuster
```

## Browser DevTools

Open with F12 (or Cmd+Option+I on Mac). Go to the Network tab.
Every HTTP request your browser makes appears here — headers, cookies, response bodies.
Key actions: filter by XHR/Fetch, copy any request as curl, inspect Set-Cookie headers.

## Verify lab connectivity

```bash
# From Kali — ping your Ubuntu VM (replace with your Host-Only IP)
ping -c 4 192.168.56.101

# Scan your Ubuntu VM — Host-Only network only, never scan hosts you don't own
nmap -sV 192.168.56.101
```

## TryHackMe rooms to complete first

1. "Welcome" room (how to use TryHackMe + AttackBox)
2. "Tutorial" room (connect VPN or use AttackBox)
3. Start Pre-Security path — complete all rooms in order
