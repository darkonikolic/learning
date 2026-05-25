# Windows PrivEsc — systematic manual enumeration

Run every command block below on every Windows target. Many findings are invisible without methodical enumeration.

## Identity and privileges

```cmd
whoami
whoami /all          # full user info including privileges and groups
whoami /priv         # token privileges — look for SeImpersonate, SeDebug, SeBackup
net user             # local users
net user <username>  # specific user details
net localgroup administrators
net localgroup
```

## System information

```cmd
systeminfo                       # OS, patch level, hotfixes — key for CVE research
systeminfo | findstr /B /C:"OS Name" /C:"OS Version" /C:"System Type"
wmic os get Caption,Version,OSArchitecture
hostname
echo %USERDOMAIN%
```

## Running processes and services

```cmd
tasklist /SVC                     # processes with associated services
tasklist /FI "USERNAME ne NT AUTHORITY\SYSTEM"    # non-system processes
wmic service list brief           # all services
wmic service get name,displayname,pathname,startmode
sc query type= all                # all service states
```

## Network connections

```cmd
netstat -ano                      # all connections with PIDs
netstat -ano | findstr LISTENING
ipconfig /all
route print
arp -a
```

## Installed software and patches

```cmd
wmic product get name,version     # installed software
wmic qfe list brief               # installed hotfixes/patches
wmic qfe get Caption,Description,HotFixID,InstalledOn
```

## Registry — key PrivEsc checks

```cmd
# AlwaysInstallElevated
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

# Stored credentials
reg query HKLM /f password /t REG_SZ /s
reg query HKCU /f password /t REG_SZ /s

# AutoLogon credentials
reg query "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
```

## Filesystem — interesting locations

```cmd
dir "C:\Program Files"
dir "C:\Program Files (x86)"
dir C:\Users
dir C:\Users\<user>\Desktop
dir C:\Users\<user>\Documents
dir C:\Windows\Temp
dir C:\Temp 2>nul
dir C:\ /s /b 2>nul | findstr /si password
```

## Unquoted service paths — quick check

```cmd
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "C:\Windows"
```

Any path with spaces and no quotes is a potential unquoted service path vulnerability.
