# Packet capture and analysis

Read traffic with tcpdump and Wireshark. Used for CTF analysis, credential sniffing on test networks, and understanding what exploits actually do on the wire.

## tcpdump — capture and filter

```bash
# Basic capture
sudo tcpdump -i eth0                             # live capture on eth0
sudo tcpdump -i any                              # all interfaces
sudo tcpdump -i eth0 -c 50                       # stop after 50 packets
sudo tcpdump -i eth0 -w /tmp/capture.pcap        # write to file
sudo tcpdump -r /tmp/capture.pcap -n             # read file, no DNS resolution

# Filter syntax
sudo tcpdump -i eth0 'tcp port 80'               # HTTP only
sudo tcpdump -i eth0 'tcp port 80 and host 10.10.10.1'
sudo tcpdump -i eth0 'not port 22'               # exclude SSH noise
sudo tcpdump -i eth0 'udp port 53'               # DNS only
sudo tcpdump -i eth0 -A 'tcp port 80'            # -A prints ASCII payload
```

## Wireshark display filters

```bash
# Open a pcap
wireshark /tmp/capture.pcap

# Filters to use in the filter bar:
ip.addr == 192.168.1.100           # all traffic to/from this IP
ip.src == 192.168.1.100            # only traffic FROM this IP
tcp.port == 443                    # HTTPS traffic
http.request.method == "GET"       # HTTP GET requests only
http.response.code == 200          # successful HTTP responses
dns.qry.name contains "evil"       # DNS queries with "evil" in name
tcp.flags.syn == 1                 # SYN packets only (new connections)
!(arp || dns || icmp)              # filter out noise
```

## Wireshark — follow a stream

1. Capture or open a pcap with HTTP traffic
2. Find any HTTP packet → right-click → Follow → TCP Stream
3. Red = client sent, Blue = server sent
4. Useful for: reading HTTP credentials, seeing POST body, extracting file transfers

## Analyze sample PCAPs

```bash
# Download sample malware traffic PCAPs for analysis
# Source: https://www.malware-traffic-analysis.net/training-exercises.html
# Or use Wireshark sample captures: https://wiki.wireshark.org/SampleCaptures

# Quick analysis workflow:
sudo tcpdump -r sample.pcap -n | head -30                  # quick overview
sudo tcpdump -r sample.pcap -n 'tcp port 80' | grep "GET"  # HTTP requests
# Then open in Wireshark for deeper inspection
```

## Lab exercise — capture a full HTTP transaction

```bash
# Terminal 1: start capture
sudo tcpdump -i lo -w /tmp/http_lab.pcap 'tcp port 8080' &

# Terminal 2: start HTTP server, make request
python3 -m http.server 8080 &
curl http://localhost:8080/

# Stop both
kill %2; kill %1

# Analyze
sudo tcpdump -r /tmp/http_lab.pcap -n
wireshark /tmp/http_lab.pcap &
# Filter: http — find GET request and 200 response
# Follow TCP stream — see full exchange
```

## Practice

- TryHackMe "Wireshark: The Basics": https://tryhackme.com/room/wiresharkthebasics
- TryHackMe "Wireshark: Packet Operations": https://tryhackme.com/room/wiresharkpacketoperations
- Malware traffic analysis exercises: https://www.malware-traffic-analysis.net/training-exercises.html

## Completion bar

Capture traffic with tcpdump using a BPF filter, open in Wireshark, apply display filters for IP/port/protocol, follow a TCP stream, and identify what the client requested and what the server returned.
