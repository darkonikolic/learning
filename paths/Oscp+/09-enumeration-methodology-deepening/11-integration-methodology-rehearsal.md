# Full Enumeration Chain Drill — Time-Boxed

Run this drill on TryHackMe "Basic Pentesting", "Mr Robot", or HTB "Blue". Target time: 45 minutes for enumeration phase only.

## Setup

```bash
TARGET=10.10.10.x
mkdir -p ~/labs/$TARGET/{recon,scans,exploit,loot}
```

## Step 1 — Start Full nmap (background)

```bash
nmap -sV -sC -p- $TARGET -oA ~/labs/$TARGET/scans/nmap_full &
```

## Step 2 — While nmap Runs: Quick Pass

```bash
# Quick scan for common ports
nmap -sV --open --min-rate 5000 $TARGET

# If 80/443 found immediately:
curl -I http://$TARGET
curl http://$TARGET/robots.txt
```

## Step 3 — Review Full nmap Results

```bash
grep "open" ~/labs/$TARGET/scans/nmap_full.nmap
```

## Step 4 — Per-Service Enumeration

HTTP (80/443/8080):

```bash
gobuster dir -u http://$TARGET -w /usr/share/wordlists/dirb/common.txt -x php,txt,html -t 40
nikto -h http://$TARGET -o ~/labs/$TARGET/scans/nikto.txt
```

SMB (445):

```bash
smbclient -L //$TARGET -N
nxc smb $TARGET -u '' -p '' --shares
nmap --script smb-vuln-ms17-010 -p 445 $TARGET
```

FTP (21):

```bash
ftp $TARGET
# user: anonymous, pass: (blank)
```

SNMP (161/UDP):

```bash
nmap -sU -p 161 $TARGET && snmpwalk -v2c -c public $TARGET
```

## Step 5 — Search Exploits

```bash
# For each service + version found:
searchsploit vsftpd 2.3.4
searchsploit "apache 2.4.49"
searchsploit samba 3.x
```

## Step 6 — Document All Findings

```bash
cat > ~/labs/$TARGET/recon/summary.md << 'EOF'
| Port | Service | Version | Notes | Exploitable? |
|------|---------|---------|-------|--------------|
EOF
# Fill in manually from nmap output
```

## Step 7 — Identify Top 2-3 Attack Vectors

Before leaving enumeration phase, write down:
1. Most likely initial access vector (specific CVE or technique)
2. Backup vector if first fails
3. Any credentials or usernames found

## Time Checkpoint

- 0:00 — Start full nmap, run quick scan in parallel
- 0:10 — First services identified, begin service-specific enum
- 0:30 — All services enumerated, exploit search done
- 0:45 — Summary written, attack vectors identified
