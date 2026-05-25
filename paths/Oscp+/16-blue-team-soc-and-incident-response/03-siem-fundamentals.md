# SIEM Fundamentals

Search, correlate, alert. SIEMs aggregate logs — your job is to find the signal.

## Splunk Search Syntax

```splunk
# Basic event search
index=windows EventCode=4625

# Count failed logins by source IP
index=windows EventCode=4625 | stats count by src_ip | sort -count

# Brute force detection — >10 failures in 5 minutes
index=windows EventCode=4625
| bucket _time span=5m
| stats count by _time, src_ip
| where count > 10

# Find process creation with suspicious command
index=windows EventCode=4688 CommandLine="*powershell*download*"

# Lateral movement — NTLM logons between workstations
index=windows EventCode=4624 LogonType=3 NOT dest="domain_controller"
| stats count by src_ip, dest | sort -count

# Data exfiltration indicator — large outbound transfers
index=network bytes_out > 10000000 | stats sum(bytes_out) by dest_ip | sort -sum(bytes_out)
```

## Elastic/Kibana — KQL Syntax

```kql
# Failed logons
event.code: "4625"

# Failed logons from specific IP
event.code: "4625" AND source.ip: "192.168.1.100"

# PowerShell execution
event.code: "4688" AND process.name: "powershell.exe"

# Combine conditions
event.code: "4625" AND winlog.event_data.FailureReason: *

# Time range (use UI picker or)
@timestamp >= "2024-01-01T00:00:00" and @timestamp <= "2024-01-02T00:00:00"
```

## Building a Basic Detection Rule

Threshold-based: N failed logins from same IP within Y minutes.

Splunk alert:
```splunk
index=windows EventCode=4625
| bucket _time span=10m
| stats count by _time, src_ip
| where count >= 5
```
- Save as Alert → trigger action → email or webhook

Elastic detection rule:
- Security → Rules → Create Rule → Threshold
- Index: `winlogbeat-*`, Query: `event.code:4625`
- Threshold field: `source.ip`, over: 5 in last 10 minutes

## Free Practice Datasets

```bash
# Splunk BOSS of the SOC (BOTS) dataset — realistic attack scenarios
# https://github.com/splunk/botsv3

# Import into Splunk free trial and work through challenges
# Categories: web attack, phishing, insider threat, APT

# TryHackMe Splunk rooms
# "Splunk: Basics" and "Investigating with Splunk"
```

## Key SIEM Use Cases

| Use Case | Log Source | Key Fields |
|---|---|---|
| Brute force | Windows Security | EventID 4625, src_ip |
| Lateral movement | Windows Security | EventID 4624, LogonType 3 |
| Persistence | Windows Security/System | EventID 4698, 7045 |
| C2 beaconing | Proxy/DNS logs | dest_ip, query frequency |
| Data exfil | Proxy/FW | bytes_out, dest_ip |

## Practice

- Splunk BOTS dataset (free with Splunk trial)
- TryHackMe "Splunk" room series
- LetsDefend.io alert triage exercises
