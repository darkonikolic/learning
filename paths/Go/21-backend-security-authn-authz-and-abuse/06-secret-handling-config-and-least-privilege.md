# Unit 6 — Secret handling in Go services (no printf accidents)

Rules of thumb:

```
load secrets from env / mounted files / secret manager integration pattern for your org
never log secrets—even “temporarily”
rotate without redeploy thrash where possible (still often requires rolling restart practical honesty)
```

Practice: implement config struct with **redacted `String()`** for logs.
