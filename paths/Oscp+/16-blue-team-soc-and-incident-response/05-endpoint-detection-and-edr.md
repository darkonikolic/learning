# Endpoint Detection and EDR

EDR detects behaviors, not just signatures. Know what telemetry is generated when you attack.

## Sysmon — Windows Telemetry

```powershell
# Install Sysmon with SwiftOnSecurity config (excellent baseline)
# https://github.com/SwiftOnSecurity/sysmon-config

Invoke-WebRequest -Uri https://download.sysinternals.com/files/Sysmon.zip -OutFile Sysmon.zip
Expand-Archive Sysmon.zip
Invoke-WebRequest -Uri https://raw.githubusercontent.com/SwiftOnSecurity/sysmon-config/master/sysmonconfig-export.xml -OutFile sysmonconfig.xml
.\Sysmon64.exe -accepteula -i sysmonconfig.xml
```

## Key Sysmon Event IDs

| Event ID | What It Captures | Attack Relevance |
|---|---|---|
| 1 | Process Create | Command execution, malware launch |
| 3 | Network Connection | C2, lateral movement |
| 7 | Image Loaded (DLL) | DLL hijacking, injection |
| 8 | CreateRemoteThread | Process injection |
| 11 | File Created | Malware dropped |
| 13 | Registry Value Set | Persistence via registry |
| 22 | DNS Query | C2 domain resolution |
| 25 | Process Tampering | EDR evasion attempts |

## Querying Sysmon Logs (PowerShell)

```powershell
# Get process creation events with command line
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -FilterXPath '*[System[EventID=1]]' |
    Select-Object TimeCreated, @{N='CmdLine';E={$_.Properties[10].Value}} | Format-List

# Find network connections to suspicious IPs
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -FilterXPath '*[System[EventID=3]]' |
    Where-Object { $_.Message -like "*4444*" -or $_.Message -like "*8080*" }

# Find DNS queries (malware C2 resolution)
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -FilterXPath '*[System[EventID=22]]' |
    Select-Object TimeCreated, @{N='Query';E={$_.Properties[5].Value}} | Format-List
```

## Velociraptor — Open Source DFIR

```bash
# Download from https://github.com/Velocidex/velociraptor/releases
# Run server (attacker/analyst machine)
./velociraptor gui

# Deploy agent to endpoint, collect artifacts:
# Windows.Forensics.ProcessInfo — running processes
# Windows.System.Pslist — process list with hashes
# Windows.EventLogs.Evtx — bulk event log collection
# Generic.Network.Netstat — network connections

# Hunt across endpoints — run artifact on all connected agents
# Artifacts → Hunt Manager → New Hunt → select artifact
```

## Windows Defender for Endpoint (MDE) — KQL Hunting

```kql
// Suspicious PowerShell execution
DeviceProcessEvents
| where ProcessCommandLine has_any ("DownloadString", "IEX", "Invoke-Expression", "EncodedCommand")
| project Timestamp, DeviceName, AccountName, ProcessCommandLine

// Lateral movement — remote process creation
DeviceLogonEvents
| where LogonType == "Network" and ActionType == "LogonSuccess"
| summarize count() by RemoteIP, DeviceName
| where count_ > 5

// Persistence — scheduled task creation
DeviceProcessEvents
| where ProcessCommandLine has "schtasks" and ProcessCommandLine has "/create"
```

## Key EDR Concepts

- Behavioral detection: EDR watches process trees, not file hashes
- Red team implication: `cmd.exe` spawned by `word.exe` is an alert, even if the binary is clean
- AMSI: blocks malicious PowerShell at runtime — EDR hooks into it
- ETW: Windows event tracing — EDR telemetry source

## Practice

- TryHackMe "Sysmon" room — install, configure, query
- TryHackMe "Velociraptor" room
- CyberDefenders labs with Sysmon logs as evidence
