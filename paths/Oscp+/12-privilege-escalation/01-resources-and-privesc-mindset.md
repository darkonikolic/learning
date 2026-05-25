# Privilege escalation — resources and mindset

PrivEsc is 40% of OSCP. Getting a low-priv shell is the halfway point — root or SYSTEM is the goal. Enumerate everything before assuming nothing works.

## Primary resources

| Resource | URL |
|----------|-----|
| TCM "Linux PrivEsc" (YouTube) | https://www.youtube.com/watch?v=ZTioFZDMrfE |
| TCM "Windows PrivEsc" (YouTube) | https://www.youtube.com/watch?v=_8xJaaQlpBo |
| TryHackMe Linux PrivEsc | https://tryhackme.com/room/linuxprivesc |
| TryHackMe Windows PrivEsc | https://tryhackme.com/room/windows10privesc |
| HackTricks | https://book.hacktricks.xyz/ |
| GTFObins | https://gtfobins.github.io/ |
| LOLBAS (Windows) | https://lolbas-project.github.io/ |

## Mindset

**Enumerate first — exploit second.** Rushing to kernel exploits without methodical enumeration wastes time and can crash services.

PrivEsc order of preference:
```
1. Sudo misconfiguration (easiest, most common)
2. SUID/SGID binary abuse
3. Cron job hijack / writable scripts
4. Weak service permissions (Windows)
5. Stored credentials
6. Path hijacking
7. Kernel exploit (last resort — can cause instability)
```

## Note-taking discipline

Track what you have checked in a checklist per box. OSCP has a time limit. Unticked items are unexplored attack surface.

```
[ ] sudo -l
[ ] SUID/SGID binaries
[ ] Cron jobs
[ ] World-writable directories/files
[ ] Stored credentials (config files, history)
[ ] Running services
[ ] Installed software versions
[ ] Kernel version
[ ] Network connections (pivot paths)
```

Never move to the next box assuming you have found nothing — check every item.
