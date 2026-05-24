# Unit 02 — Proxy, interception & HTTP History

Theme: grounding Burp circulation—**traffic you may legally inspect**.

Course alignment: Apprentice instalation ⇢ browser ⇢ imported CA ⇢ Proxy tabs.

Operational targets:

- Understand **Intercept on/off**, scope filters, unintended leakage of unrelated tabs.  
- **HTTP History** triage—not hoarding—but correlating benign mutation attempts.

Symfony drill:

```http
GET /api/users?page=1
```

Mutate **`page`** values you hypothesise (**e.g. `500`**), observe behavioural deltas defensively—not blind numeric spam absent hypothesis.

Topics: proxies, interception cadence, request/response halves, baseline headers vs cookies interplay.
