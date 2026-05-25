# Linux quick reference — security-relevant commands

Assumes basic Linux comfort. Focus here is on commands that matter during a pentest or CTF.

## User and privilege enumeration

```bash
whoami                          # current user
id                              # uid, gid, groups
sudo -l                         # what can this user run as root?
cat /etc/passwd                 # all users (UID 0 = root)
cat /etc/shadow                 # password hashes (requires root)
cat /etc/sudoers                # sudo config
```

## SUID and interesting file hunting

```bash
# Find SUID binaries — executables that run as their owner (often root)
find / -perm -4000 -type f 2>/dev/null

# Find world-writable files
find / -perm -o+w -type f 2>/dev/null

# Find files owned by root but writable by others
find / -user root -writable 2>/dev/null | grep -v proc
```

## Scheduled tasks and services

```bash
crontab -l                      # current user's cron jobs
cat /etc/crontab                # system-wide cron jobs
ls /etc/cron.*                  # cron.d, cron.daily, etc.
systemctl list-units --type=service --state=running
ps aux                          # all running processes
```

## Network state from inside a machine

```bash
netstat -tulpn                  # listening ports and which process
ss -tulpn                       # same, newer tool
cat /etc/hosts                  # local hostname resolution
ip addr                         # IP addresses on all interfaces
```

## Interesting files to check

```
/etc/passwd          — user list
/etc/shadow          — password hashes (need root)
/etc/hosts           — internal hostnames
/etc/crontab         — scheduled tasks
~/.ssh/authorized_keys  — who can SSH in as this user
~/.bash_history      — commands the user ran
/var/mail/           — email (sometimes contains creds)
/tmp/ and /var/tmp/  — world-writable, used to stage payloads
```

## Practice

TryHackMe "Linux Fundamentals" parts 1–3: https://tryhackme.com/module/linux-fundamentals
TryHackMe "Linux PrivEsc": https://tryhackme.com/room/linuxprivesc
