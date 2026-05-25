# Progressing to Medium-Difficulty Boxes

Don't move to Medium until you're solving Easy boxes in under 90 minutes without hints.

## Signals You're Ready

- Solving Easy boxes consistently in under 90 min
- Enumeration feels automatic — you're not forgetting UDP, SMB, or secondary ports
- You know which exploit to try based on the service version without Googling first

## What Changes at Medium

- Multi-step exploitation: find credential in a file → spray it → use it to privesc
- Custom exploit modifications required (not just copy-paste from ExploitDB)
- Intentional rabbit holes — services that look exploitable but aren't
- PrivEsc requires chaining multiple misconfigs

## Approach Adjustments

Spend 30% more time on enumeration than you did at Easy tier. Most Medium failures happen because something was missed in recon, not because the exploit was too hard.

Common Medium-box failure points:
- Forgetting UDP ports (`nmap -sU --top-ports 100 target`)
- Not checking all found services (every open port has an attack surface)
- Not trying default credentials on every service
- Missing subdirectories under found directories

## Recommended HTB Retired Medium Boxes

- **Beep** — Elastix, multiple entry points, PrivEsc via sudo
- **Optimum** — Windows, HFS exploit, PrivEsc via kernel
- **Grandpa / Granny** — IIS WebDAV, classic Windows PrivEsc
- **Bastard** — Drupal RCE, Windows PrivEsc

## PG Practice Medium

OffSec Proving Grounds Practice Medium boxes are closer to OSCP exam difficulty than HTB Medium. After 3-4 HTB Medium boxes, switch to PG Practice. Track time per box in your notes — target under 2 hours per machine before enrolling in PEN-200.
