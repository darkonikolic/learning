# nmap Methodology — All Scan Types

Only scan hosts you own or have explicit written permission to test. Practice on Metasploitable2 locally.

## Scan Progression

Quick scan — run first, fast results:

```bash
nmap -sV --open target
```

Full scan — all ports, version detection, default scripts:

```bash
nmap -sV -sC -p- target -oA scans/full_scan
```

UDP scan — often missed, catches SNMP/DNS/TFTP:

```bash
nmap -sU --top-ports 20 target
```

OSCP methodology start (balances speed vs coverage):

```bash
nmap -sV -sC -p 1-10000 target -oA scans/initial
```

## Output Formats

`-oA` saves three files: `.nmap` (text), `.gnmap` (greppable), `.xml` (importable).

Parse open ports from saved output:

```bash
grep "open" scans/full_scan.nmap
grep "open" scans/full_scan.gnmap | awk '{print $2, $5}'
```

## NSE Scripts

Run vulnerability scripts:

```bash
nmap --script vuln target
```

Specific script examples:

```bash
nmap --script smb-vuln-ms17-010 -p 445 target
nmap --script ftp-anon -p 21 target
nmap --script http-title -p 80,443,8080 target
nmap --script ssh-auth-methods -p 22 target
nmap --script mysql-empty-password -p 3306 target
```

## Common Flags

| Flag | Purpose |
|------|---------|
| `-sV` | Service version detection |
| `-sC` | Default NSE scripts |
| `-p-` | All 65535 ports |
| `-oA` | Output all formats |
| `--open` | Show only open ports |
| `--min-rate 5000` | Speed up scan |

## Practice Target

Metasploitable2 local VM — run `nmap -sV -sC -p- <metasploitable_ip> -oA scans/meta2` and enumerate every service found.
