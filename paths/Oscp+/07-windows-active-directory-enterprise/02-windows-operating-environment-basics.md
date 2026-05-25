# Windows Operating Environment Basics

Key filesystem paths, CMD commands, and PowerShell for security work.

## Security-Relevant Directory Structure

```
C:\Windows\System32\          — OS binaries, DLLs, executables
C:\Windows\System32\config\   — registry hives (SAM, SYSTEM, SECURITY)
C:\Windows\Repair\            — backup SAM file (readable by admin)
C:\Windows\System32\drivers\etc\hosts  — local DNS override
C:\Users\<username>\          — user profiles, AppData, Desktop
C:\Users\<username>\AppData\Roaming\  — application data, browser profiles
C:\ProgramData\               — all-user application data (often writable)
C:\Program Files\             — installed applications (64-bit)
C:\Program Files (x86)\       — installed applications (32-bit)
C:\Temp\ or C:\Windows\Temp\  — temp files, often world-writable
```

## CMD Essentials

```cmd
dir /a                          # list all files including hidden
dir /s /b *.txt                 # recursive search for .txt files
type file.txt                   # print file contents
findstr /i "password" *.txt     # case-insensitive string search in files
findstr /si "password" *.xml *.config *.ini  # search multiple types
where python                    # find executable location
set                             # print all environment variables
echo %USERPROFILE%              # current user's home directory
echo %PATH%                     # executable search paths
ipconfig /all                   # network config with MAC and DNS
```

## PowerShell Equivalents

```powershell
Get-ChildItem -Path C:\ -Hidden -Recurse -ErrorAction SilentlyContinue
Get-Content C:\path\to\file.txt
Select-String -Path C:\Users -Recurse -Pattern "password" -Include *.txt,*.xml,*.config
Get-ChildItem Env:              # all environment variables
$env:USERPROFILE                # user profile path
```

## Security-Relevant Files to Check

```cmd
# Local DNS overrides (may redirect traffic)
type C:\Windows\System32\drivers\etc\hosts

# Backup SAM (credential hashes if accessible)
dir C:\Windows\Repair\
dir C:\Windows\System32\config\RegBack\

# Unattended install files (may contain plaintext credentials)
dir /s /b C:\unattend.xml C:\sysprep.inf C:\sysprep.xml 2>nul
```

## Exercise

Complete TryHackMe "Windows Fundamentals 1", "Windows Fundamentals 2", and "Windows Fundamentals 3" rooms:  
https://tryhackme.com/room/windowsfundamentals1xbx  
https://tryhackme.com/room/windowsfundamentals2x0x  
https://tryhackme.com/room/windowsfundamentals3xzx  

On your Windows VM: run each command block above, note the output, and find at least one file that contains a string matching "password" using findstr.
