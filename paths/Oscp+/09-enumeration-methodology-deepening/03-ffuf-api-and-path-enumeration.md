# ffuf for API Endpoint Discovery

API endpoints often aren't linked in the UI. Fuzz them explicitly with targeted wordlists.

## API Path Discovery

```bash
ffuf -u http://target/api/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/api/api-endpoints.txt \
  -mc 200,201,204,400,401,403
```

Generic paths:

```bash
ffuf -u http://target/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/raft-medium-words.txt \
  -mc 200,301,302,403
```

## Method Fuzzing on Found Endpoints

```bash
ffuf -u http://target/api/users \
  -w /usr/share/seclists/Fuzzing/http-request-methods.txt \
  -X FUZZ \
  -mc 200,201,204,405
```

## Parameter Name Fuzzing

GET parameter discovery:

```bash
ffuf -u "http://target/search?FUZZ=test" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -mc 200 -fs 1234
```

POST parameter discovery:

```bash
ffuf -u http://target/api/user \
  -X POST \
  -d "FUZZ=value" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -mc 200,400,422
```

JSON parameter fuzzing:

```bash
ffuf -u http://target/api/user \
  -X POST \
  -d '{"FUZZ":"value"}' \
  -H "Content-Type: application/json" \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -mc 200,400,422
```

## Handle Rate Limiting

```bash
ffuf -u http://target/api/FUZZ -w wordlist.txt -rate 10
```

## Reduce False Positives

```bash
# Step 1: run once, note most common response size
ffuf -u http://target/api/FUZZ -w wordlist.txt -mc all 2>&1 | grep -oP 'Size: \d+' | sort | uniq -c | sort -rn | head

# Step 2: filter that size
ffuf -u http://target/api/FUZZ -w wordlist.txt -fs 742
```

## Practice

Juice Shop API enumeration — run ffuf against `http://localhost:3000/api/FUZZ` and map all reachable endpoints before reading source code.
