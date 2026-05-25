# Pivoting and Tunneling — Resources and Lab Setup

Essential resources and environment prep before you touch a single tunnel.

## Core Resources

- HTB Academy "Pivoting, Tunneling, and Port Forwarding" — free, excellent, covers all major tools
  https://academy.hackthebox.com/module/details/158
- OffSec PEN-200 Module 14 — Tunneling Through Deep Packet Inspection
- TryHackMe "Wreath" room — multi-hop pivoting scenario, start to finish
  https://tryhackme.com/room/wreath
- IppSec YouTube — search "pivoting" for HTB box walkthroughs

## Tools to Have Ready

```bash
# Install core tools
sudo apt install chisel sshuttle proxychains4 socat ncat -y

# Ligolo-ng (download binaries — proxy for attacker, agent for victim)
# https://github.com/nicocha30/ligolo-ng/releases

# Chisel (also download binary for victim delivery)
# https://github.com/jpillora/chisel/releases
```

## Lab Setup

Minimum viable lab: two isolated network segments.

```
Kali (attacker)
  └── eth0: 192.168.1.0/24  (your network)
  └── eth1: 10.10.10.0/24   (internal segment)

Pivot VM (e.g., Ubuntu)
  └── eth0: 192.168.1.50    (reachable from Kali)
  └── eth1: 172.16.0.50     (internal only)

Target VM
  └── eth0: 172.16.0.100    (only reachable through Pivot)
```

Use VirtualBox/VMware with host-only adapters and internal network adapters.

HTB Pro Labs "Offshore" and "RastaLabs" have realistic multi-segment environments.

## Key Mental Model

Pivoting = using a compromised host as a relay to reach otherwise unreachable networks.
Every technique below answers: how do I get tool traffic from my machine to a network I can't directly touch?
