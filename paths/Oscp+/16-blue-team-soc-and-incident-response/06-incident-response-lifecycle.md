# Incident Response Lifecycle

IR process: PICERL. Structured response prevents chaos and limits damage.

## PICERL Framework

```
Preparation → Identification → Containment → Eradication → Recovery → Lessons Learned
```

## Phase 1 — Preparation

```
- Runbooks for common incident types (ransomware, phishing, insider)
- IR contacts: security team, legal, PR, HR, executive sponsor
- Backups verified and tested
- EDR/SIEM deployed and logging
- Network segmentation in place
- IR team trained and tabletop exercised
```

## Phase 2 — Identification

```bash
# Initial triage questions:
# What triggered the alert? (SIEM rule, EDR alert, user report)
# What is the affected system? (hostname, IP, owner, criticality)
# When did activity start? (first seen timestamp)
# Is this ongoing?

# Quick scope check — is there lateral movement?
# SIEM query: logons from affected host to other systems in last 24h
index=windows EventCode=4624 src_ip=<affected_host> | stats count by dest

# Check for related alerts on same host or same IOC
# Build initial IOC list: IPs, hashes, domains, usernames
```

## Phase 3 — Containment

```bash
# Isolate host (network quarantine — keep it on for forensics, just cut network)
# EDR: isolate host from console (Defender ATP, CrowdStrike, etc.)

# Disable compromised accounts
net user <username> /active:no                  # Windows local
Disable-ADAccount -Identity <username>          # AD

# Block IOCs at firewall/proxy
# IP block, domain block, hash block in EDR

# Preserve evidence BEFORE wiping
# Take memory dump: winpmem or Magnet RAM Capture
winpmem.exe memory.raw

# Disk image (if needed): FTK Imager or dd
```

## Phase 4 — Eradication

```bash
# Remove malware
# Delete malicious files, scheduled tasks, services, registry keys

# Close access vector
# Patch the exploited vulnerability
# Reset all credentials that may have been compromised
# Rotate service account passwords
# Revoke compromised certificates/tokens/API keys

# Verify clean — rescan with EDR, check persistence mechanisms
# HKLM\Software\Microsoft\Windows\CurrentVersion\Run
# schtasks /query /fo LIST /v
# sc query
```

## Phase 5 — Recovery

```bash
# Restore from clean backup (verify backup predates compromise)
# Rebuild if no clean backup exists — faster than cleaning complex malware

# Gradually restore services (don't rush — confirm clean)
# Monitor intensively post-recovery (attacker may return)
# Consider threat hunting across fleet for similar IOCs
```

## Phase 6 — Lessons Learned

```
Post-incident review (within 2 weeks):
- What happened? Full timeline.
- How was it detected? How could it have been detected earlier?
- What went well in the response?
- What needs improvement?
- What controls would have prevented this?
- Action items with owners and deadlines
```

## IR Report Structure

```
1. Executive Summary (1 page — business impact, timeline, status)
2. Technical Timeline (chronological, all events with timestamps)
3. Root Cause Analysis (how did attacker get in?)
4. Scope of Impact (affected systems, data, accounts)
5. IOC List (IPs, domains, hashes, file paths, registry keys)
6. Remediation Actions Taken
7. Recommendations (preventive controls, detection improvements)
```

## Practice

- TryHackMe "ItsyBitsy" — IR investigation room
- Blue Team Labs Online IR scenarios (follow the PICERL phases)
- CyberDefenders "CyberCorp Case 2" — full enterprise IR scenario
