# Full Reconnaissance Chain on a Target

Practice this chain on Metasploitable2 (local VM) or TryHackMe "Basic Pentesting" room. Goal: complete in under 45 minutes.

## Setup

```bash
# Create target workspace
mkdir -p ~/labs/target/{recon,exploit,loot,report}
TARGET=10.10.10.5   # replace with actual IP
```

## Step 1 — nmap

```bash
nmap -sV -sC -p- $TARGET -oA ~/labs/target/recon/nmap_full
```

While waiting, start quick scan in another tmux pane:

```bash
nmap -sV --open --min-rate 5000 $TARGET
```

## Step 2 — Web (if port 80/443/8080 found)

```bash
curl -I http://$TARGET
curl http://$TARGET/robots.txt
gobuster dir -u http://$TARGET -w /usr/share/wordlists/dirb/common.txt -x php,txt,html -t 40
nikto -h http://$TARGET
```

## Step 3 — SMB (if port 445 found)

```bash
smbclient -L //$TARGET -N
nmap --script smb-vuln-ms17-010 -p 445 $TARGET
```

## Step 4 — FTP (if port 21 found)

```bash
ftp $TARGET
# user: anonymous, password: (blank or email)
```

## Step 5 — Search Exploits

```bash
# After identifying service versions from nmap output:
searchsploit vsftpd 2.3.4
searchsploit "UnrealIRCd"
searchsploit apache 2.2
```

## Step 6 — SNMP (if port 161/UDP found)

```bash
nmap -sU -p 161 $TARGET
snmpwalk -v2c -c public $TARGET
```

## Step 7 — Document Findings

Create a table in `~/labs/target/report/notes.md`:

```
| Port | Service     | Version       | Notes              | Exploitable? |
|------|-------------|---------------|--------------------|--------------|
| 21   | FTP         | vsftpd 2.3.4  | anonymous login OK | YES - MS08   |
| 80   | HTTP        | Apache 2.2.8  | DVWA running       | YES - SQLi   |
| 445  | SMB         | Samba 3.x     | MS17-010 check     | MAYBE        |
```

## Step 8 — Identify Attack Vector

Pick the 2-3 most promising findings and note the specific exploit or technique to try next.
