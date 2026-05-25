# Windows and Active Directory: Resources and Lab Setup

Set up the lab and install tools before working through the rest of this phase.

## Platforms

- TryHackMe "Active Directory Basics" room (free): https://tryhackme.com/room/activedirectorybasics
- HTB Academy "Introduction to Active Directory" module (free): https://academy.hackthebox.com/module/details/74
- TryHackMe "Attacktive Directory" room (guided attack lab): https://tryhackme.com/room/attacktivedirectory

## Local Lab Option

Download Windows Server 2019 eval (free, 180-day trial):  
https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019

Minimum setup: one Windows Server 2019 VM promoted to Domain Controller + one Windows 10 VM joined to the domain.  
Run both in VirtualBox or VMware on a host-only network.

## Install Tools on Kali

```bash
sudo apt update
sudo apt install -y bloodhound neo4j crackmapexec smbclient enum4linux ldap-utils nmap

# NetExec (modern crackmapexec replacement)
pip3 install netexec

# Impacket suite
pip3 install impacket

# Kerbrute
wget https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64 -O /usr/local/bin/kerbrute
chmod +x /usr/local/bin/kerbrute
```

## PowerShell Tools (on Windows VM)

```powershell
# Download PowerView
IEX (New-Object Net.WebClient).DownloadString('https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Recon/PowerView.ps1')

# Or download to disk
Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Recon/PowerView.ps1' -OutFile C:\Tools\PowerView.ps1
```

## Exercise

1. Complete TryHackMe "Active Directory Basics" room in full
2. Install all Kali tools above — verify each with `tool --help` or `tool -h`
3. Optional: build the local two-VM lab and confirm domain join works
