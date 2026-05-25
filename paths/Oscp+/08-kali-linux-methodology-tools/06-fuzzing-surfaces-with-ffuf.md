# ffuf — Fast Fuzzing for Web Targets

ffuf is faster than gobuster for most web fuzzing tasks and more flexible for parameter/header fuzzing.

## Install

```bash
sudo apt install ffuf
```

## Directory Discovery

Basic:

```bash
ffuf -u http://target/FUZZ -w /usr/share/wordlists/dirb/common.txt
```

With extensions:

```bash
ffuf -u http://target/FUZZ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt \
  -e .php,.html,.txt,.bak
```

## Parameter Fuzzing

GET parameter name discovery:

```bash
ffuf -u "http://target/page?FUZZ=value" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -mc 200
```

POST body fuzzing:

```bash
ffuf -u http://target/login \
  -X POST \
  -d "user=FUZZ&pass=test" \
  -w /usr/share/seclists/Usernames/top-usernames-shortlist.txt \
  -H "Content-Type: application/x-www-form-urlencoded"
```

## Vhost Enumeration

First get baseline response size, then filter it:

```bash
# Step 1: note response size for invalid vhost
curl -o /dev/null -s -w "%{size_download}\n" -H "Host: invalid.target.com" http://target

# Step 2: fuzz and filter that size
ffuf -u http://target -H "Host: FUZZ.target.com" \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -fs 1234
```

## Filtering Responses

| Flag | Purpose |
|------|---------|
| `-fs SIZE` | Filter by response size |
| `-fc 404,403` | Filter by status code |
| `-mc 200,302` | Match only these codes |
| `-fw NUM` | Filter by word count |
| `-rate 50` | Limit requests per second |

## Reduce False Positives

Run once, note the most common response size, then add `-fs SIZE` to filter it out.

## Practice

TryHackMe "Content Discovery" room. Also try parameter fuzzing against Juice Shop (`http://localhost:3000`).
