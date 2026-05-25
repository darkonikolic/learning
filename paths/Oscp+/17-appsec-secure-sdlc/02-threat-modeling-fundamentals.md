# Threat Modeling Fundamentals

Practical threat modeling — not academic. Find real risks before attackers do, applied to actual features.

## Tools

- OWASP Threat Dragon (free, visual): https://owasp.org/www-project-threat-dragon/
- Microsoft TMT: https://aka.ms/threatmodelingtool
- Draw.io for manual DFDs: https://app.diagrams.net/

## STRIDE Framework

| Letter | Threat | Example |
|--------|--------|---------|
| S | Spoofing | Fake user identity, JWT forgery |
| T | Tampering | Modify request params, CSRF |
| R | Repudiation | No audit logs, deny sending a message |
| I | Info Disclosure | Error messages leak stack traces |
| D | Denial of Service | No rate limiting, resource exhaustion |
| E | Elevation of Privilege | IDOR, broken access control |

## 5-Step Process

```
1. Draw data flow diagram (DFD) for the feature
   - External entities (users, external APIs)
   - Processes (application components)
   - Data stores (DB, cache, files)
   - Trust boundaries (dashed lines between zones)

2. Identify trust boundaries
   - Internet → WAF → App → DB
   - User input always crosses a boundary

3. Enumerate threats per component using STRIDE
   - For each process and data store: which STRIDE threats apply?

4. Rate risk
   - Risk = Likelihood × Impact
   - Use DREAD or simple High/Medium/Low

5. Define mitigations
   - Map each threat to a control
   - Controls: validate input, enforce authz, encrypt at rest, add logging
```

## Quick Threat Model — Login Flow Example

```
Endpoint: POST /api/login  {email, password}

S - Can attacker spoof identity?         → Brute force, credential stuffing
T - Can attacker tamper with request?    → Inject into email field, modify JWT
R - Is login activity logged?            → Missing audit log = repudiation risk
I - Does error message leak info?        → "email not found" vs "wrong password"
D - Is rate limiting applied?            → No = DoS/brute force risk
E - Can user escalate after login?       → Role assigned server-side? Or from token?
```

## Key Questions Per API Endpoint

```
- Who is allowed to call this endpoint?
- What data does it read/write?
- What happens if authentication is bypassed?
- What happens if a low-privilege user calls it?
- What does the error message reveal?
- Is this action logged?
```

## Practice Exercise

Threat model a password reset flow:
1. Draw DFD: user → email link → token validation → password update
2. Apply STRIDE to each step
3. Identify at least 3 real threats with mitigations
