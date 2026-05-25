# Defensive Tools

SOC and IR tooling. Know these as both a defender and to understand what attackers are evading.

## Resources

- Sysmon config: https://github.com/SwiftOnSecurity/sysmon-config
- Velociraptor docs: https://docs.velociraptor.app/
- Splunk free dev license: https://www.splunk.com/en_us/download.html
- Elastic Security: https://www.elastic.co/security

## Wireshark (Packet Analysis)

```bash
# Capture on interface
wireshark &
tshark -i eth0 -w capture.pcap

# Read pcap
tshark -r capture.pcap

# Filter syntax (display filters)
tshark -r capture.pcap -Y "http.request.method == POST"
tshark -r capture.pcap -Y "ip.addr == 192.168.1.10"
tshark -r capture.pcap -Y "dns"
tshark -r capture.pcap -Y "tcp.port == 4444"   # look for C2
tshark -r capture.pcap -Y "smb2"               # SMB traffic

# Extract HTTP objects
tshark -r capture.pcap --export-objects http,/tmp/http-objects/
```

## Zeek (Network Security Monitoring)

```bash
# Install
apt install zeek

# Analyze PCAP offline
zeek -r capture.pcap

# Live capture
zeek -i eth0

# Output logs (conn.log, http.log, dns.log, ssl.log, files.log)
cat conn.log | zeek-cut id.orig_h id.resp_h id.resp_p proto duration
cat http.log | zeek-cut ts host uri user_agent status_code
cat dns.log | zeek-cut ts query qtype_name answers

# Look for beaconing (regular intervals in conn.log)
cat conn.log | zeek-cut id.orig_h id.resp_h duration | sort | uniq -c | sort -rn
```

## Suricata (IDS/IPS)

```bash
# Install
apt install suricata

# Test against PCAP
suricata -r capture.pcap -l /tmp/suricata-logs/

# Live IDS mode
suricata -c /etc/suricata/suricata.yaml -i eth0

# View alerts
tail -f /var/log/suricata/fast.log
cat /var/log/suricata/eve.json | jq 'select(.event_type=="alert")'

# Update Emerging Threats rules
suricata-update
```

## Sysmon (Windows Endpoint Telemetry)

```powershell
# Install with config (use SwiftOnSecurity config)
.\Sysmon64.exe -accepteula -i sysmonconfig-export.xml

# View logs
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" | Select-Object -First 20

# Key Event IDs
# 1  — Process creation (command line)
# 3  — Network connection
# 7  — Image loaded (DLL)
# 8  — CreateRemoteThread (process injection)
# 10 — Process access (credential dump)
# 11 — FileCreate
# 13 — RegistryEvent
# 22 — DNS query

# Forward to Splunk/Elastic via Winlogbeat
```

## Velociraptor (DFIR + EDR)

```bash
# Start server
./velociraptor-v0.72-linux-amd64 config generate > server.config.yaml
./velociraptor-v0.72-linux-amd64 --config server.config.yaml frontend

# Deploy agent on endpoint and connect to server
# GUI at https://localhost:8889

# Key VQL queries (Velociraptor Query Language)
# Hunt for running processes:
SELECT Pid, Name, Exe, CommandLine FROM pslist()

# Find files modified recently:
SELECT FullPath, Mtime FROM glob(globs="C:/Users/*/AppData/Roaming/*") WHERE Mtime > "2024-01-01"

# Collect browser artifacts:
SELECT * FROM Artifact.Windows.Applications.Chrome.History()
```

## Splunk (SIEM — SPL Queries)

```bash
# Start Splunk (free dev license, 500MB/day)
/opt/splunk/bin/splunk start

# Core SPL queries
# Failed logins
index=windows EventCode=4625 | stats count by Account_Name, Source_Network_Address

# Lateral movement (logon type 3)
index=windows EventCode=4624 Logon_Type=3 | stats count by Account_Name, Workstation_Name

# Process execution with Sysmon
index=sysmon EventCode=1 | table Time, Computer, User, CommandLine

# DNS queries to suspicious domains
index=dns | stats count by query | sort -count
```

## YARA (Malware Pattern Matching)

```bash
# Install
apt install yara

# Example rule
cat > detect_mimikatz.yar << 'EOF'
rule Mimikatz {
    strings:
        $s1 = "sekurlsa::logonpasswords" ascii
        $s2 = "lsadump::dcsync" ascii
        $s3 = "mimikatz" ascii nocase
    condition:
        2 of them
}
EOF

# Scan file
yara detect_mimikatz.yar suspicious.exe

# Scan directory
yara -r detect_mimikatz.yar /suspect/directory/

# YARA rules library
# https://github.com/Yara-Rules/rules
```

## TheHive (Incident Management)

```bash
# Docker deploy
docker-compose up -d   # using official compose file

# Create case via API
curl -XPOST http://localhost:9000/api/case \
  -H "Authorization: Bearer $THEHIVE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"title":"Suspicious C2 Traffic","severity":3,"tlp":2}'
```
