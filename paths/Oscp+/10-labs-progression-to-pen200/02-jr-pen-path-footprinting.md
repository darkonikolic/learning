# TryHackMe Jr Pentester Path — Recon Modules

Path URL: tryhackme.com/path/outline/jrpenetrationtester

Complete this path before moving to unguided HTB boxes.

## Priority Modules

Work these in order:
1. Passive Reconnaissance
2. Active Reconnaissance
3. Nmap
4. Content Discovery
5. Subdomain Enumeration
6. Vulnerability Research

## Passive Recon Commands

```bash
whois target.com
dig target.com ANY
dig target.com MX
dig target.com NS
theHarvester -d target.com -b google
theHarvester -d target.com -b bing,linkedin,google
```

Shodan: shodan.io — search `hostname:target.com` or `net:IP_RANGE`
Censys: search.censys.io — search by IP, hostname, or cert CN

## Active Recon Commands

```bash
# Full port scan
nmap -sV -sC -p- -T4 target

# UDP top ports
nmap -sU --top-ports 20 target

# OS detection
nmap -O target

# Traceroute
traceroute target
```

Burp Suite passive crawl: set as proxy, browse target, review Site Map.

## How to Use Each Room

Don't just click through. For every room:
1. Complete the guided exercise with the room's target
2. Redo the same commands on your own local VM from memory
3. Write down every new command you encountered

## Completion Signal

You're ready for HTB Easy when you can run a full passive + active recon on a new target in under 20 minutes without referencing notes.
