# gobuster and Recursive Directory Discovery

gobuster for targeted scans, feroxbuster when you need recursive depth.

## gobuster — Standard Directory Scan

```bash
gobuster dir -u http://target \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -x php,asp,aspx,txt,html,bak,old,zip \
  -t 40 \
  -o scans/gobuster.txt
```

## gobuster — DNS Subdomain Enumeration

```bash
gobuster dns -d target.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt \
  -t 50
```

## gobuster — Vhost Enumeration

```bash
gobuster vhost -u http://target.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```

## feroxbuster — Recursive Discovery

feroxbuster automatically recurses into found directories:

```bash
sudo apt install feroxbuster

feroxbuster -u http://target \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -x php,html,txt \
  -r \
  -o scans/ferox.txt
```

Limit recursion depth:

```bash
feroxbuster -u http://target -w wordlist.txt -d 3
```

Filter status codes:

```bash
feroxbuster -u http://target -w wordlist.txt -C 404,403,302
```

## Wordlist Selection

| Wordlist | Speed | Coverage |
|----------|-------|----------|
| `dirb/common.txt` | Fast | Low |
| `raft-medium-directories.txt` | Medium | Good |
| `directory-list-2.3-medium.txt` | Slow | High |
| `directory-list-2.3-big.txt` | Very slow | Very high |

## When to Use Each Tool

- gobuster: quick targeted scan, DNS/vhost enumeration
- feroxbuster: webapp with many nested directories, need recursion
- ffuf: parameter and header fuzzing, more filter options

## Practice

TryHackMe "Content Discovery" room. Run both gobuster and feroxbuster against the same target and compare output.
