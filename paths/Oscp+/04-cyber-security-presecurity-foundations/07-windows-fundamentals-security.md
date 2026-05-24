# Unit 07 — Windows fundamentals for security newcomers

## Theme

Operational literacy on Microsoft's surface area.

## TryHackMe clusters

Sequential Windows fundamentals modules numbered typically 1–3 (titling rotates).

## VM exercises — PowerShell

```powershell
Get-Process | Select-Object -First 15
Get-Service | Where-Object Status -EQ 'Running' | Select-Object -First 15
hostname
whoami
```

Classic shell auxiliaries still matter:

```
tasklist
ipconfig /all
net user
```

## Focus lenses

Filesystem ACL intuition, registry mention only as hive-of-misconfigs placeholder, Windows services escalation class awareness without exploit detail yet, **UAC** high-level—not bypass catalog.

## Learning outcome

You stop treating Windows internals as unknowable blobs—you ask structured triage questions about identity, privileges, services, exposures.
