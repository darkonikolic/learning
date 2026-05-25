# Unit 10 — Configuration & secret ownership (no hard-coded production creds)

Anti-pattern: `DB_PASSWORD=admin` in source.

Preferred patterns (choose what matches your org, but understand trade-offs):

```
environment variables injected at runtime
mounted files / secret stores
12-factor style separation of config from code
```

## Practice

Create `config/` package reading env with validation (fail fast on boot if misconfigured).

## Interview prompts

Secret rotation; least privilege for reading secrets; avoiding logging config dumps.
