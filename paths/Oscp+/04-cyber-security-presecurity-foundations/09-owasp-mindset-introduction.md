# OWASP Top 10 as a practical testing checklist

Each category mapped to an attack description, a tool, and a defense.

## OWASP Top 10 — 2021

| # | Category | Attack (1 line) | Tool to test | Defense |
|---|---|---|---|---|
| A01 | Broken Access Control | Access another user's data by changing an ID | Burp Suite + Autorize | Server-side auth checks on every request |
| A02 | Cryptographic Failures | Intercept HTTP traffic or crack weak password hashes | Wireshark, hashcat | TLS everywhere, bcrypt for passwords |
| A03 | Injection | SQL injection via input field: `' OR 1=1--` | sqlmap | Parameterized queries |
| A04 | Insecure Design | Logic flaw: skip payment step in checkout flow | Manual testing | Threat modeling during design |
| A05 | Security Misconfiguration | Default creds (admin/admin), directory listing enabled | nikto, gobuster | Hardening guides, disable defaults |
| A06 | Vulnerable Components | Known CVE in outdated library version | `npm audit`, `snyk test` | Keep dependencies updated |
| A07 | Auth Failures | Brute-force login with no rate limiting | hydra (lab only) | Rate limiting + MFA |
| A08 | Software Integrity | Tampered package in CI/CD pipeline | Check download hashes | SRI tags, signed packages |
| A09 | Logging Failures | Attack happens with no trace in logs | Try error conditions, check logs | Structured logging, centralized SIEM |
| A10 | SSRF | `url=http://169.254.169.254/` to hit cloud metadata | Manual, curl | Allowlist outbound URLs, block metadata IPs |

## Run Juice Shop locally and test each category

```bash
docker run -d -p 3000:3000 bkimminich/juice-shop
# Browse to http://localhost:3000
# Challenges menu shows progress — covers all 10 OWASP categories
```

## Quick OWASP reference

- OWASP Top 10 detail: https://owasp.org/www-project-top-ten/
- Juice Shop challenge list: https://pwning.owasp-juice.shop/companion-guide/latest/part2/

## Practice

TryHackMe "OWASP Top 10 - 2021" room: https://tryhackme.com/room/owasptop102021
