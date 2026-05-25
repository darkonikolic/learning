# PEN-200 Readiness Self-Assessment

Answer these 20 questions from memory with no notes. If you can't answer 15 or more, keep practicing before enrolling.

## Questions

```
1.  How do you enumerate SMB shares from Linux?
2.  What's the nmap command for a full version+script scan on all ports?
3.  How do you exploit MS17-010 manually without Metasploit?
4.  What does LinPEAS check first when run on a Linux target?
5.  How do you get a shell from a SQL injection vulnerability?
6.  What's the Kerberoasting command with impacket?
7.  How do you crack an NTLM hash with hashcat?
8.  What's the difference between a bind shell and a reverse shell?
9.  How do you upgrade a netcat shell to a fully interactive TTY?
10. How do you enumerate users in an AD domain without credentials?
11. What is AS-REP roasting and when does it apply?
12. How do you transfer files from your attacker machine to a Windows target?
13. What's the command to download and run PEASS on a Linux target?
14. How do you find SUID misconfigs on Linux?
15. What are the OSCP exam rules on Metasploit usage?
16. How do you identify a web app's tech stack quickly?
17. What does SeImpersonatePrivilege enable on Windows and how do you exploit it?
18. How do you mount a CIFS/SMB share on Linux?
19. What information does BloodHound collect and how do you run the collector?
20. What must every OSCP exam report screenshot include?
```

## Scoring

| Score | Action |
|-------|--------|
| < 15 | Revisit weak areas, keep doing PG machines |
| 15–18 | Ready to enroll, start PEN-200 |
| 19–20 | Start PEN-200 now |

## Sample Answers to Check Against

```bash
# Q1: SMB shares
smbclient -L //target -N
nxc smb target -u '' -p '' --shares

# Q2: Full scan
nmap -sV -sC -p- -T4 target

# Q6: Kerberoasting
impacket-GetUserSPNs domain.local/user:pass -dc-ip DC_IP -request

# Q9: Shell upgrade
python3 -c 'import pty;pty.spawn("/bin/bash")'
# then: Ctrl+Z, stty raw -echo; fg, reset

# Q14: SUID
find / -perm -u=s -type f 2>/dev/null
```
