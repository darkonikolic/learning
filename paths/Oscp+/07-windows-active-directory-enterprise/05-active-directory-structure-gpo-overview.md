# Active Directory Structure and GPO

Core AD components and how to enumerate them from both Windows and Linux.

## Key Components

| Component | Description |
|-----------|-------------|
| Domain | Logical boundary — `corp.local` |
| Domain Controller (DC) | Server that runs AD DS, holds the directory database |
| Forest | One or more domains with a trust relationship |
| Organizational Unit (OU) | Container for grouping users, computers, policies |
| GPO | Group Policy Object — applied to OUs to configure settings |
| Site | Physical network location grouping |

## Enumerate from Domain-Joined Windows (CMD)

```cmd
net user /domain                         # all domain users
net group /domain                        # all domain groups
net group "Domain Admins" /domain        # members of Domain Admins
net accounts /domain                     # password policy
gpresult /r                              # GPOs applied to current user/computer
```

## Enumerate with PowerShell (RSAT or PowerView)

```powershell
# Built-in AD module (on DCs or with RSAT installed)
Get-ADDomain
Get-ADUser -Filter * | Select Name, SamAccountName, Enabled, LastLogonDate
Get-ADGroup -Filter * | Select Name, GroupScope
Get-ADGroupMember "Domain Admins" | Select Name, SamAccountName
Get-ADComputer -Filter * | Select Name, OperatingSystem, Enabled

# PowerView (if RSAT not available)
Get-Domain
Get-DomainUser | Select samaccountname, description, memberof
Get-DomainGroupMember "Domain Admins"
```

## GPO Enumeration

```powershell
# List all GPOs
Get-GPO -All | Select DisplayName, GpoStatus, CreationTime

# GPOs applied to a specific OU
Get-GPInheritance -Target "OU=Users,DC=corp,DC=local"
```

Key GPOs to inspect:
- **Default Domain Policy** — password policy (min length, complexity, lockout)
- **Software Restriction** / **AppLocker** — what's blocked
- **Logon Scripts** — may execute commands or scripts on login
- **Drive Mappings** — may reveal file server paths

## Password Policy

```powershell
Get-ADDefaultDomainPasswordPolicy
# Look for: MinPasswordLength, LockoutThreshold, LockoutDuration
```

```cmd
net accounts /domain
```

## Exercise

Complete TryHackMe "Active Directory Basics" room:  
https://tryhackme.com/room/activedirectorybasics  

On your lab DC: run `Get-ADUser -Filter *` and count the users. Run `Get-ADGroupMember "Domain Admins"` — who is listed? Check the password policy — what is the minimum password length?
