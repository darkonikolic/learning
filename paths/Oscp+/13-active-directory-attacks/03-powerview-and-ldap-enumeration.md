# PowerView and LDAP Enumeration

PowerView gives granular manual enumeration that BloodHound sometimes misses. Use both.

## PowerView (Windows)

```powershell
Import-Module .\PowerView.ps1
# Or bypass AMSI first:
# Set-MpPreference -DisableRealtimeMonitoring $true (needs admin)
```

**Domain basics:**
```powershell
Get-Domain
Get-DomainController
Get-DomainPolicy
(Get-DomainPolicy)."system access"   # Password policy
```

**Users and groups:**
```powershell
Get-DomainUser
Get-DomainUser -Identity jsmith
Get-DomainUser -Properties samaccountname,description   # Look for passwords in description
Get-DomainGroup
Get-DomainGroupMember "Domain Admins"
Get-DomainGroupMember "Enterprise Admins"
```

**Computers:**
```powershell
Get-DomainComputer
Get-DomainComputer -Properties dnshostname,operatingsystem
```

**Shares and GPOs:**
```powershell
Find-DomainShare -CheckShareAccess          # Only shows accessible shares
Get-DomainGPO
Get-DomainGPOLocalGroup                     # GPOs that add users to local admin
```

**Trusts:**
```powershell
Get-DomainTrust
Get-ForestTrust
```

## LDAP Enumeration from Linux

```bash
# Anonymous LDAP query
ldapsearch -x -H ldap://DC_IP -b "dc=domain,dc=local"

# Authenticated
ldapsearch -x -H ldap://DC_IP -b "dc=domain,dc=local" \
  -D "user@domain.local" -w 'Password123'

# Get all users
ldapsearch -x -H ldap://DC_IP -b "dc=domain,dc=local" \
  "(objectClass=user)" sAMAccountName description
```

## NetExec Enumeration

```bash
# Users
nxc smb DC_IP -u user -p pass --users

# Groups
nxc smb DC_IP -u user -p pass --groups

# Password policy
nxc smb DC_IP -u user -p pass --pass-pol

# Logged-on users
nxc smb TARGET_IP -u user -p pass --loggedon-users

# Check local admin access across subnet
nxc smb 192.168.1.0/24 -u user -p pass
```

**Tip:** `Get-DomainUser -Properties description` frequently surfaces passwords left in AD description fields by sysadmins. Always check it.
