# LDAP Queries and DNS Enumeration

Enumerating AD users, groups, and structure from Linux using LDAP and DNS.

## LDAP Anonymous Bind (no credentials)

```bash
# Test if anonymous bind is allowed
ldapsearch -x -H ldap://DC_IP -b "dc=corp,dc=local"

# If it returns results — anonymous access is enabled
# If it returns "Invalid credentials" or empty — not allowed
```

## LDAP with Credentials

```bash
# Enumerate all users
ldapsearch -x -H ldap://DC_IP \
  -D "user@corp.local" -w 'Password123' \
  -b "dc=corp,dc=local" \
  "(objectClass=user)" sAMAccountName cn mail

# Enumerate all groups
ldapsearch -x -H ldap://DC_IP \
  -D "user@corp.local" -w 'Password123' \
  -b "dc=corp,dc=local" \
  "(objectClass=group)" cn member

# Find users with no preauthentication required (AS-REP roastable)
ldapsearch -x -H ldap://DC_IP \
  -D "user@corp.local" -w 'Password123' \
  -b "dc=corp,dc=local" \
  "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))" sAMAccountName

# Find users with SPN set (Kerberoastable)
ldapsearch -x -H ldap://DC_IP \
  -D "user@corp.local" -w 'Password123' \
  -b "dc=corp,dc=local" \
  "(&(objectClass=user)(servicePrincipalName=*))" sAMAccountName servicePrincipalName
```

## NetExec LDAP Enumeration

```bash
# Enumerate users with creds
nxc ldap DC_IP -u user -p 'Password123' --users
nxc ldap DC_IP -u user -p 'Password123' --groups
nxc ldap DC_IP -u user -p 'Password123' --password-not-required   # AS-REP roast candidates
nxc ldap DC_IP -u user -p 'Password123' --kerberoasting output.txt
```

## DNS Enumeration

```bash
# Find the DC via DNS SRV record
nslookup -type=SRV _ldap._tcp.dc._msdcs.corp.local

# Forward lookup of DC
nslookup corp.local DC_IP

# Zone transfer attempt (usually blocked)
dig axfr corp.local @DC_IP

# Enumerate common hostnames
for name in dc dc01 dc1 server fileserver mail; do
  nslookup $name.corp.local DC_IP 2>/dev/null
done
```

## nmap LDAP Scripts

```bash
nmap -p 389,636 --script ldap-search,ldap-rootdse DC_IP
nmap -p 389 --script ldap-brute --script-args ldap.base="dc=corp,dc=local" DC_IP
```

## Exercise

On a TryHackMe AD lab (Attacktive Directory room or similar):
1. Run `ldapsearch` with anonymous bind — does it return data?
2. If you have creds, run the user enumeration query — how many users?
3. Run the SPN query — any Kerberoastable accounts?
4. Run `nxc ldap` with `--users` — compare output to ldapsearch
