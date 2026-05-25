# AD Enumeration with BloodHound

BloodHound maps AD relationships and attack paths visually. Always run it first — it tells you exactly where to aim.

## Data Collection

**From Linux (no domain-joined machine needed):**
```bash
bloodhound-python -u user -p 'Password123' -d domain.local -c All -ns DC_IP
# Outputs JSON files in current directory
```

**From Windows (domain-joined box, SharpHound):**
```powershell
.\SharpHound.exe -c All
# Produces a ZIP — exfil and import to BloodHound GUI
```

**With just a hash (PtH collection):**
```bash
bloodhound-python -u user --hashes :NTLM_HASH -d domain.local -c All -ns DC_IP
```

## Import and Analyze

```bash
# Start services
sudo neo4j start
bloodhound &
# Default creds: neo4j / neo4j (change on first login)
```

Drag-and-drop the JSON files (or ZIP) into the BloodHound GUI upload area.

## Key Queries to Run Every Time

In BloodHound GUI → Analysis tab:

1. **Find all Domain Admins** — see who already has DA
2. **Shortest Paths to Domain Admins** — your primary attack path
3. **Shortest Path to DA from Owned** — mark your current user as Owned first
4. **Find AS-REP Roastable Users** — quick wins
5. **Find Kerberoastable Users** — service accounts with SPNs
6. **Find Computers with Unconstrained Delegation** — high-value targets

## Mark Nodes as Owned

Right-click any node → Mark as Owned. Do this for every account/machine you compromise. Re-run "Shortest Path from Owned" after each escalation.

## Custom Cypher Queries

```cypher
-- All users with SPN (Kerberoastable)
MATCH (u:User {hasspn:true}) RETURN u.name

-- Users with AdminTo edges
MATCH (u:User)-[:AdminTo]->(c:Computer) RETURN u.name, c.name
```

Add custom queries in BloodHound GUI → Queries → + icon.

**Practice target:** GOAD lab — run BloodHound, find all paths to ESSOS.LOCAL Domain Admin.
