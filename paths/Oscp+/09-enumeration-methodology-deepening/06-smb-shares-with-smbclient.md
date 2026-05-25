# SMB Enumeration Toolkit

SMB is one of the most exploitable services on Windows targets. Enumerate it thoroughly on every machine with port 445 open.

## List Shares

Null session (no credentials):

```bash
smbclient -L //target -N
```

With credentials:

```bash
smbclient -L //target -U username%password
```

## Connect to a Share

```bash
smbclient //target/sharename -U username%password
```

Inside smbclient:

```
ls               # list files
get filename     # download file
put localfile    # upload file
recurse ON       # enable recursive operations
mget *           # download all files
```

## Mount SMB Share

```bash
sudo mkdir /mnt/smb
sudo mount -t cifs //target/sharename /mnt/smb -o username=user,password=pass
ls /mnt/smb
sudo umount /mnt/smb
```

## NetExec (nxc) — Modern CrackMapExec

Null session enumeration:

```bash
nxc smb target -u '' -p '' --shares
nxc smb target -u 'guest' -p '' --shares
```

Authenticated enumeration:

```bash
nxc smb target -u user -p pass --shares
nxc smb target -u user -p pass --sessions
nxc smb target -u user -p pass --users
nxc smb target -u user -p pass --groups
```

Password spraying:

```bash
nxc smb target -u users.txt -p passwords.txt --continue-on-success
```

## nmap SMB Scripts

```bash
nmap -p 445 --script smb-enum-shares,smb-enum-users,smb-security-mode target
nmap -p 445 --script smb-vuln-ms17-010 target
nmap -p 445 --script smb-vuln-ms08-067 target
```

## High-Value Targets in Shares

- `SYSVOL` and `NETLOGON` shares — look for GPP files with passwords (`Groups.xml`, `Services.xml`)
- Backup shares — often contain config files, database dumps
- User home shares — look for scripts, config files, SSH keys

GPP password decode:

```bash
gpp-decrypt 'encrypted_cpassword_value_here'
```

## Practice

Run full SMB enumeration against Metasploitable2. Then TryHackMe "Network Services" room — SMB section.
