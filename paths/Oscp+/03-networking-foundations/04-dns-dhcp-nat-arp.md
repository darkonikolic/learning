# DNS, DHCP, NAT, and ARP

These four protocols handle name resolution, address assignment, and address translation. All four appear in recon and pivoting.

## DNS — query records

```bash
dig google.com                           # A record (IPv4)
dig google.com AAAA                      # IPv6 address
dig google.com MX                        # mail servers
dig google.com TXT                       # SPF, DKIM, verification tokens
dig google.com NS                        # name servers
dig -x 8.8.8.8                           # reverse lookup (PTR)
dig @8.8.8.8 google.com                  # query specific DNS server
nslookup google.com                      # simpler alternative
host -t NS google.com                    # name servers via host command
```

## DNS record types

| Type | Purpose |
|------|---------|
| A | IPv4 address |
| AAAA | IPv6 address |
| MX | Mail server |
| CNAME | Alias (canonical name) |
| TXT | Arbitrary text (SPF, DKIM, verification) |
| NS | Name server |
| PTR | Reverse lookup |
| SOA | Zone authority info |

## DNS zone transfer (recon technique — lab targets only)

```bash
# Attempt zone transfer — reveals all DNS records if misconfigured
dig axfr @nameserver target.domain
# Example on intentionally vulnerable target:
dig axfr @nsztm1.digi.ninja zonetransfer.me
```

## ARP — layer 2 address resolution

```bash
arp -a                           # ARP cache (IP → MAC mappings)
ip neigh                         # same, modern syntax
# Wipe and re-populate cache:
sudo ip neigh flush all
ping -c 1 192.168.1.1 && arp -a | grep 192.168.1.1
```

## Wireshark — capture DNS traffic

```bash
sudo tcpdump -i eth0 -c 20 udp port 53 -w /tmp/dns.pcap
dig google.com
sudo tcpdump -r /tmp/dns.pcap -n
# In Wireshark: filter dns
# Observe: query (A?) and response (A answer section)
```

## DHCP and NAT — what to know

DHCP: `sudo journalctl | grep -i dhcp` — see what IP was assigned and when.

NAT: your RFC1918 address gets translated to a public IP at the router. Relevant when targeting DMZ hosts — understand which side of NAT you're on.

```bash
# Your private IP vs public IP
ip a show eth0                           # private (RFC1918)
curl -s https://ifconfig.me             # public (post-NAT)
```

## Practice

- TryHackMe "DNS in Detail": https://tryhackme.com/room/dnsindetail
- TryHackMe "What is Networking?": https://tryhackme.com/room/whatisnetworking
- Live zone transfer demo: `dig axfr @nsztm1.digi.ninja zonetransfer.me`

## Completion bar

Query A/MX/NS/TXT records for a domain, attempt a zone transfer against `zonetransfer.me`, capture DNS packets with tcpdump, and inspect with Wireshark filter `dns` — without notes.
