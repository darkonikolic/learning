# Unit 8 — SSRF: fetching user-controlled URLs from the backend

Danger: background jobs hitting internal metadata endpoints because user supplied “URL to import.”

Mitigations sketch:

```
allow-lists / block private IP ranges / DNS rebinding awareness high level
separate network egress controls
never forward internal auth headers blindly
```

Interview: give a concrete Go `http.Client` footgun example and how you’d harden a fetcher.
