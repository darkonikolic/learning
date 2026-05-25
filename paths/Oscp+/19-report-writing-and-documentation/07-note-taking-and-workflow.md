# Note-Taking and Workflow

Good notes during the assessment enable good reports after. If you didn't write it down, it didn't happen.

## Note-Taking Tools

| Tool | Strengths | Best For |
|------|-----------|----------|
| Obsidian | Local, fast, markdown, graph view | Primary notes, OSCP exam |
| CherryTree | Tree structure, rich text + code blocks | Common in offensive community |
| Notion | Collaborative, templates, database views | Team engagements |
| tmux + vim | Zero overhead, always available | Quick terminal notes |

For OSCP exam: Obsidian or CherryTree. Local only — no cloud sync during exam.

## Folder Structure Per Engagement

```
/engagement-name/
  /recon/
    nmap-initial.txt
    nmap-full.txt
    nmap-udp.txt
    gobuster-80.txt
    subdomains.txt
  /exploitation/
    sqli-login-bypass.md
    smb-eternalblue.md
  /post-exploitation/
    linpeas-output.txt
    credentials-found.md
    pivot-notes.md
  /screenshots/
    01-nmap-open-ports.png
    02-web-app-login.png
    03-sqli-payload.png
    04-shell-whoami.png
    05-privesc-suid.png
    06-root-proof.png
  /report/
    draft.md
    final.pdf
```

## Screenshot Naming Convention

```
[target-ip]-[vulnerability]-[step]-[date].png

Examples:
192.168.1.100-sqli-auth-bypass-20240315.png
10.10.10.50-privesc-suid-root-proof-20240315.png
dc01-dcsync-ntds-dump-20240315.png
```

## During Assessment — What to Record

- Every command run and its output (copy to notes, not just terminal scroll)
- Every credential found: username, password, hash, service, source
- Every open port with service version
- Every failed attempt (saves you trying the same thing twice)
- Timestamps on key events (initial access, PrivEsc, proof captured)

## Credentials File Template

```
## Credentials Found

| User | Password/Hash | Type | Source | Service |
|------|--------------|------|--------|---------|
| admin | admin123 | plaintext | /config.php | MySQL |
| john | $6$abc...xyz | sha512crypt | /etc/shadow | SSH |
| svc_backup | NTLMhash | NTLM | secretsdump | AD |
```

## OSCP Exam Critical Rule

After exam time ends, you cannot reconnect to any machine. Take every screenshot before you move to the next task. There is no "I'll get that screenshot at the end."
