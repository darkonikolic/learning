# Unit 06 — SMB share visibility on owned Windows VMs

```bash
sudo apt install smbclient
smbclient -L localhost -U guest   # illustrative; adapt to authorised lab credentials
```

Document share naming patterns, DACL inheritance surprises, unintended world-readable artefacts—ethical disclosure mindset even when practising alone.
