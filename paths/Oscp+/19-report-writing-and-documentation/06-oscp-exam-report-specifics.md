# OSCP Exam Report Specifics

The OSCP exam report is a pass/fail deliverable. Technical exploitation earns points; the report is what converts those points into a passing grade.

## Submission Requirements

- Format: PDF only
- Deadline: 24 hours after exam time ends (not 24 hours after you stop hacking)
- Submission: OffSec exam portal
- Use the OffSec-provided report template from PEN-200

## Required Content Per Machine

For every compromised machine, you must include:

1. Screenshot showing ALL of the following in ONE image:
   - `hostname` or `ipconfig`/`ifconfig` output
   - `whoami` output
   - Contents of `local.txt` or `proof.txt` (cat the file)
   - The file must be readable — not just proof of access

2. Full step-by-step exploitation chain:
   - Every command run
   - Every tool used with exact flags
   - Screenshots at each major step
   - Exact payloads used

3. For partial credit (local.txt only): same requirements — screenshot with hostname + whoami + local.txt content

## Active Directory Chain

Document end-to-end:
- Initial access method
- Each lateral movement step
- Privilege escalation on each hop
- Domain Admin proof: `whoami /all` showing Domain Admins membership, or `secretsdump` output on DC

## Common Failure Reasons

- Screenshot does not show `hostname` AND `whoami` AND file content in same frame
- Steps are not reproducible — "I ran a script" without specifying what script
- Missing `local.txt` screenshots (partial credit machines still need full documentation)
- Submitted wrong file — recheck you're uploading the correct PDF
- Report submitted after deadline (the 24-hour clock does not pause)

## Screenshot Discipline During Exam

- Take screenshots immediately after each step — you cannot reconnect after time expires
- Save to disk with descriptive names: `192.168.1.100-privesc-proof.png`
- After getting proof: screenshot first, then anything else
- If VPN disconnects: reconnect and re-screenshot before time runs out

## Practice Standard

Document every PG Practice and HTB machine as a full exam-style report. When you can produce a clean, complete report for a Medium machine in under 30 minutes, you have the right habit.
