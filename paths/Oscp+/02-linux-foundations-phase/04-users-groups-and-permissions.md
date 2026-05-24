# Unit 04 — Users, groups, and permissions

## Theme

Who can access what on the system.

## LabEx

Finish:

- User Management  
- Permissions  

## Udemy — Linux Administration Bootcamp

Sections:

- Users  
- Permissions  

## Commands to practice

`chmod`, `chown`, `sudo`, `groups`

## Exercise

```bash
touch secret.txt
chmod 600 secret.txt
chmod 755 script.sh
```

Interpret a mode string such as `-rwxr-xr-x` in your own words (owner / group / others; read/write/execute).

## Topic checklist

- Users and groups  
- `sudo`  
- POSIX permissions (`rwx`)  
- `chmod` / `chown`  

## Learning outcome

You can set sane defaults for scripts and sensitive files and explain why a permission change fixes or breaks access.
