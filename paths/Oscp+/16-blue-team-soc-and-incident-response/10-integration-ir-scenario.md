# Integration — Full IR Scenario Walkthrough

Put it all together: receive alert → investigate → timeline → contain → report.

## Recommended Lab

Use one of these for a realistic scenario:
- Blue Team Labs Online: "Sticky Situation" or "Infection Monkey" IR scenarios
  https://blueteamlabs.online/
- CyberDefenders: "CyberCorp Case 2" (free, DFIR heavy)
  https://cyberdefenders.org/blueteam-ctf-challenges/
- TryHackMe "Carnage" room — PCAP and log-based IR
  https://tryhackme.com/room/c2carnage

Work through this as a timed exercise: target 2–3 hours.

## Step 1 — Receive Alert, Read Initial IOCs

```
Alert received: "EDR — Credential Dumping Detected on DESKTOP-A1B2C3"
Time: 2024-03-15 14:32:11 UTC

Initial IOCs from alert:
- Affected host: DESKTOP-A1B2C3 (192.168.1.45)
- Process: lsass.exe accessed by rundll32.exe
- Parent: cmd.exe
- User context: john.smith@corp.local
- File dropped: C:\Windows\Temp\svch0st.exe (SHA256: abc123...)
```

## Step 2 — SIEM Pivot — Timeline Reconstruction

```splunk
# Start 30 minutes before alert — what triggered this?
index=windows host="DESKTOP-A1B2C3" earliest=-30m@m latest=+30m@m
| sort _time
| table _time, EventCode, Account_Name, Process_Name, CommandLine

# Find how attacker got initial access
index=windows EventCode=4624 dest="DESKTOP-A1B2C3" earliest=-2h@h
| table _time, src_ip, Account_Name, Logon_Type

# Look for lateral movement from this host
index=windows EventCode=4624 src_ip="192.168.1.45" earliest=-2h@h
| stats count by dest, Account_Name | sort -count

# Check email/web for phishing delivery (if proxy logs available)
index=proxy src="192.168.1.45" earliest=-4h@h
| table _time, url, action
```

## Step 3 — Identify Patient Zero and Attack Vector

```
Questions to answer:
1. How did attacker get in? (phishing email? exploit? valid creds?)
2. What was the first malicious action?
3. What account was used?
4. What tools/TTPs were used? Map to MITRE ATT&CK.

Example finding:
- 13:45: john.smith received phishing email with macro attachment
- 13:47: WINWORD.EXE spawned cmd.exe (T1566.001 Spearphishing)
- 13:48: cmd.exe downloaded svch0st.exe via certutil (T1105 Ingress Tool Transfer)
- 14:30: svch0st.exe (Cobalt Strike beacon) accessed lsass (T1003.001 LSASS Memory)
```

## Step 4 — Scope the Incident

```splunk
# Was svch0st.exe seen on other hosts?
index=sysmon Image="*svch0st*" OR CommandLine="*svch0st*"
| stats count by ComputerName

# Were creds used for lateral movement?
index=windows EventCode=4624 Account_Name="john.smith" earliest=-6h@h
| stats count by ComputerName | where count > 0

# Data exfiltration check — large outbound after compromise
index=proxy src="192.168.1.45" action=allowed bytes_out > 1000000 earliest=14:30
| table _time, url, bytes_out
```

## Step 5 — Containment Recommendations

```
Immediate (within 1 hour):
1. Isolate DESKTOP-A1B2C3 — network quarantine via EDR
2. Disable john.smith Active Directory account
3. Block C2 IP (identified from Cobalt Strike beacon config) at firewall
4. Block svch0st.exe hash at EDR across all endpoints
5. Force password reset for any accounts used from compromised host

Short-term (within 24 hours):
6. Scan all endpoints for svch0st.exe and Cobalt Strike IOCs
7. Review all john.smith logons in past 30 days
8. Pull and preserve memory from DESKTOP-A1B2C3 before reimage
```

## Step 6 — Write IR Summary Report

```
IR REPORT — Incident #INC-2024-0315-001
Date: 2024-03-15 | Severity: HIGH | Status: Contained

Executive Summary:
A phishing email delivered a macro-enabled document to john.smith at 13:45 UTC.
The macro executed a Cobalt Strike beacon, leading to credential dumping on
DESKTOP-A1B2C3. No evidence of lateral movement or data exfiltration confirmed.
Containment completed by 15:00 UTC.

Timeline:
13:45 - Phishing email received (subject: "Q1 Invoice")
13:47 - WINWORD.EXE executed macro, spawned cmd.exe
13:48 - svch0st.exe downloaded and executed (Cobalt Strike)
14:32 - EDR alert: lsass credential dump attempted
14:45 - Analyst begins investigation
15:00 - Host isolated, account disabled, IOCs blocked

IOCs:
- File: svch0st.exe | SHA256: abc123...
- C2: 185.220.101.47:443
- Domain: cdn-updates[.]com

Remediation:
- Host DESKTOP-A1B2C3 reimaged
- john.smith account reset, MFA enforced
- Phishing filter updated to block macro documents

Recommendations:
- Disable macro execution for non-approved documents (GPO)
- Deploy email sandboxing for attachments
- Add Cobalt Strike IOC rule to SIEM
```

## Practice Sequence

1. CyberDefenders "CyberCorp Case 2" — structured enterprise IR
2. Blue Team Labs Online "Sticky Situation" — hands-on scenario
3. TryHackMe "Carnage" — PCAP plus endpoint logs combined
4. Time yourself — OSCP+ blue team challenges are time-boxed
