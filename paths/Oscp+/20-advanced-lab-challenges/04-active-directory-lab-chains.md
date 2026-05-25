# Active Directory Lab Chains

AD exploitation is a progression from isolated techniques to chained multi-hop compromise. Build the skill in layers.

## Level 1 — Guided Learning

**TryHackMe "Attacktive Directory"** (free room, ~4 hours)
- Guided Kerberoasting, AS-REP roasting, DCSync
- Explains each technique before you execute
- Good for first exposure, not for exam prep

Outcome: understand what each attack does and why it works.

## Level 2 — Guided-to-Independent (HTB Retired Machines)

These have public writeups available — read after attempting independently.

**HTB "Forest"** (Linux DC)
- AS-REP roasting → get hash for account with pre-auth disabled
- BloodHound enumeration → find WriteDACL path
- Abuse WriteDACL → grant DCSync rights → dump NTDS

**HTB "Sauna"** (Windows DC)
- Username enumeration from website → AS-REP roasting
- Autologon credentials in registry → lateral movement
- BloodHound → DCSync path → dump all hashes

**HTB "Active"** (Windows — GPP password)
- SMB anonymous read → Groups.xml → decrypt cpassword
- Kerberoasting SPN account → crack hash → admin access

Commands for each technique:
```bash
# AS-REP Roasting
GetNPUsers.py DOMAIN/ -usersfile users.txt -no-pass -dc-ip $DC

# Kerberoasting
GetUserSPNs.py DOMAIN/user:password -dc-ip $DC -request

# DCSync
secretsdump.py DOMAIN/user:password@$DC

# BloodHound collection
bloodhound-python -d DOMAIN -u user -p password -c All -ns $DC
```

## Level 3 — Realistic Multi-Domain

**GOAD (local lab)**: 5 VMs, 2 domains, 3 domain controllers, multiple attack paths.
- northcitadel.local + sevenkingdoms.local
- Includes: Kerberoasting, AS-REP, ACL abuse, GPO attacks, cross-domain trusts
- Free, fully local: github.com/Orange-Cyberdefense/GOAD

Spend a week mapping all attack paths. Then reset and exploit from scratch without notes.

## Level 4 — Professional Simulation

**VulnLab chains** (vulnlab.com): Multi-machine chains requiring lateral movement and realistic privilege escalation paths.

**HTB Pro Labs "Offshore"**: Full AD environment, 14+ machines, realistic enterprise network. Requires Pro subscription (~$14/month).

## DA Compromise Checklist

Goal: execute this chain independently before OSCP exam.

```
[ ] Enumerate domain: users, groups, computers, trusts
[ ] Find AS-REP roastable accounts (no pre-auth required)
[ ] Find Kerberoastable accounts (SPNs set)
[ ] Crack hashes offline (hashcat -m 18200 / -m 13100)
[ ] Run BloodHound to find attack path to DA
[ ] Identify ACL abuse paths (GenericWrite, WriteDACL, ForceChangePassword)
[ ] Lateral movement with found credentials (WinRM, SMB, RDP)
[ ] Privilege escalation on each hop
[ ] DCSync from DA privileges: secretsdump.py
[ ] Extract all domain hashes
```
