# Credential and Hash Tools

Crack what you capture. Identify the hash type first, then throw the right attack at it.

## Resources

- Hashcat example hashes: https://hashcat.net/wiki/doku.php?id=example_hashes
- SecLists passwords: https://github.com/danielmiessler/SecLists/tree/master/Passwords
- CrackStation (online): https://crackstation.net/
- hashes.com (online): https://hashes.com/en/decrypt/hash

## Identify Hash Type

```bash
# hashid
pip install hashid
hashid '$2y$10$qJ9YB2OkPBP2NM1RfDW4UOXJiLpRNrJb...'
hashid '5f4dcc3b5aa765d61d8327deb882cf99'

# hash-identifier
hash-identifier
# paste hash at prompt

# Hashcat auto-detect
hashcat --identify hash.txt
```

## Hashcat

```bash
# Install (Kali pre-installed, or)
apt install hashcat

# Mode reference (most common)
# -m 0     MD5
# -m 100   SHA1
# -m 1400  SHA-256
# -m 1000  NTLM
# -m 5600  NetNTLMv2
# -m 13100 Kerberos TGS-REP (Kerberoasting)
# -m 18200 Kerberos AS-REP (AS-REP Roasting)
# -m 22000 WPA2 (PMKID)
# -m 1800  sha512crypt $6$
# -m 3200  bcrypt $2*$
# -m 500   md5crypt $1$

# Dictionary attack
hashcat -m 1000 hashes.txt /usr/share/wordlists/rockyou.txt

# Dictionary + rules
hashcat -m 1000 hashes.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule
hashcat -m 1000 hashes.txt rockyou.txt -r /usr/share/hashcat/rules/rockyou-30000.rule

# Combine rule sets
hashcat -m 1000 hashes.txt rockyou.txt \
  -r /usr/share/hashcat/rules/best64.rule \
  -r /usr/share/hashcat/rules/toggles1.rule

# Brute force (mask attack)
hashcat -m 0 hashes.txt -a 3 ?u?l?l?l?d?d?d?d    # 8 chars: Upper+lower+4 digits
hashcat -m 0 hashes.txt -a 3 ?a?a?a?a?a?a         # 6 any chars

# Mask charset reference
# ?l = lowercase alpha
# ?u = uppercase alpha
# ?d = digits
# ?s = special chars
# ?a = all printable

# Show cracked results
hashcat -m 1000 hashes.txt rockyou.txt --show

# Resume session
hashcat --restore

# Use GPU (auto-detected)
hashcat -m 1000 hashes.txt rockyou.txt -d 1        # specify GPU device
```

## John the Ripper

```bash
# Install
apt install john

# Auto-detect and crack
john hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt

# Specify format
john hashes.txt --format=NT --wordlist=rockyou.txt
john hashes.txt --format=sha512crypt --wordlist=rockyou.txt

# List supported formats
john --list=formats | grep -i ntlm

# Show cracked
john hashes.txt --show

# Crack zip password
zip2john protected.zip > zip.hash
john zip.hash --wordlist=rockyou.txt

# Crack SSH key passphrase
ssh2john id_rsa > ssh.hash
john ssh.hash --wordlist=rockyou.txt

# Crack /etc/shadow
unshadow /etc/passwd /etc/shadow > combined.txt
john combined.txt --wordlist=rockyou.txt
```

## Wordlists

```bash
# rockyou.txt (standard — 14M passwords)
ls /usr/share/wordlists/rockyou.txt.gz
gunzip /usr/share/wordlists/rockyou.txt.gz

# SecLists (comprehensive collection)
apt install seclists
ls /usr/share/seclists/Passwords/

# Most useful:
/usr/share/seclists/Passwords/Leaked-Databases/rockyou-50.txt      # top 50
/usr/share/seclists/Passwords/Common-Credentials/10-million-password-list-top-100000.txt
/usr/share/seclists/Passwords/Default-Credentials/default-passwords.csv

# Generate custom wordlist from target website
cewl http://target.com -d 2 -m 5 -w custom-wordlist.txt
```

## Practical Hash Attack Examples

```bash
# NTLM (from secretsdump output)
# Administrator:500:aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c:::
hashcat -m 1000 ntlm.txt rockyou.txt -r rules/best64.rule

# Kerberoast TGS (from GetUserSPNs or Rubeus)
# $krb5tgs$23$*svc_sql$CORP.LOCAL$...
hashcat -m 13100 tgs.txt rockyou.txt -r rules/best64.rule

# AS-REP Roast (from GetNPUsers or Rubeus asreproast)
# $krb5asrep$23$user@corp.local:...
hashcat -m 18200 asrep.txt rockyou.txt

# NetNTLMv2 (from Responder capture)
# user::CORP:challenge:response:...
hashcat -m 5600 netntlm.txt rockyou.txt
```
