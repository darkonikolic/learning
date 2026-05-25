# Reconnaissance Tools

Find what's exposed before you touch it. All recon must be against systems you own or have explicit written authorization to test.

## Resources

- Shodan: https://shodan.io
- theHarvester: https://github.com/laramies/theHarvester
- Amass: https://github.com/owasp-amass/amass
- SecLists: https://github.com/danielmiessler/SecLists

## Nmap

```bash
# Quick scan — top 1000 ports
nmap -sC -sV target -oA nmap-quick

# Full TCP port scan
nmap -sC -sV -p- target -oA nmap-full

# UDP scan (top 100)
nmap -sU --top-ports 100 target

# Vuln scripts
nmap --script vuln target

# OS detection + aggressive
nmap -A target

# Scan subnet, output all formats
nmap -sC -sV 192.168.1.0/24 -oA nmap-subnet
```

## Masscan (Fast — Large Ranges)

```bash
# Install
apt install masscan

# Scan entire subnet for web ports
masscan 192.168.1.0/24 -p80,443,8080,8443 --rate=1000

# Scan large range fast
masscan 10.0.0.0/8 -p22,80,443,3389 --rate=5000 -oG masscan-out.txt

# Pipe into Nmap for service detection
masscan 10.0.0.0/24 -p- --rate=1000 | awk '{print $6}' | \
  xargs -I{} nmap -sC -sV -p- {}
```

## Shodan (Internet Exposure)

```bash
# Install CLI
pip install shodan
shodan init <API_KEY>

# Search for exposed services
shodan search "apache 2.4" org:"Target Company"
shodan search 'hostname:target.com port:22'
shodan search 'ssl.cert.subject.cn:target.com'

# Host info
shodan host 1.2.3.4

# Download results
shodan download results 'org:"Target Corp"'
shodan parse --fields ip_str,port,transport results.json.gz
```

## theHarvester (OSINT — Email, Subdomains)

```bash
# Basic search across sources
theHarvester -d target.com -b google,bing,linkedin,dnsdumpster

# All sources
theHarvester -d target.com -b all

# Save results
theHarvester -d target.com -b google,linkedin -f harvest-results
```

## Amass (Subdomain Enumeration)

```bash
# Passive enumeration (OSINT only)
amass enum -passive -d target.com

# Active enumeration (DNS brute force)
amass enum -d target.com -brute -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# Intel — find related ASNs and CIDRs
amass intel -org "Target Corporation"

# Visualize
amass viz -d3 -d target.com
```

## Subfinder (Fast Passive Subdomain Discovery)

```bash
# Install
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Basic run
subfinder -d target.com

# All sources, verbose
subfinder -d target.com -all -v

# Output to file, pipe to httpx
subfinder -d target.com -o subs.txt
cat subs.txt | httpx -status-code -title -tech-detect
```

## DNSx (DNS Resolution + Enumeration)

```bash
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Resolve list of subdomains
cat subs.txt | dnsx -resp

# Brute force subdomains
dnsx -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

## Recon-ng (Modular OSINT Framework)

```bash
recon-ng
> marketplace install all
> workspaces create target_com
> modules load recon/domains-hosts/bing_domain_web
> options set SOURCE target.com
> run
> show hosts
```

## Ethical Note

Passive recon (Shodan queries, public DNS lookups) is generally lower risk but check your scope. Active scanning (Nmap, Masscan against live systems) requires explicit written authorization. Never scan systems not in scope.
