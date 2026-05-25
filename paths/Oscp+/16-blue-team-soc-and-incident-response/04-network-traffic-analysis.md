# Network Traffic Analysis

Identify C2, lateral movement, exfiltration, and tunneling in packet captures.

## Wireshark Filters

```wireshark
# Filter by port
tcp.port == 445
tcp.port == 4444

# HTTP POST requests only (data submission, possible exfil)
http.request.method == "POST"

# DNS queries containing suspicious strings
dns.qry.name contains "evil"
dns.qry.name matches ".*\.xyz$"

# All traffic to/from suspicious IP
ip.addr == 10.10.10.100

# Connections with large data transfer
tcp.len > 10000

# SMB traffic (lateral movement indicator)
smb || smb2

# Beaconing — regular interval connections (filter then check timing)
ip.dst == known_c2_ip

# TLS without valid SNI (suspicious encrypted traffic)
ssl.handshake.type == 1 && !ssl.handshake.extensions_server_name
```

## Tshark (Command Line Wireshark)

```bash
# Read PCAP and show HTTP requests
tshark -r capture.pcap -Y "http.request" -T fields -e ip.src -e http.host -e http.request.uri

# Extract DNS queries
tshark -r capture.pcap -Y "dns.qry.type == 1" -T fields -e dns.qry.name | sort | uniq -c | sort -rn

# Find large data transfers
tshark -r capture.pcap -T fields -e ip.src -e ip.dst -e tcp.len | awk '$3>5000' | sort -k3 -rn | head

# Follow TCP stream (stream number from Wireshark)
tshark -r capture.pcap -Y "tcp.stream eq 5" -z follow,tcp,ascii,5
```

## Zeek (Bro) — Structured Log Analysis

```bash
# Process PCAP with Zeek — generates structured logs
zeek -C -r capture.pcap

# Key log files generated:
# conn.log    — all connections (src, dst, port, bytes, duration)
# http.log    — HTTP requests and responses
# dns.log     — DNS queries and answers
# ssl.log     — TLS/SSL sessions
# files.log   — transferred files

# Parse conn.log — find high-volume connections
cat conn.log | zeek-cut id.orig_h id.resp_h id.resp_p duration orig_bytes | sort -k5 -rn | head

# Find long-duration connections (C2 keep-alive)
cat conn.log | zeek-cut id.orig_h id.resp_h duration | awk '$3 > 300' | sort -k3 -rn

# DNS tunneling — look for long domain names or high query counts
cat dns.log | zeek-cut query | awk 'length($1) > 50' | sort | uniq -c | sort -rn
```

## Suricata — IDS Rule Review

```bash
# Run Suricata against PCAP
suricata -r capture.pcap -l /tmp/suricata-output/

# Review alerts
cat /tmp/suricata-output/fast.log
cat /tmp/suricata-output/eve.json | python3 -m json.tool | grep -A5 '"event_type":"alert"'
```

## Key Attack Patterns to Identify

```
C2 Beaconing:     Regular interval (every 30/60/300s) connections to same IP
DNS Tunneling:    Long subdomains (>50 chars), high DNS query frequency
Data Exfil:       Large outbound POST/PUT, unusual ports, encrypted to unknown IP
Lateral Movement: SMB connections workstation-to-workstation, NTLM auth chains
Port Scanning:    Many connections with RST/no response, incrementing dest ports
```

## Free PCAP Practice

- malware-traffic-analysis.net — real malware PCAPs with full writeups
  https://www.malware-traffic-analysis.net/
- CyberDefenders — PCAP-based challenges
  https://cyberdefenders.org/
- TryHackMe "Wireshark: The Basics" and "Zeek" rooms
