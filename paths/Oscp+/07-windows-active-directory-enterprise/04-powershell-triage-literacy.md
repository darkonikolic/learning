# Unit 04 — PowerShell discipline for auditors

Structured exercises:

`Get-ChildItem`, `Get-Content`, `Get-Service`, `Get-Process`, `Select-String`

Composition rehearsal:

```
Get-Process | Sort-Object CPU -Descending | Select-Object -First 15
```

Aim for **repeatable scripted micro-queries** aiding triage—not one-off improvised typing alone.
