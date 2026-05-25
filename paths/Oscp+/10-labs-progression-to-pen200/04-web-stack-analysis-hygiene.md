# Web Enumeration Routine

Run this chain on every machine with an HTTP/HTTPS service. Don't skip steps.

## Standard Web Enum Chain

```bash
# 1. Identify tech stack
curl -I http://target
whatweb http://target

# 2. Directory discovery
gobuster dir \
  -u http://target \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
  -x php,txt,html,bak,old \
  -t 50

# 3. Check common files
curl http://target/robots.txt
curl http://target/sitemap.xml
curl http://target/.htaccess
curl http://target/web.config

# 4. Vuln scan
nikto -h http://target

# 5. Subdomain/vhost fuzzing
gobuster vhost -u http://target.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

## Manual Browsing Checklist

- Login pages: try default creds (`admin:admin`, `admin:password`, `guest:guest`)
- Upload forms: attempt file upload bypass (rename `.php` to `.php5`, `.phtml`)
- Search bars: test for SQLi (`'`, `' OR 1=1--`, `"`)
- URL parameters: test for LFI (`?page=../../../etc/passwd`)
- HTML source comments: `Ctrl+U` in browser, grep for TODOs, passwords, paths

## CMS-Specific Scans

```bash
# WordPress
wpscan --url http://target --enumerate u,vp,vt

# Joomla
joomscan -u http://target

# Drupal
droopescan scan drupal -u http://target
```

## SecLists Location

```bash
# Install if missing
sudo apt install seclists

ls /usr/share/seclists/Discovery/Web-Content/
```

## Signal to Move On

Web enum is done when: all directories exhausted, all parameters tested, CMS scan complete, Nikto reviewed. If nothing actionable, pivot to other services — web is not always the entry point.
