# Integration drills and completion criteria

Scenario-based drill: you've just landed on a new Linux box via SSH. Run the following commands in order — no looking up flags.

## Drill sequence — new box, first 5 minutes

```bash
# 1. Who am I and what can I do?
id
whoami
sudo -l

# 2. Where am I?
hostname
ip a
cat /etc/os-release

# 3. Who else is here?
cat /etc/passwd | cut -d: -f1,3,7 | grep -v nologin
cat /etc/group
last | head -20

# 4. What is running?
ps aux
ss -tulpn
systemctl list-units --type=service --state=running

# 5. What files are interesting?
find / -perm -4000 -type f 2>/dev/null     # SUID binaries
find /home -name "*.txt" -o -name "*.key" -o -name "*.pem" 2>/dev/null
find / -writable -type f 2>/dev/null | grep -v proc | head -20

# 6. Logs and history
cat ~/.bash_history
sudo tail -50 /var/log/auth.log
sudo journalctl -u ssh --since "1 day ago"

# 7. Filesystem — what is here?
ls -la /
ls -la /opt /srv /var/www 2>/dev/null
df -h
```

## 15 commands you must run from memory

1. `id`
2. `sudo -l`
3. `ip a`
4. `ss -tulpn`
5. `ps aux`
6. `cat /etc/passwd`
7. `cat /etc/shadow` (if root)
8. `find / -perm -4000 -type f 2>/dev/null`
9. `find / -writable -type f 2>/dev/null | grep -v proc`
10. `cat ~/.bash_history`
11. `ls -la /home/`
12. `systemctl list-units --type=service --state=running`
13. `uname -a`
14. `cat /etc/crontab`
15. `env`

## Text processing mini-drill

```bash
# Without help: extract all users with /bin/bash as shell from /etc/passwd
grep "/bin/bash$" /etc/passwd | cut -d: -f1

# Count failed SSH logins in auth.log
grep "Failed password" /var/log/auth.log | wc -l

# Find the top 5 IPs with failed logins
grep "Failed password" /var/log/auth.log | \
  grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | \
  sort | uniq -c | sort -rn | head -5
```

## Practice rooms

- TryHackMe "Linux Fundamentals" Part 1–3:
  - https://tryhackme.com/room/linuxfundamentalspart1
  - https://tryhackme.com/room/linuxfundamentalspart2
  - https://tryhackme.com/room/linuxfundamentalspart3
- TryHackMe "Linux Challenges": https://tryhackme.com/room/linuxctf

## Exit bar

Complete the full drill sequence on a fresh VM without checking notes. Time yourself — target under 10 minutes for all 15 commands plus the three text processing tasks.
