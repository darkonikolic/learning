# Integration exercise — map a full web request

Pick any website and trace one complete HTTP request from browser to server and back.

## Exercise steps

1. Open Chrome or Firefox → press F12 → Network tab
2. Browse to any login page (use your DVWA or Juice Shop lab)
3. Submit the login form
4. In the Network tab, click the POST request that appeared
5. Document everything in the table below

## What to document

| Field | What you found |
|---|---|
| URL | full URL including query params |
| Method | GET or POST |
| Request headers | Content-Type, User-Agent, Host |
| Cookies sent | names and values |
| Request body | what was submitted (username, password) |
| Response code | 200, 302, 401, 403... |
| Response headers | Set-Cookie, Location, Content-Type |
| Sensitive data in response | token? user data? internal paths? |

## Replay with curl

Right-click the request in DevTools → Copy → Copy as cURL. Paste into terminal and run.
Now modify the password field and observe the difference in response.

```bash
# Example — inspect cookie flags
curl -v http://localhost/login -d "username=admin&password=password" 2>&1 | grep -i "set-cookie"

# Good response (all three flags present):
# Set-Cookie: PHPSESSID=abc123; path=/; HttpOnly; Secure; SameSite=Strict

# Bad response (no flags):
# Set-Cookie: PHPSESSID=abc123
```

## Questions to answer after the exercise

- Does the session cookie have `HttpOnly`? If not, XSS can steal it.
- Does it have `Secure`? If not, it gets sent over plain HTTP.
- Does it have `SameSite`? If not, CSRF attacks are easier.
- Is the password sent over HTTPS or HTTP? (Check scheme in URL bar — padlock icon)
- Does the response contain any sensitive data that shouldn't be there?

## Practice

TryHackMe "Putting It All Together" room: https://tryhackme.com/room/puttingitalltogether
