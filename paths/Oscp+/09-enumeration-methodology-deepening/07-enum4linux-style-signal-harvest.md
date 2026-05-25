# Linux/Windows Enumeration — User and Group Harvesting

Extract users, groups, shares, and password policy before exploiting. Targets must be systems you own or are authorized to test.

## enum4linux-ng (preferred over original enum4linux)

```bash
sudo apt install enum4linux-ng
enum4linux-ng -A target -oA scans/enum4linux
```

`-A` runs all checks. Output includes: users, groups, shares, OS info, password policy.

## enum4linux (classic)

```bash
sudo apt install enum4linux
enum4linux -a target
```

Extract user list from output:

```bash
enum4linux -a target | grep "user:" | cut -d[ -f2 | cut -d] -f1 > users.txt
```

## rpcclient

Connect with null session:

```bash
rpcclient -U "" target -N
```

Inside rpcclient:

```
enumdomusers              # list domain users
enumdomgroups             # list domain groups
queryuser 0x3e8           # get user info by RID
querydispinfo             # user display info
netshareenumall           # list all shares
```

## Lookupsid (Impacket)

Enumerate SIDs to find users:

```bash
lookupsid.py anonymous@target
lookupsid.py domain/user:pass@target
```

## Kerbrute — User Enumeration (No Creds Needed)

Enumerate valid domain users via Kerberos pre-auth errors:

```bash
kerbrute userenum --dc target -d domain.local /usr/share/seclists/Usernames/xato-net-10-million-usernames-ug.txt
```

Save valid users:

```bash
kerbrute userenum --dc target -d domain.local userlist.txt -o valid_users.txt
```

## Build User Wordlist

Combine sources:

```bash
# From enum4linux
enum4linux -a target | grep "user:" | cut -d[ -f2 | cut -d] -f1 > users.txt

# From LDAP (if port 389 open)
ldapsearch -x -H ldap://target -b "DC=domain,DC=local" "(objectClass=person)" sAMAccountName 2>/dev/null | grep sAMAccountName | awk '{print $2}' >> users.txt

# From web app (found in source, profiles, error messages) — add manually
sort -u users.txt -o users.txt
```

## Practice

TryHackMe "Attacktive Directory" room uses rpcclient and enum4linux as first enumeration steps.
