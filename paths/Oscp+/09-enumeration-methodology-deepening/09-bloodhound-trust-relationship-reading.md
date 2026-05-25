# BloodHound — AD Attack Path Analysis

BloodHound maps AD relationships and finds attack paths to Domain Admin. Run it after getting any domain credentials.

## Install and Start

```bash
sudo apt install bloodhound neo4j

# Start neo4j first
sudo neo4j start
```

Browse to http://localhost:7474 → login with `neo4j/neo4j` → change password.

Start BloodHound:

```bash
bloodhound
```

Login with the neo4j credentials you just set.

## Collect Data

From Linux (bloodhound-python):

```bash
sudo pip3 install bloodhound
bloodhound-python -u user -p pass -d domain.local -c All -ns DC_IP
```

Creates ZIP file in current directory.

From Windows (SharpHound — run on Windows target):

```
SharpHound.exe -c All
SharpHound.exe -c All --ZipFilename output.zip
```

## Import Data

Drag and drop the ZIP file into the BloodHound GUI.

## Key Queries to Run Every Time

In BloodHound → Analysis tab:

```
Find Shortest Paths to Domain Admins
Find AS-REP Roastable Users
Find Kerberoastable Users with Most Privileges
Find Computers where Domain Users are Local Admin
Find All Domain Admins
Shortest Paths to Unconstrained Delegation Systems
```

## Mark Owned Nodes

Right-click any compromised user or computer → Mark as Owned. BloodHound then shows attack paths from your owned nodes.

## Reading Attack Paths

Each edge (arrow) in BloodHound is an exploitable relationship:

| Edge | Meaning |
|------|---------|
| `MemberOf` | Group membership |
| `AdminTo` | Local admin on computer |
| `HasSession` | User has active session on computer |
| `CanRCE` | Can execute code remotely |
| `GenericAll` | Full control over object |
| `WriteDacl` | Can modify object permissions |

Click any edge → click "?" → BloodHound shows the attack technique and tool commands.

## Practice

Download pre-built sample data: github.com/BloodHoundAD/BloodHound/tree/master/examples — import and run all default queries to learn the interface before using it on real AD.
