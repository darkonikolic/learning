# nmap as Primary Enumeration Tool — Complete Methodology

Four-phase approach: fast scan first, then progressively deepen. Only scan hosts you own or have permission to test.

## Phase 1 — Fast Initial Scan

```bash
nmap -sV --open --min-rate 5000 target
```

Gets results in ~30 seconds. Identifies most common open ports and services.

## Phase 2 — Full TCP Scan

```bash
nmap -sV -sC -p- target -oA scans/nmap_full
```

All 65535 ports, version detection, default scripts. Run this in background while working Phase 1 results.

## Phase 3 — UDP Scan

```bash
nmap -sU --top-ports 100 target -oA scans/nmap_udp
```

Catches SNMP (161), DNS (53), TFTP (69), NTP (123). Often overlooked.

## Phase 4 — Targeted Script Scans

Run after identifying services:

```bash
nmap --script vuln target -oA scans/nmap_vuln
nmap --script smb-vuln-ms17-010,smb-enum-shares,smb-enum-users -p 445 target
nmap --script http-title,http-methods,http-auth-finder -p 80,443,8080 target
```

## Useful NSE Scripts by Service

| Service | Script |
|---------|--------|
| FTP | `ftp-anon`, `ftp-bounce` |
| SSH | `ssh-auth-methods`, `ssh-hostkey` |
| SMB | `smb-vuln-ms17-010`, `smb-enum-shares` |
| HTTP | `http-title`, `http-methods` |
| MySQL | `mysql-empty-password`, `mysql-info` |
| SNMP | `snmp-info`, `snmp-sysdescr` |

## Parse Results

```bash
# Extract open ports and services
grep "open" scans/nmap_full.nmap | awk '{print $1, $3}'

# Get just port numbers for other tools
grep "open" scans/nmap_full.gnmap | grep -oP '\d+/open' | cut -d/ -f1 | tr '\n' ','
```

## Practice

TryHackMe "Nmap" room — covers all scan types with exercises. Then run full methodology against TryHackMe "Basic Pentesting" room.
