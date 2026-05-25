# OSI, TCP/IP, TCP vs UDP, and first captures

Understand the layered model in terms of what breaks at each layer and what tools operate where. Then capture real traffic.

## OSI layers — practical mapping

| Layer | Name | What fails here | Tools |
|-------|------|-----------------|-------|
| 7 | Application | App crashes, protocol mismatch | curl, browser |
| 4 | Transport | Wrong port, firewall dropping packets | ss, nmap |
| 3 | Network | Wrong route, no gateway, IP unreachable | ping, traceroute, ip route |
| 2 | Data Link | MAC mismatch, switch config | arp, ip neigh |
| 1 | Physical | Cable, NIC, RF | hardware |

## TCP three-way handshake

```
Client          Server
  |---SYN-------->|
  |<--SYN-ACK-----|
  |---ACK-------->|   connection established
  |---DATA------->|
  |<--ACK---------|
  |---FIN-------->|   teardown
  |<--FIN-ACK-----|
```

## TCP vs UDP

| | TCP | UDP |
|-|-----|-----|
| Connection | Yes (handshake) | No |
| Reliability | Yes (retransmit) | No |
| Ordering | Yes | No |
| Speed | Slower | Faster |
| Use cases | HTTP, SSH, SMTP | DNS, NTP, DHCP, VoIP |

## Basic connectivity commands

```bash
ping -c 4 8.8.8.8                    # ICMP echo — is host reachable?
traceroute google.com                # hop-by-hop path (Layer 3)
traceroute -n google.com             # no DNS resolution (faster)
ss -tulpn                            # local TCP/UDP listeners
```

## Capture the TCP handshake with tcpdump

```bash
# Terminal 1 — start capture
sudo tcpdump -i eth0 -c 20 tcp -w /tmp/handshake.pcap

# Terminal 2 — generate traffic
curl -s http://example.com > /dev/null

# Read the capture
sudo tcpdump -r /tmp/handshake.pcap -n
# Look for: [S] SYN, [S.] SYN-ACK, [.] ACK
```

## Wireshark — observe the handshake

```bash
wireshark /tmp/handshake.pcap
```
- Filter: `tcp.flags.syn == 1` — see SYN packets only
- Filter: `tcp` — all TCP traffic
- Right-click a packet → Follow → TCP Stream — see full conversation

## Practice

- TryHackMe "OSI Model" room: https://tryhackme.com/room/osimodelzi
- TryHackMe "Packets and Frames": https://tryhackme.com/room/packetsframes
- Practical Networking OSI series: https://www.practicalnetworking.net/series/packet-traveling/packet-traveling/

## Completion bar

Capture a TCP handshake with tcpdump, open it in Wireshark, identify SYN/SYN-ACK/ACK packets — without instructions.
