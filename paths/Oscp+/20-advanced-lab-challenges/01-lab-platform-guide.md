# Lab Platform Guide

Different platforms serve different purposes. Use the right one for where you are in your journey.

## Platform Comparison

| Platform | URL | Style | Best For |
|----------|-----|-------|----------|
| TryHackMe | tryhackme.com | Guided, browser-based | Foundations, beginners |
| HackTheBox | hackthebox.com | Independent exploitation | Intermediate/Advanced |
| OffSec Proving Grounds | offsec.com/labs/practice | OSCP-style machines | OSCP direct prep |
| VulnLab | vulnlab.com | Realistic AD chains | AD depth, team labs |
| HTB Pro Labs | hackthebox.com/hacking-labs | Full environment simulation | Advanced, Red Team |
| GOAD (local) | github.com/Orange-Cyberdefense/GOAD | Self-hosted multi-DC AD | Free AD lab, realism |

## Which Platform When

**Just starting**: TryHackMe "Jr Penetration Tester" learning path — guided, explains concepts, no frustration cliff.

**OSCP preparation**: OffSec Proving Grounds Practice. Machines are built by the same team that builds OSCP exam machines. Same OS versions, same vulnerability types, same difficulty calibration.

**AD attack chains**: VulnLab for realistic multi-hop chains. GOAD locally if you want unlimited practice at zero cost.

**Career development beyond OSCP**: HTB Pro Labs — Offshore (AD), RastaLabs (Red Team), Cybernetics (full enterprise).

## PG Practice vs HTB for OSCP

PG Practice is the better choice because:
- Same infrastructure team as OSCP exam
- Community writeups are available after 3 months (good for learning)
- "Try Harder" rating maps more closely to exam difficulty
- OffSec provides hints (limited) — HTB does not for active machines

## GOAD Setup (Free AD Lab)

```bash
# Requirements: VirtualBox, Vagrant, Python 3
git clone https://github.com/Orange-Cyberdefense/GOAD.git
cd GOAD
pip3 install ansible pywinrm
cd ad/GOAD/providers/virtualbox
vagrant up
# Provisions: 5 VMs, 2 domains, 3 DCs, multiple vulnerable configurations
```

Gives you: Kerberoastable accounts, AS-REP roasting targets, ACL abuse paths, GPO exploitation, full DA compromise chain — all local, all free.
