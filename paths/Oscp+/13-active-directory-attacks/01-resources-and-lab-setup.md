# AD Attacks: Resources and Lab Setup

Active Directory is the centerpiece of OSCP+ enterprise scenarios. Stand up a real lab before touching any other file in this phase.

## Resources

- HTB Academy: [Active Directory Enumeration & Attacks](https://academy.hackthebox.com/module/details/143)
- TCM Security: [Practical Ethical Hacking](https://academy.tcm-sec.com/p/practical-ethical-hacking-the-complete-course) — AD sections
- TryHackMe: [Active Directory Basics](https://tryhackme.com/room/winadbasics) + [Attacktive Directory](https://tryhackme.com/room/attacktivedirectory)
- VulnLab: [vulnlab.com](https://vulnlab.com) — realistic AD chains, closest to exam feel
- GOAD (Game of Active Directory): [github.com/Orange-Cyberdefense/GOAD](https://github.com/Orange-Cyberdefense/GOAD) — free, local, multi-domain

## Lab Options

**Option A — GOAD (free, local)**
```bash
git clone https://github.com/Orange-Cyberdefense/GOAD
cd GOAD
# Requires Vagrant + VirtualBox or VMware
vagrant up
```

**Option B — HTB Pro Labs**
- Offshore: large enterprise AD sim
- RastaLabs: red team focused, harder

## Tools to Install

```bash
# BloodHound + Neo4j
sudo apt install bloodhound neo4j -y
sudo neo4j start

# NetExec (CrackMapExec successor)
pip3 install netexec

# Impacket suite
pip3 install impacket

# Kerbrute
wget https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64
chmod +x kerbrute_linux_amd64 && mv kerbrute_linux_amd64 /usr/local/bin/kerbrute

# BloodHound Python ingestor
pip3 install bloodhound

# Certipy (ADCS attacks)
pip3 install certipy-ad
```

Rubeus and SharpHound: grab from [github.com/GhostPack](https://github.com/GhostPack) or a pre-compiled repo.

## Verification

```bash
nxc --version
impacket-GetUserSPNs --help
bloodhound-python --help
certipy --help
```

**Ethical scope:** All techniques in this phase apply only to labs you own or engagements with explicit written authorization.
