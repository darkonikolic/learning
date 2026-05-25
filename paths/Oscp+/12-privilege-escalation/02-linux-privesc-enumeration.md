# Linux PrivEsc — systematic manual enumeration

Run every command below on every Linux box. Speed up with a saved enumeration script, but understand each command before you automate.

## Identity and privileges

```bash
id
whoami
sudo -l                                          # what can current user sudo?
cat /etc/passwd                                  # all users
cat /etc/shadow                                  # hashes — readable only if misconfigured
cat /etc/group
```

## SUID/SGID binaries

```bash
find / -perm -4000 -type f 2>/dev/null           # SUID
find / -perm -2000 -type f 2>/dev/null           # SGID
find / -perm -6000 -type f 2>/dev/null           # both
```

Cross-reference every result at https://gtfobins.github.io/

## Cron jobs

```bash
crontab -l                                       # current user's crons
crontab -l -u root 2>/dev/null                   # root's crons (if visible)
cat /etc/crontab
ls -la /etc/cron*
cat /etc/cron.d/*
```

Check if any cron-called scripts are world-writable:
```bash
ls -la /path/to/script_in_crontab
```

## Environment and PATH

```bash
env
echo $PATH
cat ~/.bash_history
cat ~/.bashrc
cat ~/.profile
```

## OS and kernel

```bash
uname -a
uname -r
cat /proc/version
cat /etc/os-release
lsb_release -a 2>/dev/null
```

## Running processes and network

```bash
ps aux
ps aux | grep root
ss -tulpn                                        # open ports/sockets
netstat -tulpn 2>/dev/null                       # older systems
cat /etc/hosts
```

## File system — interesting locations

```bash
find / -writable -type f 2>/dev/null | grep -v proc   # world-writable files
find / -writable -type d 2>/dev/null                   # world-writable dirs
find / -name "*.conf" 2>/dev/null | xargs grep -l "password" 2>/dev/null
find /home -name ".ssh" -type d 2>/dev/null
cat /root/.bash_history 2>/dev/null                    # if readable
```

## Installed packages and capabilities

```bash
dpkg -l                                          # Debian/Ubuntu
rpm -qa                                          # RHEL/CentOS
getcap -r / 2>/dev/null                          # Linux capabilities
```

## NFS shares

```bash
cat /etc/exports                                 # look for no_root_squash
showmount -e <target>
```

Run this checklist top-to-bottom on every box. Store results in your notes before starting exploitation attempts.
