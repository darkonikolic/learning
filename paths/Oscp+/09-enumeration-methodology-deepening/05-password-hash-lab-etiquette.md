# Password Cracking and Hash Identification

Only crack hashes from systems you own or have explicit authorization to test.

## Identify Hash Type

```bash
hashid 'hash_value_here'
hash-identifier   # interactive, paste hash
```

Common hash formats:

| Hash | Length | Example |
|------|--------|---------|
| MD5 | 32 hex | `5f4dcc3b5aa765d61d8327deb882cf99` |
| SHA1 | 40 hex | `5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8` |
| SHA256 | 64 hex | `...` |
| NTLM | 32 hex | looks like MD5 but different algorithm |
| bcrypt | starts with `$2y$` | `$2y$10$...` |
| NTLMv2 | `username::domain:challenge:hash` | from Responder capture |

## Hashcat Modes

| Mode | Hash Type |
|------|-----------|
| 0 | MD5 |
| 100 | SHA1 |
| 1000 | NTLM |
| 3200 | bcrypt |
| 13100 | Kerberos TGS (Kerberoasting) |
| 18200 | AS-REP (AS-REP roasting) |
| 22000 | WPA2 |
| 5600 | NTLMv2 |

## Crack Commands

MD5 with rockyou:

```bash
hashcat -m 0 hash.txt /usr/share/wordlists/rockyou.txt
```

NTLM with rules:

```bash
hashcat -m 1000 ntlm.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

Kerberoast TGS:

```bash
hashcat -m 13100 tgs_hashes.txt /usr/share/wordlists/rockyou.txt
```

AS-REP roast:

```bash
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt
```

## John the Ripper

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --format=NT hash.txt --wordlist=rockyou.txt
john --show hash.txt   # show cracked results
```

## Unshadow (Linux /etc/shadow)

```bash
unshadow /etc/passwd /etc/shadow > combined.txt
john combined.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

## Practice

TryHackMe "Crack the Hash" room — identifies and cracks multiple hash types in sequence.
