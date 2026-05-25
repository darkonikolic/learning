# Lab Machine Note-Taking Template

Use this template for every machine. One file per machine. Store in a `labs/` directory.

## Template

```markdown
## Target: [IP/hostname]
## Date: YYYY-MM-DD
## Platform: [TryHackMe / HTB / PG]
## Difficulty: [Easy / Medium / Hard]

### Recon
- Ports open:
- Services:
- OS guess:

### Web Enumeration
- Directories found:
- Interesting pages:
- Tech stack:

### Exploitation
- Vulnerability:
- CVE (if applicable):
- Exploit used:
- Payload:
- Command run:

### Post-Exploitation
- User gained:
- PrivEsc vector:
- Root/SYSTEM gained:

### Credentials Found
-

### Flags
- user.txt:
- root.txt / local.txt / proof.txt:

### Dead Ends
- What I tried that didn't work:

### Time Spent
- Total:
```

## Screenshot Policy

Every flag: run this in the same terminal window before screenshotting:

```bash
hostname && whoami && cat /home/user/user.txt
hostname && whoami && cat /root/root.txt
```

For Windows:
```cmd
hostname && whoami && type C:\Users\user\Desktop\user.txt
hostname && whoami && type C:\Users\Administrator\Desktop\root.txt
```

Name screenshot files consistently:
- `targetname_user_flag.png`
- `targetname_root_flag.png`

Use Flameshot (`flameshot gui`) or the built-in screenshot shortcut on your OS.

## Why This Matters

OSCP exam requires a written report with screenshots proving you owned each machine. Missing a screenshot during the exam costs points you cannot recover. Build this habit on every practice machine now.
