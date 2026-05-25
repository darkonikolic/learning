# Integration — end-to-end packet trace exercise

Trace a complete browser fetch from DNS query to TCP close. Match every Wireshark frame to a protocol step.

## Setup — capture everything

```bash
# Terminal 1: start capture (use eth0 or your active interface)
sudo tcpdump -i eth0 -w /tmp/full_trace.pcap &
TCPDUMP_PID=$!

# Terminal 2: make a plain HTTP request (not HTTPS — plaintext for learning)
curl -v http://example.com 2>&1 | tee /tmp/curl_output.txt

# Stop capture
kill $TCPDUMP_PID
```

## What you should find in the capture — frame by frame

```
1. DNS query (UDP port 53)
   → Your machine asks: "What is the IP for example.com?"

2. DNS response (UDP port 53)
   → DNS server replies: "93.184.216.34"

3. TCP SYN (flags [S])
   → Your machine opens connection to 93.184.216.34:80

4. TCP SYN-ACK (flags [S.])
   → Server acknowledges, opens connection

5. TCP ACK (flags [.])
   → Three-way handshake complete

6. HTTP GET request
   → GET / HTTP/1.1
   → Host: example.com

7. HTTP 200 OK response
   → Server sends back HTML body

8. TCP FIN (flags [F.])
   → Connection teardown begins
```

## Wireshark — label each frame

```bash
wireshark /tmp/full_trace.pcap
```

Apply these filters one at a time and note what you see:

```
dns                              # find frames 1 and 2
tcp.flags.syn == 1               # find frame 3
tcp.flags.syn == 1 && tcp.flags.ack == 1  # find frame 4
http                             # find frames 6 and 7
tcp.flags.fin == 1               # find frame 8
```

## Match curl output to Wireshark

```bash
cat /tmp/curl_output.txt
# curl shows:
# * Trying 93.184.216.34:80...    ← after DNS resolution (frames 1-2)
# * Connected to example.com       ← after TCP handshake (frames 3-5)
# > GET / HTTP/1.1                 ← frame 6
# < HTTP/1.1 200 OK                ← frame 7
```

## Command sequence — run and observe

```bash
# Step 1: resolve manually first
dig example.com +short

# Step 2: trace the route
traceroute -n example.com

# Step 3: banner grab on port 80
nc -w 3 example.com 80
GET / HTTP/1.0

# Step 4: full curl with timing
curl -w "\nDNS: %{time_namelookup}s\nConnect: %{time_connect}s\nTotal: %{time_total}s\n" \
     -o /dev/null -s http://example.com
```

## Self-check questions

- Which frame is the DNS query? Which is the response?
- How many TCP packets does the handshake take?
- In the HTTP GET, what headers does your curl send by default?
- What HTTP status code did you get?
- How does the connection close — RST or FIN?

## Practice

- TryHackMe "Wireshark: The Basics": https://tryhackme.com/room/wiresharkthebasics
- TryHackMe "Network Fundamentals" module: https://tryhackme.com/module/network-fundamentals
- Download a real HTTP pcap: https://wiki.wireshark.org/SampleCaptures#http

## Completion bar

Open a pcap of a full HTTP fetch, label the DNS/handshake/request/response/teardown frames using Wireshark filters, and explain each one — without notes.
