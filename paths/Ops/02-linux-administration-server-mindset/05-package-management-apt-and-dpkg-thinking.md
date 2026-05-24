# Unit 05 — APT / dpkg ergonomics plus dependency humility

Exercise package lifecycle ethically on ephemeral hosts—for example reversible nginx experimentation when policy aligns; alternatively choose smaller CLI payloads.

Mindful sequences:

```bash
sudo apt install …
sudo apt remove …
dpkg -l | head                  # illustrative sampling only
```

## Mindset rehearsals

Enumerate repository trust sourcing, versioning drift, leftover configuration directories (`purge` ramifications), orphaned dependency fallout, destructive `autoremove` blindness—simulate planning before irreversible housekeeping.
