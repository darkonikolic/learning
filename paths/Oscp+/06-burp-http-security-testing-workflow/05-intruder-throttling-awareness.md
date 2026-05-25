# Intruder: Automated Fuzzing with Rate Limit Awareness

Intruder automates parameter fuzzing. Burp Community is throttled to ~1 request/second — use it for targeted tests, not mass brute force.

## Send to Intruder

From HTTP History or Repeater: Ctrl+I or right-click → Send to Intruder.

## Mark Payload Positions

In the Positions tab, clear all auto-selected positions (Clear §).  
Highlight the value you want to fuzz → click "Add §".

```
# Example: username enumeration
POST /login HTTP/1.1
Host: localhost

username=§admin§&password=wrongpass
```

## Attack Types

| Type | Use case |
|------|----------|
| Sniper | one parameter, one wordlist |
| Battering Ram | same value into all parameters simultaneously |
| Pitchfork | multiple parameters, one wordlist each (paired) |
| Cluster Bomb | multiple parameters, all combinations (use carefully) |

## Wordlists

```bash
# Kali built-in
ls /usr/share/wordlists/
/usr/share/wordlists/rockyou.txt
/usr/share/wordlists/dirb/common.txt

# SecLists (install if missing)
sudo apt install seclists
ls /usr/share/seclists/Usernames/
ls /usr/share/seclists/Passwords/
```

## Reading Intruder Results

Sort by **Length** column — different response length = different server behavior = valid username or successful guess.  
Sort by **Status** — 302 redirect on one attempt = login succeeded.

## Faster Alternative: ffuf

Community Burp throttling makes Intruder slow for large lists. Use ffuf for speed:

```bash
# Username enumeration
ffuf -u http://localhost/login -X POST \
  -d "username=FUZZ&password=wrongpass" \
  -w /usr/share/seclists/Usernames/Names/names.txt \
  -fr "Invalid username" -t 50

# Password spray (known username)
ffuf -u http://localhost/login -X POST \
  -d "username=admin&password=FUZZ" \
  -w /usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt \
  -fr "Invalid password" -t 10
```

## Exercise

1. In DVWA (security=Low), find the login form
2. Send a login POST to Intruder
3. Mark the `username` parameter as payload position
4. Attack type: Sniper
5. Wordlist: use `/usr/share/seclists/Usernames/Names/names.txt`
6. Start attack — sort by Length — which usernames return a different response?
7. Confirm with ffuf — compare speed
