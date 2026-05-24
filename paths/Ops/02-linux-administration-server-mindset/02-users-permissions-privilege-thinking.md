# Unit 02 — Users, ownership, permission bits, audited privilege escalation

Tools: `chmod`, `chown`, `groups`, `sudo`, `whoami`, `id`.

Interpret `-rwxr-xr-x` triplets distinctly for owners, groups, and others—note differing semantics **files vs directories** (execute on directory ≈ traversal / lookup permission).

Controlled experiment:

```bash
touch secret.txt
chmod 600 secret.txt
chmod 755 deploy.sh   # when ethically present inside disposable lab artefacts
sudo useradd -m testuser   # later remove cleanly with symmetrical housekeeping
```

## Mindset emphasis

Incidents originate often from unintended ownership drift, brittle `sudoers` expectations, careless world-readable sensitive paths—practice reading listings like calm pager introspection rehearsals.
