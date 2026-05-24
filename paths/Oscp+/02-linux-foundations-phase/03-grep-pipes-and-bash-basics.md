# Unit 03 — grep, pipelines, and Bash basics

## Theme

Finding data and composing small shell programs.

## LabEx

Finish:

- **Text-Fu**

Add basic Bash:

- Variables  
- `if`  
- `for` / `while`  
- Exit codes  

## Commands to practice

`grep`, `find`, `locate`, `tee`, `xargs`, `awk '{print $1}'`, `sed 's/old/new/g'`

## Pipelines

Practice composing with `|`.

Example:

```bash
cat app.log | grep oauth
```

## Bash basics

Example script pattern:

```bash
#!/bin/bash
for f in *.log; do
  grep ERROR "$f"
done
```

## Exercise

```bash
find . -name "*.php"
find . -name "*.yaml"
grep oauth app.log
cat app.log | awk '{print $1}'
sed 's/oauth/oauth2/g' log.txt
```

## Topic checklist

- `grep`, `find`, `locate`  
- Pipes, `tee`, `xargs`  
- Bash variables and loops  
- Exit codes  

## Learning outcome

You can search a tree, filter logs, and write short loops without copy‑pasting fragile one‑liners you do not understand.
