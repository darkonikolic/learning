# grep, pipes, and Bash basics

Search files, chain commands, and write simple scripts. Used constantly during enumeration and log analysis.

## grep — find patterns

```bash
grep "root" /etc/passwd                        # lines containing "root"
grep -i "failed" /var/log/auth.log             # case-insensitive
grep -n "error" app.log                        # show line numbers
grep -v "nologin" /etc/passwd                  # exclude matches (invert)
grep -r "password" /etc/                       # recursive search
grep -E "^(root|admin)" /etc/passwd            # extended regex, multiple patterns
grep -l "password" /var/www/html/*.php         # list files that match, not lines
```

## find — locate files

```bash
find /etc -name "*.conf" -type f               # all .conf files
find / -name "id_rsa" 2>/dev/null              # find private keys, suppress errors
find /var/www -name "*.php" -newer /tmp/ref    # files modified recently
find / -perm -4000 -type f 2>/dev/null         # SUID binaries (privesc hunting)
find /home -name ".bash_history" 2>/dev/null   # user history files
```

## awk and sed — transform text

```bash
awk '{print $1}' access.log                    # print first field (space-delimited)
awk -F: '{print $1, $3}' /etc/passwd           # username and UID
awk '$9 == "404" {print $7}' access.log        # HTTP 404 URLs from Apache log
sed 's/old/new/g' file.txt                     # replace all occurrences
sed -n '10,20p' file.txt                       # print lines 10-20
```

## Pipes — chain three or more commands

```bash
# Top 10 IPs hitting a web server
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Find all ERROR lines, extract unique IPs
grep "ERROR" app.log | awk '{print $NF}' | sort | uniq

# List all open ports from nmap output
grep "open" nmap_output.txt | awk '{print $1}' | cut -d/ -f1
```

## Bash script template

```bash
#!/bin/bash
TARGET=$1
OUTDIR="results/$TARGET"
mkdir -p "$OUTDIR"

for PORT in 80 443 8080 8443; do
    if nc -z -w 2 "$TARGET" "$PORT" 2>/dev/null; then
        echo "[+] $TARGET:$PORT open" | tee -a "$OUTDIR/ports.txt"
    fi
done
```

## Lab exercise — find errors and count unique IPs

```bash
# Generate a sample log, then analyze it
sudo journalctl -n 500 > /tmp/sample.log
grep -i "error\|fail\|denied" /tmp/sample.log | wc -l
grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' /tmp/sample.log | sort | uniq -c | sort -rn | head -5
find /var/log -name "*.log" -size +1M 2>/dev/null
```

## Practice

- LabEx Text-Fu track: https://labex.io/courses/linux-text-processing-and-regular-expressions
- TryHackMe Linux Fundamentals Part 3: https://tryhackme.com/room/linuxfundamentalspart3

## Completion bar

Write a one-liner that: finds all `.log` files under `/var/log`, greps for "error" case-insensitively, counts unique occurrences — using `find`, `grep`, `sort`, `uniq -c`.
