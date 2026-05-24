# Unit 07 — Bash iteration, branching, guard-railed scripting habits

Iteration illustration:

```bash
#!/usr/bin/env bash
for f in *.log; do
  grep ERROR "$f" || true
done
```

Author `backup.sh` compressing rotations, relocating generations, pruning aged snapshots—with dry rehearsals before trusting destructive trims.

Articulate conscientious quoting, purposeful exit signalling, restrained `errexit` adoption balancing diagnostics friendliness organisational norms prescribe.
