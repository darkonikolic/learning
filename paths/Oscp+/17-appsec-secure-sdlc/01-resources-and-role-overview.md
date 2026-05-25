# AppSec Resources and Role Overview

AppSec engineers bridge dev and security — code reviews, tool integration, threat modeling, vuln validation.

## Core Resources

- OWASP Testing Guide v4.2: https://owasp.org/www-project-web-security-testing-guide/
- OWASP ASVS: https://owasp.org/www-project-application-security-verification-standard/
- PortSwigger Web Academy (free, best web security training): https://portswigger.net/web-security
- SANS SEC522 (paid): https://www.sans.org/courses/application-security-securing-web-apps-apis-microservices/
- OWASP Code Review Guide: https://owasp.org/www-project-code-review-guide/

## Practice Platforms

- PortSwigger Labs: https://portswigger.net/web-security/all-labs
- DVWA: `docker run --rm -it -p 80:80 vulnerables/web-dvwa`
- WebGoat: `docker run -p 8080:8080 webgoat/webgoat`
- Juice Shop: `docker run -p 3000:3000 bkimminich/juice-shop`
- OWASP crAPI (API security): `docker-compose -f deploy/docker/docker-compose.yml up`

## Core Tools

| Tool | Purpose |
|------|---------|
| Burp Suite Pro | Manual web testing, proxy, scanner |
| OWASP ZAP | Free DAST, CI/CD integration |
| Semgrep | SAST, multi-language, extensible rules |
| Snyk | Dependency + container scanning |
| Trivy | All-in-one scanner (images, IaC, code) |
| Trufflehog | Secrets scanning in git history |

## The AppSec Role in Practice

Typical responsibilities:
1. Threat model new features before dev writes code
2. Review PRs for security issues (manual + SAST)
3. Own SAST/DAST/SCA tooling in CI/CD pipeline
4. Validate vulns reported by scanners or bug bounty
5. Write security requirements and developer guidance
6. Incident response support for application-layer attacks

## Learning Order

Start at PortSwigger Web Academy (SQL injection → XSS → authentication → access control).
Complete all OWASP Top 10 labs before moving to AppSec tooling.
ASVS Level 2 is your baseline for what "secure" means in code.
