# Why Reporting Matters

A technically perfect pentest with a bad report delivers zero value. The report is what clients actually pay for — it's the only artifact they keep after you leave.

## Why It's Critical

- **OSCP exam**: you must submit a professional report to pass, even if you fully compromised every machine
- **Job applications**: sample reports are routinely requested in pentest hiring interviews
- **Client relationship**: a clear report prevents re-testing disputes and proves scope coverage
- **Legal protection**: documents what was tested, when, and what was found

## Resources

- TCM Security sample pentest report: github.com/hmaverickadams/TCM-Security-Sample-Pentest-Report
- OffSec report template: provided inside PEN-200 course materials
- HackTricks reporting section: book.hacktricks.xyz (search "pentest report")

## Report Management Tools

| Tool | Use Case | URL |
|------|----------|-----|
| Ghostwriter | Full engagement management, finding library | ghostwriter.wiki |
| Dradis | Collaborative report building, integrates tool output | dradisframework.com |
| Obsidian | Local markdown notes → export to report | obsidian.md |
| Notion | Collaborative, good for templates | notion.so |

## What "Good" Looks Like

Read the TCM Security sample report on GitHub before writing anything. It demonstrates:
- Executive summary that a CFO can understand
- Findings with reproducible steps
- Evidence that is clearly labelled and timestamped
- Remediation that is actionable, not generic

## Minimum Viable Practice

Document every single HTB or PG machine you solve as a mini-report. Force yourself to write:
1. Summary of what you found
2. Step-by-step exploitation with screenshots
3. Remediation recommendation

After 10 machines, report writing becomes muscle memory.
