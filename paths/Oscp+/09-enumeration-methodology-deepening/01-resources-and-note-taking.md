# Resources and Note-Taking Setup for Enumeration

Set up your note-taking and lab environment before starting any machine.

## Learning Platforms

- TryHackMe "Jr Penetration Tester" path — structured, beginner-to-intermediate
- HTB Academy "Penetration Tester" job role path — free with registration, covers AD enumeration
- TryHackMe "Nmap", "Content Discovery", "Attacktive Directory" — individual rooms for specific tools

## Note-Taking Tools

Obsidian — recommended: markdown, local, searchable, graph view for AD relationships:

```bash
# Download from obsidian.md — AppImage for Linux
chmod +x Obsidian*.AppImage && ./Obsidian*.AppImage
```

CherryTree — tree structure, popular in OSCP community:

```bash
sudo apt install cherrytree
```

## Directory Structure Per Engagement

```bash
mkdir -p ~/labs/TARGET_NAME/{recon,scans,exploit,loot,screenshots,report}
```

Replace `TARGET_NAME` with hostname or IP. Keep all tool output here.

## Minimum Note Template Per Machine

```
Hostname:
IP:
OS:

Open Ports:
| Port | Service | Version | Notes |
|------|---------|---------|-------|

Credentials Found:
- service: user:pass

Flags:
- user.txt:
- root.txt:

Attack Path:
1.
2.
3.
```

## Tools Covered in This Phase

nmap, gobuster, ffuf, enum4linux-ng, smbclient, NetExec (nxc), ldapsearch, BloodHound, LinPEAS, WinPEAS, Impacket suite, Kerbrute — install all upfront:

```bash
sudo apt install -y nmap gobuster ffuf enum4linux smbclient bloodhound neo4j python3-impacket
pip3 install kerbrute 2>/dev/null || sudo apt install kerbrute
curl -L https://github.com/Pennyw0rth/NetExec/releases/latest/download/nxc -o /usr/local/bin/nxc && chmod +x /usr/local/bin/nxc
```
