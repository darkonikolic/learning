# Packages, logs, and systemd

Install tools, read logs, archive data. Practical ops skills used every lab session.

## apt package management

```bash
sudo apt update                          # refresh package index (do this first)
sudo apt install nmap gobuster curl -y   # install tools non-interactively
sudo apt remove nmap                     # remove package
sudo apt autoremove                      # clean unused dependencies
dpkg -l | grep nmap                      # check if package is installed
dpkg -l | grep "^ii"                     # list all installed packages
which nmap && nmap --version             # confirm install and version
```

## Log files — where to look

| File | Contains |
|------|----------|
| `/var/log/auth.log` | SSH logins, sudo usage, su attempts |
| `/var/log/syslog` | General system events |
| `/var/log/nginx/access.log` | Web requests |
| `/var/log/nginx/error.log` | Web errors |
| `/var/log/apache2/access.log` | Apache requests |
| `/var/log/dpkg.log` | Package installs/removes |

## journalctl — systemd logs

```bash
sudo journalctl -f                           # follow live system log
sudo journalctl -u ssh                       # SSH service logs only
sudo journalctl -u ssh --since "1 hour ago"  # recent SSH activity
sudo journalctl --since "2024-01-01" --until "2024-01-02"
sudo journalctl -p err                       # errors only
```

## Archive and extract with tar

```bash
tar -czf backup.tar.gz ~/pentest/            # compress directory (c=create, z=gzip, f=file)
tar -xzf backup.tar.gz -C /tmp/restore/     # extract to target directory
tar -tzf backup.tar.gz                       # list contents without extracting
tar -czf loot-$(date +%F).tar.gz /tmp/loot/ # timestamped archive
```

## Lab exercise — install nmap, run it, check journal

```bash
sudo apt update && sudo apt install nmap -y
nmap --version
# Run a scan and check what the system logged
nmap -sV localhost
sudo journalctl -u systemd-resolved --since "2 minutes ago"
sudo tail -50 /var/log/syslog | grep -i "nmap\|scan\|port"
```

## Practice

- TryHackMe "Linux Fundamentals Part 3": https://tryhackme.com/room/linuxfundamentalspart3
- Udemy "Linux Administration Bootcamp" — package management section: https://www.udemy.com/course/linux-administration-bootcamp/

## Completion bar

Install a package, check journal for related activity, archive a directory, list archive contents — using `apt` `dpkg` `journalctl` `tar` without looking up flags.
