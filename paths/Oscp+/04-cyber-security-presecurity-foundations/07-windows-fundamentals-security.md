# Windows fundamentals for security — CMD and PowerShell

Commands you run after landing on a Windows box to understand what you have.

## Basic enumeration — CMD

```cmd
whoami /all                     REM current user + privileges + groups
net user                        REM all local users
net user administrator          REM details on a specific user
net localgroup administrators   REM who's in the admins group
systeminfo                      REM OS version, hotfixes, hostname
ipconfig /all                   REM network interfaces, DNS, gateway
tasklist /SVC                   REM running processes with service names
netstat -ano                    REM connections + PIDs
```

## Basic enumeration — PowerShell

```powershell
Get-Process | Sort-Object CPU -Descending | Select-Object -First 10
Get-Service | Where-Object { $_.Status -eq "Running" }
Get-LocalUser
Get-LocalGroupMember Administrators
Get-NetIPAddress
Get-NetTCPConnection | Where-Object State -eq Listen
```

## Registry — persistence and auto-run locations

```cmd
REM Check what runs on startup
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run
reg query HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce
```

## File system — interesting locations

```
C:\Users\<user>\Desktop\
C:\Users\<user>\Documents\
C:\Users\<user>\AppData\Roaming\
C:\Windows\System32\config\  — SAM and SYSTEM (password hashes, need SYSTEM priv)
C:\inetpub\wwwroot\          — IIS web root (check for config files)
C:\Program Files\            — installed software versions
```

## PowerShell execution policy bypass

```powershell
# Check current policy
Get-ExecutionPolicy

# Bypass for current session (common during pentests)
powershell -ExecutionPolicy Bypass -File script.ps1
Set-ExecutionPolicy -Scope CurrentUser Bypass
```

## Scheduled tasks

```cmd
schtasks /query /fo LIST /v    REM all scheduled tasks verbose
```

## Practice

TryHackMe "Windows Fundamentals" rooms 1–3: https://tryhackme.com/module/windows-fundamentals
TryHackMe "Windows PrivEsc": https://tryhackme.com/room/windows10privesc
