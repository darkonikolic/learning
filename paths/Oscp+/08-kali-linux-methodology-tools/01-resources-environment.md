# Kali Linux Setup and Resources

Get the VM image from kali.org/get-kali — use the pre-built VM (VMware or VirtualBox), not the installer ISO.

## Initial Setup

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install -y feroxbuster seclists gobuster ffuf nmap nikto exploitdb curl wget python3 netcat-traditional
```

Verify tools are present:

```bash
which nmap gobuster ffuf nikto curl wget python3 nc feroxbuster
```

## SecLists

```bash
sudo apt install seclists
# or clone directly:
git clone https://github.com/danielmiessler/SecLists /usr/share/seclists
```

Key paths after install:
- `/usr/share/seclists/Discovery/Web-Content/` — directory wordlists
- `/usr/share/seclists/Discovery/DNS/` — subdomain wordlists
- `/usr/share/seclists/Passwords/` — password lists
- `/usr/share/wordlists/rockyou.txt.gz` — unzip with `gunzip /usr/share/wordlists/rockyou.txt.gz`

## Courses and Platforms

- TCM Security "Practical Ethical Hacking" — paid, best bang for OSCP prep
- TryHackMe "Jr Penetration Tester" path — free, structured, beginner-friendly
- HTB Academy "Penetration Tester" job role path — free with registration
- PortSwigger Web Security Academy — free, best for web vulns

## Local Lab Targets

- Metasploitable2: download from SourceForge, run in same VM network as Kali
- DVWA: `docker run -d -p 80:80 vulnerables/web-dvwa`
- Juice Shop: `docker run -d -p 3000:3000 bkimminich/juice-shop`
- TryHackMe machines: connect via OpenVPN (`sudo openvpn ~/thm.ovpn`)
