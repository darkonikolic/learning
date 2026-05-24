# Phase two — Networking foundations (goals, resources, lab setup)

Phase two ends when you can explain **packet path**, **why a firewall blocked something**, **DNS**, **NAT**, **subnets**, **routing**, basic **traffic capture**, and everyday **network debugging** — without treating networking as unexplained magic.

## Exit mindset

| Avoid | Aim for |
|-------|---------|
| “Networking is magic” | “I see the system and the flow.” |

You should articulate at least conceptually:

- How traffic moves **browser → resolver → routing → TCP → TLS → HTTP → server**.
- Typical failure classes: **wrong DNS**, **no route**, **blocked port**, **NAT hairpin**, **MTU fragmentation**, stale **ARP**/neighbor cache.

## Primary resources — Practical Networking

**Site:** [https://www.practicalnetworking.net/](https://www.practicalnetworking.net/)

Work through:

- OSI model  
- TCP vs UDP  
- IP addressing  
- Subnetting & CIDR  
- DNS  
- DHCP  
- NAT  
- ARP  
- Routing  
- Packet flow  

This is your **anchor** syllabus.

## Primary resources — Udemy (selected only)

**Course:** [Networking Fundamentals — CCNA start](https://www.udemy.com/course/complete-networking-fundamentals-course-ccna-start/)

If the slug changes, locate the enrollment page you purchased and substitute the authoritative URL yourself.

Topics to cover:

- OSI vs TCP/IP practical framing  
- IP addressing  
- Subnetting & CIDR  
- DNS  
- DHCP  
- NAT  
- Routing fundamentals  

**Skip for this phase:** Deep Cisco IOS lab grind, switching/VLAN internals at enterprise depth. **Outcome target is OSCP-aligned foundation**, not a CCNA trophy.

## Supplemental — NetworkChuck (spot use only)

**Channel:** [https://www.youtube.com/@NetworkChuck](https://www.youtube.com/@NetworkChuck)

Search when a topic does not “click”:

- “NetworkChuck OSI model”  
- “NetworkChuck TCP UDP”  
- “NetworkChuck subnetting”  

Not a substitute for Practical Networking sequence.

## TryHackMe

**Platform:** [https://tryhackme.com/](https://tryhackme.com/)

Rooms / paths:

1. Locate the **Wireshark**-style room and practise **captures ethically** — only hosts you control or THM-hosted targets.  
2. **Network Fundamentals** path modules.  

Later (after competence here): optional **Pre Security** warmup path if you rotate into Phase three materials.

## Subnet rehearsal (muscle memory)

**Site:** [https://subnettingpractice.com/](https://subnettingpractice.com/)

Use it as **short recurring practice** whenever you rotate IP math — rhythm is yours, not mandated here.

## Lab packages (Ubuntu VM)

```bash
sudo apt update
sudo apt install -y wireshark traceroute tcpdump dnsutils netcat-openbsd nmap curl
```

`wireshark` may prompt for capture permissions (`wireshark` group / capabilities) — configure once and document how you solved it.

## Deliverable for this primer file

Copy the **primary resource links** into your notes tool and schedule **three** Practical Networking sections you will finish first — in order — before hopping elsewhere.
