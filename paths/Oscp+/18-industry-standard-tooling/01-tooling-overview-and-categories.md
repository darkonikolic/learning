# Industry Standard Tooling Overview

Know what each tool is for, when to reach for it, and enough to get started. This phase is a reference map.

## Tooling by Category

| Category | Tools |
|----------|-------|
| Reconnaissance | Nmap, Masscan, Shodan, theHarvester, Amass, Recon-ng |
| Web Testing | Burp Suite Pro, OWASP ZAP, Nikto, Nuclei, SQLmap, ffuf, wfuzz |
| Exploitation | Metasploit, Sliver, Havoc, Cobalt Strike, searchsploit |
| AD / Windows | BloodHound, CrackMapExec/NetExec, PowerView, Impacket, Rubeus, Mimikatz |
| Credentials | Hashcat, John the Ripper, CrackStation |
| Post-Exploitation | Meterpreter, PEASS-ng, Ligolo-ng, Socat, Netcat |
| Defensive | Wireshark, Zeek, Suricata, Velociraptor, Splunk, Elastic, Sysmon, YARA |
| AppSec | Semgrep, Snyk, Trivy, Trufflehog, ZAP, Burp Suite |
| Reporting | Pwndoc, SysReptor, Dradis, Cherrytree |

## Coverage Map to Other Phases

```
Reconnaissance tools     → Phase 09 (Enumeration Methodology)
Web testing tools        → Phase 06 (Burp/HTTP), Phase 10 (Labs)
Exploitation frameworks  → Phase 11 (Exploitation Fundamentals)
AD/Windows tools         → Phase 13 (Active Directory Attacks)
Credential tools         → Phase 12 (Privilege Escalation)
Post-exploitation        → Phase 14 (Post-Exploitation)
Pivoting tools           → Phase 15 (Pivoting and Tunneling)
Defensive tools          → Phase 16 (Blue Team/SOC/IR)
AppSec tools             → Phase 17 (AppSec Secure SDLC)
```

## What to Know for Each Tool

```
1. What problem does it solve?
2. One-liner to get started with it
3. Where does it fit in the attack/defense chain?
4. What does it NOT do (so you reach for the right tool)?
```

## Tool Installation Baseline (Kali Linux)

```bash
# Most tools pre-installed in Kali
# Verify presence
which nmap burpsuite metasploit-framework bloodhound hashcat

# Install missing tools
sudo apt update
sudo apt install -y nmap masscan nikto gobuster ffuf john hashcat seclists

# Go-based tools
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Python-based tools
pip install impacket bloodhound trufflehog
```

## Key Wordlists (SecLists)

```bash
# Clone SecLists — essential for all enumeration
git clone https://github.com/danielmiessler/SecLists /usr/share/seclists
# or: apt install seclists

ls /usr/share/seclists/
# Discovery/    — directories, DNS, API endpoints
# Passwords/    — wordlists for cracking
# Usernames/    — username lists
# Fuzzing/      — payload lists for injection testing
```

## Tool Decision Flow

```
Need to find open ports fast?        → Masscan then Nmap
Need to find web content?            → ffuf or gobuster
Need to test web vulns manually?     → Burp Suite Pro
Need automated web vuln scan?        → Nuclei or ZAP
Need to compromise a Windows box?    → Metasploit or manual exploit
Need AD attack paths?                → BloodHound
Need to crack hashes?                → Hashcat
Need to escalate on Linux?           → LinPEAS then manual
Need to pivot through a network?     → Ligolo-ng
```
