# Finding Template and CVSS

Every finding uses the same template. Consistency matters — clients compare findings across sections and across assessments.

## Finding Template

```
Title:               [Concise vulnerability name — 5 words max]
Severity:            Critical / High / Medium / Low / Informational
CVSS Score:          X.X
CVSS Vector:         CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
CWE:                 CWE-89 (SQL Injection)
Affected Component:  hostname / IP / URL / parameter

Description:
[What is the vulnerability and why does it exist. 2-4 sentences.
Focus on root cause, not just the symptom.]

Evidence:
[Screenshot of exploitation, request/response from Burp, command output.
Label clearly: Figure 1 — SQL injection payload in POST /api/login]

Steps to Reproduce:
1. Navigate to https://target.com/api/login
2. Intercept POST request with Burp Suite
3. Modify `username` parameter to: ' OR 1=1--
4. Forward request — observe authentication bypass

Impact:
[What can an attacker achieve. Be specific and business-oriented.
"An unauthenticated attacker can bypass authentication and access
all 12,000 customer records including PII and payment data."]

Remediation:
[Specific fix with code example where possible]
Use parameterized queries:
  cursor.execute("SELECT * FROM users WHERE user = ?", (username,))
Reference: OWASP SQL Injection Prevention Cheat Sheet

References:
- CWE-89: https://cwe.mitre.org/data/definitions/89.html
- OWASP: https://owasp.org/www-community/attacks/SQL_Injection
- CVE-XXXX-XXXXX (if applicable)
```

## CVSS Scoring

Calculator: first.org/cvss/calculator/3.1

Key vectors to understand:
- **AV** (Attack Vector): Network (N) = remotely exploitable — highest impact
- **AC** (Attack Complexity): Low (L) = reliable, no special conditions
- **PR** (Privileges Required): None (N) = no auth needed
- **UI** (User Interaction): None (N) = no victim action required
- **C/I/A** (Impact): High (H) = full loss of confidentiality/integrity/availability

## Severity Thresholds

| CVSS Range | Severity |
|------------|----------|
| 9.0 – 10.0 | Critical |
| 7.0 – 8.9  | High |
| 4.0 – 6.9  | Medium |
| 0.1 – 3.9  | Low |
| 0.0        | Informational |

## For OSCP Exam

OffSec provides their own finding template inside the PEN-200 course. Use it exactly. Do not invent your own format for the exam submission.
