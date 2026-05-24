# Unit 08 — Integration drills and Phase one completion criteria

## Theme

**Closed‑book style** rehearsal (no cheating with search during the drill block — then verify gaps afterward).

## Scenarios (do without looking up)

1. Locate a relevant log file for a failing service scenario you invent on your VM.  
2. Filter that log with `grep`.  
3. Change permissions on a file to match two different intent cases (secret vs runnable script).  
4. Restart or reload a practice service with `systemctl`.  
5. Find a process by pattern; terminate it cleanly.  
6. Install a small package you have not installed before (then remove if you wish).

Toolkit you should actively use:

`find`, `grep`, `chmod`, `systemctl`, `journalctl`, `kill`, `apt`

## Phase one exit bar (skills)

Commands you should handle **without relying on external search mid‑session** for basic flags:

`grep`, `find`, `chmod`, `chown`, `ps`, `kill`, `systemctl`, `journalctl`, `curl`, `ssh`, `scp`, `tail`, `less`, `cat`, `apt`, `sudo`

Concepts you must be able to explain briefly:

| Area | Checkpoint |
|------|-------------|
| Filesystem | Where things live; absolute vs relative paths |
| Permissions | Users, groups, `rwx`, when `sudo` is appropriate |
| Processes | PID, stopping processes, basics of service supervision |
| Logs | Finding recent errors; journal vs files |
| Text | Pipes; simple `grep`/`awk`/`sed` workflows |
| Bash | Variables, loops, exit codes |

## Stretch (optional sanity)

Rebuild one exercise from Units 01–07 from memory once per topic.

## Deliverable

Write a half‑page note: **three weaknesses** surfaced during Unit 08 and **one deliberate repetition** you plan explicitly (no implied calendar).
