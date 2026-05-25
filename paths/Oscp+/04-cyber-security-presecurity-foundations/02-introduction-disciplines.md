# Security disciplines overview — roles, tools, and attack lifecycle

Five roles, what each does daily, and the attack/defense lifecycle end-to-end.

## Role comparison

| Role | Daily work | Core tools | Avg salary (US) |
|---|---|---|---|
| Penetration Tester | Find and exploit vulns in client systems | Burp Suite, Metasploit, nmap | $90–130k |
| Red Team Operator | Simulate adversary TTPs, evade defenses | Cobalt Strike, custom C2, AD tools | $110–160k |
| SOC Analyst | Monitor alerts, triage incidents, write detections | Splunk, ELK, SIEM platforms | $55–85k |
| AppSec Engineer | Review code, run DAST/SAST, fix vulns in SDLC | Semgrep, Burp, Snyk, CodeQL | $120–160k |
| Bug Bounty Hunter | Self-directed vuln hunting on scope targets | Burp Suite, custom recon scripts | Variable |

## Attack lifecycle

```
Recon → Scan → Exploit → Pivot → Post-exploitation → Report
```

- Recon: OSINT (LinkedIn, Shodan, WHOIS), subdomain enum, tech stack fingerprinting
- Scan: nmap port/service scan, vuln scan with Nessus/OpenVAS
- Exploit: use known CVE or manually exploit a misconfiguration
- Pivot: use compromised host to reach internal network
- Post-exploitation: dump creds, escalate privileges, maintain access
- Report: document findings with severity, evidence, and remediation steps

## Defense lifecycle

```
Monitor → Detect → Contain → Eradicate → Recover
```

- Monitor: collect logs from endpoints, network, apps into SIEM
- Detect: alert on anomalies — failed logins, unusual outbound, new admin accounts
- Contain: isolate affected host (pull network cable / firewall rule)
- Eradicate: remove malware, patch vuln, rotate creds
- Recover: restore from backup, verify clean state, resume operations

## Practice

TryHackMe "Careers in Cyber" room: https://tryhackme.com/room/careersincyber (free)
