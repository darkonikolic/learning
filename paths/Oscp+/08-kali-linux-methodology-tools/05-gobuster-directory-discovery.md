# Unit 05 — Structured directory probing with Gobuster

```bash
sudo apt install gobuster
gobuster dir -u http://localhost:8080 -w /usr/share/wordlists/dirb/common.txt
```

Explain why unexpected `/debug`, `/internal`, dormant `/admin` artefacts matter defensively—even when benign in your scaffold.
