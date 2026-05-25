# Log Analysis Fundamentals

Reading logs like an analyst — find attacker activity in the noise.

## Windows Event Log Key IDs

| Event ID | Meaning | Why It Matters |
|---|---|---|
| 4624 | Successful logon | Who logged in, from where, what type |
| 4625 | Failed logon | Brute force indicator |
| 4648 | Logon with explicit credentials | Pass-the-hash, runas |
| 4662 | Directory service object access | AD enumeration/DCSync |
| 4720 | User account created | Persistence |
| 4728/4732/4756 | User added to group | Privilege escalation |
| 4688 | Process created | Command execution (needs audit policy) |
| 4698 | Scheduled task created | Persistence |
| 7045 | New service installed | Persistence, malware |
| 4776 | NTLM authentication | Lateral movement indicator |

## Reading Windows Event Logs

```powershell
# PowerShell — get failed logons
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} | Select-Object TimeCreated, Message | Format-List

# Get all logons from specific IP
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} | Where-Object {$_.Message -like "*192.168.1.100*"}

# Export to CSV for analysis
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4688} | Export-Csv c:\logs\processes.csv
```

## Linux Log Locations

```bash
# Authentication events
tail -f /var/log/auth.log          # Ubuntu/Debian
tail -f /var/log/secure            # RHEL/CentOS

# SSH brute force — look for repeated "Failed password"
grep "Failed password" /var/log/auth.log | awk '{print $11}' | sort | uniq -c | sort -rn | head

# Successful logins
grep "Accepted password\|Accepted publickey" /var/log/auth.log

# System events
journalctl -f                       # Live
journalctl --since "2024-01-01" --until "2024-01-02"
journalctl -u sshd --since "1 hour ago"
```

## Web Server Log Analysis

```bash
# Apache/Nginx access log — look for attack patterns
cat /var/log/apache2/access.log | awk '{print $9}' | sort | uniq -c | sort -rn
# Status codes: 200=success, 403=forbidden, 404=not found, 500=server error

# Find POST requests (data submission, upload attempts)
grep "POST" /var/log/apache2/access.log | grep -v "200"

# Find scanning activity (lots of 404s from one IP)
awk '$9==404 {print $1}' /var/log/apache2/access.log | sort | uniq -c | sort -rn | head

# Find suspicious user agents
grep -i "sqlmap\|nikto\|nmap\|masscan\|curl\|python" /var/log/apache2/access.log
```

## Quick Anomaly Patterns

```bash
# Logon outside business hours
# Multiple failed logins then success (brute force → compromise)
# New admin account created shortly after a logon
# Process created by unexpected parent (e.g., word.exe spawning cmd.exe)
# Lateral movement: logon type 3 (network) from workstation to workstation
```

## Practice

- TryHackMe "Windows Event Logs" room
- TryHackMe "Investigating Windows" room
- Blue Team Labs Online "Log Analysis" challenges
