# Unit 02 — Shell hygiene, journaling & repeatable labs

Treat course installation plus update cadence academically (snapshot or rollback readiness first).

Practice:

```bash
sudo apt update && sudo apt full-upgrade -y    # consciously; know rollback story
mkdir -p securitylab && cd securitylab
history | grep nmap                             # habitual audit echoes
grep -Rn pattern .                               # restrained scope first
curl -I https://localhost/placeholder          # benign reachability rehearsals only
```

Outcomes: literate APT usage, journaling command rationales—not blind copy-pasta.
