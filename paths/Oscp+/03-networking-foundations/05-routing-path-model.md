# Routing and path model

Understand how packets travel between networks. Required for understanding pivoting and why some hosts are reachable and others are not.

## Read the routing table

```bash
ip route
# Example output:
# default via 192.168.1.1 dev eth0 proto dhcp
# 192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
# 10.10.14.0/23 dev tun0 proto kernel scope link src 10.10.14.5

# Columns: destination | via (gateway) | dev (interface) | src (our IP)
# "default" = 0.0.0.0/0 = anything not matched by a specific route
```

## Trace the path

```bash
traceroute -n google.com           # numeric (no DNS), shows each hop's IP and latency
traceroute -n -T google.com        # TCP traceroute (bypasses ICMP filters)
mtr google.com                     # live traceroute + packet loss per hop (apt install mtr)
mtr --report google.com            # one-time report, good for documenting
```

## Add and remove static routes

```bash
# Add a route to reach 10.10.10.0/24 via 192.168.1.254
sudo ip route add 10.10.10.0/24 via 192.168.1.254

# Verify
ip route | grep 10.10.10

# Remove it
sudo ip route del 10.10.10.0/24 via 192.168.1.254

# Add default gateway
sudo ip route add default via 192.168.1.1
```

## Lab exercise — map your network

```bash
# 1. Print your routing table
ip route

# 2. Trace path to an internet host
traceroute -n 8.8.8.8

# 3. Trace path to local gateway
traceroute -n $(ip route | grep default | awk '{print $3}')

# 4. Check which interface traffic uses
ip route get 10.10.10.1            # shows which interface and gateway would be used
```

## Security relevance — pivoting

When you compromise a host inside a network, it may have routes to internal subnets you can't reach directly. Example:

```bash
# On compromised host:
ip route
# Shows: 172.16.0.0/24 dev eth1 — internal network you can now reach
# You add a route on your attacker machine through the tunnel:
sudo ip route add 172.16.0.0/24 via 10.10.14.5   # route through your tunnel
```

## Draw your lab diagram

On paper or in a text file: draw every host, its IP, its subnet, and the gateway that connects subnets. This is the first thing to do at the start of every CTF or pentest engagement.

## Practice

- TryHackMe "Extending Your Network": https://tryhackme.com/room/extendingyournetwork
- Practical Networking routing series: https://www.practicalnetworking.net/series/routing/routing/

## Completion bar

Read a routing table and explain each line. Add a static route, verify it, remove it. Trace a path with `mtr` and explain why any `***` hops appear.
