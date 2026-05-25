# Threat Hunting Methodology

Proactive search for attacker activity before alerts fire. Hypothesis-driven, data-intensive.

## The Hunting Loop

```
Hypothesis → Data Collection → Analysis → Finding → Action (escalate or new detection rule)
```

## Hypothesis Sources

- MITRE ATT&CK: pick a technique, hunt for evidence of it
- Threat intelligence: actor X uses technique Y — hunt for Y in your environment
- Anomaly baseline: what's normal? hunt for deviations
- Red team findings: what did your last pentest show? hunt for it in prod

## MITRE ATT&CK Driven Hunt

```bash
# ATT&CK Navigator: https://mitre-attack.github.io/attack-navigator/
# Pick technique: T1059.001 (PowerShell)

# Hunt in Splunk
index=windows EventCode=4688 Image="*powershell*"
| table _time, ComputerName, CommandLine
| sort -_time

# Hunt in Sysmon logs
index=sysmon EventCode=1 Image="*powershell*" CommandLine="*Encoded*"
| rex field=CommandLine "(?i)-enc\w*\s+(?P<b64>[A-Za-z0-9+/=]{20,})"
| table _time, ComputerName, b64
```

## Common Hunt Hypotheses and Searches

```splunk
# Living-off-the-land: LOLBins used for execution
index=windows EventCode=4688 (Image="*certutil*" OR Image="*mshta*" OR Image="*regsvr32*" OR Image="*wscript*")

# Credential dumping — LSASS access
index=sysmon EventCode=10 TargetImage="*lsass*"
| stats count by SourceImage, GrantedAccess

# Persistence via scheduled tasks
index=windows EventCode=4698
| table _time, ComputerName, TaskName, TaskContent

# Suspicious parent-child process relationships
index=sysmon EventCode=1 (ParentImage="*winword*" OR ParentImage="*excel*" OR ParentImage="*outlook*")
  AND (Image="*cmd*" OR Image="*powershell*" OR Image="*wscript*")
```

## Elastic/KQL Hunt Queries

```kql
// PowerShell with encoded commands
process.name: "powershell.exe" AND process.args: ("-enc" OR "-EncodedCommand")

// Network connections from Office apps (macro execution)
process.name: ("WINWORD.EXE" OR "EXCEL.EXE") AND event.type: "network_attempt"

// Unusual parent for cmd.exe
process.name: "cmd.exe" AND NOT process.parent.name: ("explorer.exe" OR "cmd.exe" OR "powershell.exe")
```

## Data Sources for Hunting

| Data Source | What to Hunt |
|---|---|
| EDR/Sysmon | Process chains, network connections, file drops |
| SIEM | Logon patterns, account changes, service installs |
| Proxy logs | Unusual domains, beaconing, large uploads |
| DNS logs | DGA domains, tunneling, C2 resolution |
| Firewall logs | Scanning, outbound to known bad IPs |

## IOC Analysis Tools

```bash
# CyberChef — decode base64, deobfuscate
# https://gchq.github.io/CyberChef/

# VirusTotal — hash/IP/domain lookup
curl "https://www.virustotal.com/vtapi/v2/file/report?apikey=KEY&resource=HASH"

# URLScan.io — scan suspicious URLs
# MISP — threat intelligence platform for IOC sharing
```

## Hunt Output

- Confirmed attacker activity: escalate to IR immediately
- No finding but pattern is suspicious: tune into detection rule
- False positive noise: document and filter, refine hypothesis

## Practice

- ThreatHunting.net — techniques and datasets
- CyberDefenders labs with endpoint telemetry
- TryHackMe "Hunting with Splunk" room
- Apply MITRE ATT&CK Navigator to your HTB/lab environments
