# Local Security Surfaces and Logging

User enumeration, privilege checking, and reading Windows event logs.

## User and Group Enumeration

```cmd
# CMD
net user                              # list all local users
net user administrator                # details on specific user
net localgroup                        # list all local groups
net localgroup administrators         # members of Administrators group
```

```powershell
# PowerShell
Get-LocalUser | Select Name, Enabled, LastLogon
Get-LocalGroupMember -Group "Administrators"
Get-LocalGroupMember -Group "Remote Desktop Users"
```

## Current User Privileges

```cmd
whoami                    # current username
whoami /all               # full info: user, groups, privileges
whoami /priv              # privileges only
whoami /groups            # group memberships
```

Key privileges to note:
- `SeImpersonatePrivilege` — Potato exploits possible
- `SeBackupPrivilege` — read any file
- `SeDebugPrivilege` — access other processes' memory
- `SeTakeOwnershipPrivilege` — take ownership of any object

## Windows Defender Status

```powershell
Get-MpComputerStatus | Select AntivirusEnabled, RealTimeProtectionEnabled, AMServiceEnabled
Get-MpComputerStatus | Select AMRunningMode, QuickScanAge
```

## Event Logs — Key Event IDs

| Event ID | Meaning |
|----------|---------|
| 4624 | Successful logon |
| 4625 | Failed logon |
| 4647 | User-initiated logoff |
| 4720 | User account created |
| 4726 | User account deleted |
| 4732 | User added to a security-enabled local group |
| 4672 | Special privileges assigned to new logon |

## Query Event Logs with PowerShell

```powershell
# Last 20 security events
Get-WinEvent -LogName Security -MaxEvents 20 | Select TimeCreated, Id, Message

# Filter for specific event ID
Get-WinEvent -LogName Security | Where-Object Id -eq 4625 | Select -First 10 TimeCreated, Message

# Failed logins in last 24 hours
Get-WinEvent -LogName Security -FilterXPath "*[System[EventID=4625 and TimeCreated[timediff(@SystemTime) <= 86400000]]]" | Select TimeCreated, Message
```

## Exercise

Complete TryHackMe "Windows Event Logs" room:  
https://tryhackme.com/room/windowseventlogs  

On your Windows VM: run `whoami /all` and document every privilege listed. Query the Security log for any 4625 events — were there any failed logins?
