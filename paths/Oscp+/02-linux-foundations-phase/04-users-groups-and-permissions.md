# Users, groups, and permissions

Understanding permissions is prerequisite for privilege escalation. SUID bits and sudo misconfigs are the most common Linux privesc vectors.

## Identify current user context

```bash
id                               # uid, gid, all groups
whoami                           # just the username
groups                           # groups current user belongs to
cat /etc/passwd                  # all local users (username:x:uid:gid:info:home:shell)
sudo -l                          # what this user can run as root — always check this
```

## Read /etc/shadow (requires root)

```bash
cat /etc/shadow                  # hashed passwords — crackable offline with hashcat
# Format: username:$algorithm$salt$hash:lastchange:...
```

## Permission bits — reading ls -la output

```bash
ls -la /etc/passwd
# -rw-r--r-- 1 root root 2847 May 1 10:00 /etc/passwd
#  ^^^^^^^^^
#  rwx = owner | rwx = group | rwx = others
```

| Octal | Meaning | Common use |
|-------|---------|------------|
| 644   | rw-r--r-- | regular files |
| 755   | rwxr-xr-x | executables, dirs |
| 600   | rw------- | private keys, shadow |
| 4755  | rwsr-xr-x | SUID binary — runs as owner |

## Modify permissions and ownership

```bash
chmod 644 file.txt               # set exact permissions
chmod +x script.sh               # add execute for all
chmod 600 ~/.ssh/id_rsa          # private key must be 600 or ssh refuses it
chown user:group file.txt        # change owner and group
chown -R www-data:www-data /var/www/html
```

## Lab exercise — users, groups, SUID

```bash
# Create a user, add to a group, set permissions
sudo useradd -m testuser
sudo groupadd testgroup
sudo usermod -aG testgroup testuser
id testuser

# Find SUID binaries on the system (privesc enumeration)
find / -perm -4000 -type f 2>/dev/null
# Look for non-standard entries: /usr/bin/passwd and /usr/bin/sudo are expected
# /opt/custom_binary with SUID is suspicious

# Find world-writable files
find / -perm -o+w -type f 2>/dev/null | grep -v proc
```

## Why this matters now

When you land on a box, run `sudo -l` and `find / -perm -4000` within the first two minutes. SUID binaries like `vim`, `find`, `cp`, `bash` with SUID = instant root via GTFOBins: https://gtfobins.github.io

## Practice

- TryHackMe "Linux Fundamentals Part 2": https://tryhackme.com/room/linuxfundamentalspart2
- TryHackMe "Linux PrivEsc": https://tryhackme.com/room/linuxprivesc (preview — revisit in depth later)

## Completion bar

From memory: check current user context, read passwd/shadow, find SUID binaries, change file permissions — using `id` `sudo -l` `ls -la` `find -perm -4000` `chmod` `chown`.
