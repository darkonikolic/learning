# The Try-Hard Protocol

How long to spend on a box before looking anything up. Stick to this — it's the difference between passing and failing OSCP.

## Time-Boxing Rules

| Time | Action |
|------|--------|
| 0–45 min | Work one attack vector fully |
| 45 min stuck | Re-enumerate. Don't pivot to hints yet. |
| 2 hours total | Check a hint (one sentence, not a walkthrough) |
| 3 hours total | Read only the first step of a writeup |
| After hint | Complete the exploitation yourself, no further reading |

## Re-Enumeration Checklist (Run Before Giving Up)

```bash
# Did you scan all ports?
nmap -sV -sC -p- -T4 target

# Did you check UDP?
nmap -sU --top-ports 100 target

# Did you run NSE scripts on each service?
nmap -p 80 --script http-enum,http-title,http-methods target
nmap -p 21 --script ftp-anon,ftp-bounce target

# Did you enumerate every found directory recursively?
gobuster dir -u http://target/found-dir/ -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt

# Did you check version numbers against known exploits?
searchsploit apache 2.4.49
searchsploit vsftpd 2.3.4
```

## Research Process When Stuck

```bash
# Step 1: local exploit DB
searchsploit [service] [version]

# Step 2: Google
# "[service] [version] exploit"
# "[service] [version] CVE"
# "HTB [boxname] hint" (not walkthrough)

# Step 3: ExploitDB
# exploitdb.com — filter by platform, type
```

## The Rule That Makes OSCP Possible

Never just read a walkthrough and move on. If you looked up the answer, you still run every command yourself. If you saw the exploit, you still execute it manually. Reading without executing builds no skill.

Boxes you struggled with are more valuable than boxes you solved easily — go back after a week and try from scratch.
