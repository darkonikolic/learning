# Blue Team, SOC, and Incident Response — Resources and Role Overview

Understand what defenders see. Invaluable for red teamers and required for OSCP+ defenders track.

## Free Training Platforms

- Blue Team Labs Online — free IR and forensics scenarios
  https://blueteamlabs.online/
- TryHackMe "SOC Level 1" path — foundational analyst skills
  https://tryhackme.com/path/outline/soclevel1
- TryHackMe "SOC Level 2" path — intermediate, threat hunting and IR
  https://tryhackme.com/path/outline/soclevel2
- HTB Academy "SOC Analyst" job role path
  https://academy.hackthebox.com/paths/jobrole/1
- LetsDefend.io — alert triage simulation, free and paid tiers
  https://letsdefend.io/
- CyberDefenders — free lab challenges with real PCAP/artifact analysis
  https://cyberdefenders.org/

## Paid / Advanced

- SANS FOR508: Advanced Incident Response and Threat Hunting (industry standard, expensive)
- SANS FOR610: Reverse Engineering Malware
- Blue Team Labs Online Pro — more scenarios

## Tools to Install

```bash
# Network analysis
sudo apt install wireshark tshark zeek suricata -y

# DFIR
sudo apt install volatility3 autopsy sleuthkit -y

# Threat intel / IOC analysis
sudo apt install yara -y

# CyberChef (browser-based analysis tool)
# https://gchq.github.io/CyberChef/

# Velociraptor (DFIR platform)
# https://github.com/Velocidex/velociraptor/releases
```

## SOC Analyst Role Overview

Tier 1: Alert triage — is this a real threat or a false positive?
Tier 2: Investigation — what happened, how far did it spread?
Tier 3: Threat hunting — find attackers before they trigger alerts.
IR team: Contain, eradicate, recover, report.

Key skill overlap with OSCP+: understanding attacker TTPs from the defender's perspective makes you a better attacker — and a better defender.

## Where to Start

1. TryHackMe SOC Level 1 path (free, structured)
2. CyberDefenders "CyberCorp Case 2" lab (realistic IR scenario)
3. Blue Team Labs Online "Phishing Analysis" series (email is the top attack vector)
