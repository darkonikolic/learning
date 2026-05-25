# Directory and File Discovery with gobuster

gobuster is fast and straightforward — use it for directory brute-forcing and subdomain enumeration.

## Install

```bash
sudo apt install gobuster
```

## Directory Mode

Quick scan with common wordlist:

```bash
gobuster dir -u http://target -w /usr/share/wordlists/dirb/common.txt -t 50
```

Thorough scan with extensions:

```bash
gobuster dir -u http://target \
  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
  -x php,txt,html,bak,old,zip \
  -t 40 \
  -o gobuster_results.txt
```

Exclude noise (skip 404 and 403):

```bash
gobuster dir -u http://target -w wordlist.txt -b 404,403 -t 40
```

Show full URLs in output:

```bash
gobuster dir -u http://target -w wordlist.txt -e
```

## DNS Mode — Subdomain Enumeration

```bash
gobuster dns -d target.com \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -t 50
```

## Vhost Mode

```bash
gobuster vhost -u http://target -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain
```

## Wordlist Selection

| Wordlist | Use Case |
|----------|----------|
| `dirb/common.txt` | Fast first pass |
| `directory-list-2.3-medium.txt` | Thorough directory scan |
| `raft-medium-directories.txt` | Good general-purpose |
| `SecLists/Discovery/Web-Content/` | Full collection |

## Practice

Run against DVWA (`http://localhost`) and Juice Shop (`http://localhost:3000`). Compare what each wordlist finds.
