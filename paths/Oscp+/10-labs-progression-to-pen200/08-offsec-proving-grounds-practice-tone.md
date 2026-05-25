# OffSec Proving Grounds Practice

PG Practice is the closest simulation to the OSCP exam environment. Prioritize it over HTB once you've completed the Easy tier.

## Sign Up

offsec.com/labs/practice

- Community (free): limited daily machine time on select machines
- Subscription ($19/mo): full access to all machines

## Why PG Over HTB for OSCP Prep

| Feature | HTB | PG Practice |
|---------|-----|-------------|
| Machine style | CTF-flavored | OSCP exam-style |
| Flag names | user.txt / root.txt | local.txt / proof.txt |
| Difficulty naming | Easy/Med/Hard | Easy/Med/Hard (same as OSCP) |
| Official writeups | Community only | OffSec-provided after submission |
| OSCP correlation | Good | Best |

## Recommended Starting Machines

- **Potato** — Linux, web + PrivEsc
- **Nibbles** — Linux, common misconfig
- **Sunset** — Linux, multi-step

## How to Use PG Effectively

```bash
# Submit flags like OSCP
# local.txt = user-level shell
# proof.txt = root/SYSTEM shell

cat /home/user/local.txt
cat /root/proof.txt
```

After submitting: read the official OffSec writeup and compare your approach. Look for steps you missed or slower paths you took.

## Target

Solve 20+ PG Practice machines before enrolling in PEN-200. Machines you solve on PG are direct preparation for the exam — the style, difficulty, and documentation requirements are the same. Solving PG machines consistently is the best predictor of OSCP exam success.
