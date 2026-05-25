# Secure Code Review Methodology

Start at entry points — every route, endpoint, and input parameter. Work inward toward data stores.

## Resources

- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/
- PayloadsAllTheThings: https://github.com/swisskyrepo/PayloadsAllTheThings

## Review Order

```
1. Map all entry points (routes, API endpoints, CLI args, file uploads)
2. Trace user input through the code — where does it land?
3. Check authentication on every sensitive route
4. Check authorization (can a low-priv user reach admin actions?)
5. Review data store interactions for injection
6. Check output encoding before rendering
7. Look for hardcoded secrets
```

## High-Value Grep Patterns

```bash
# SQL injection candidates
grep -rn "mysql_query\|execute(" . --include="*.php"
grep -rn "cursor.execute\|format(" . --include="*.py" | grep "SELECT\|INSERT\|UPDATE"
grep -rn "db.query\|db.exec" . --include="*.js"

# Command injection
grep -rn "exec(\|system(\|shell_exec(\|passthru(" . --include="*.php"
grep -rn "subprocess\|os.system\|os.popen" . --include="*.py"

# Hardcoded credentials
grep -rn "password\s*=\s*['\"]" . --include="*.py"
grep -rn "api_key\|secret_key\|ACCESS_KEY" . --include="*.js"
grep -rn "BEGIN RSA PRIVATE KEY\|-----BEGIN" .

# Insecure deserialization
grep -rn "unserialize(\|pickle.loads\|yaml.load(" .

# Missing output encoding (XSS risk)
grep -rn "innerHTML\|document.write\|dangerouslySetInnerHTML" . --include="*.js"
```

## Vulnerable Patterns to Spot

```php
# PHP — SQL injection
$query = "SELECT * FROM users WHERE id=" . $_GET['id'];
mysql_query($query);

# PHP — Command injection
system("ping " . $_POST['host']);

# PHP — File inclusion
include($_GET['page'] . ".php");
```

```python
# Python — SQL injection
cursor.execute(f"SELECT * FROM users WHERE id={user_id}")
cursor.execute("SELECT * FROM users WHERE name='" + name + "'")

# Python — Command injection
os.system("ping " + request.args.get("host"))

# Python — Insecure deserialization
obj = pickle.loads(user_data)
```

```javascript
// JS — XSS
document.getElementById("output").innerHTML = userInput;

// JS — Prototype pollution
obj[userKey] = userValue;  // if userKey is "__proto__"
```

## Checklist

```
[ ] All routes require authentication (check middleware/guards)
[ ] Parameterized queries used everywhere (no string concatenation)
[ ] User input validated and sanitized at entry
[ ] Output encoded before rendering (HTML, JS, SQL contexts)
[ ] No hardcoded secrets or API keys
[ ] Authorization checks on every sensitive action (not just login)
[ ] Deserialization uses safe formats (JSON > pickle/unserialize)
[ ] File uploads: type check, size limit, store outside webroot
[ ] Error messages don't leak stack traces or internal paths
[ ] Logging in place for auth failures and sensitive actions
```

## Ethical Note

Code review is only authorized on code you own or have explicit written permission to review.
