# Executive Summary Writing

The executive summary is read by people who will not read the rest of the report. Write for a non-technical manager or CISO making a budget or escalation decision.

## What to Include

1. Purpose of the test (one sentence)
2. Scope summary (what was tested, when)
3. Overall risk rating: Critical / High / Medium / Low
4. Finding count by severity: "X Critical, Y High, Z Medium"
5. Most impactful finding in plain English — no jargon
6. Top 3 recommendations

## What to Exclude

- Tool names (not "Metasploit was used to")
- CVE numbers (not "CVE-2021-44228 was found")
- Technical exploit mechanics (save for findings section)
- Acronyms without explanation

## Template

```
Executive Summary

[Company Name] engaged [Assessor] to conduct an external network penetration
test of [scope description] from [start date] to [end date].

During the assessment, [X] vulnerabilities were identified: [A] Critical,
[B] High, [C] Medium, and [D] Low severity. The overall risk rating for
the assessed environment is CRITICAL.

The most significant finding allows an unauthenticated attacker to gain full
administrative control of the [system name], potentially enabling access to
[business impact — e.g., all customer data, financial records, internal systems].

Top recommendations:
1. Immediately patch [system] — currently allows remote takeover without credentials
2. Implement multi-factor authentication across all administrative interfaces
3. Segment the [network zone] to limit attacker lateral movement capability

Full technical details, evidence, and remediation guidance are provided in
the Findings section of this report.
```

## Tone Calibration

Good: "An attacker outside the company can gain complete control of the payroll server without a username or password."

Bad: "The SMB service running on 192.168.1.10 is vulnerable to MS17-010 (EternalBlue), allowing remote code execution via a heap spray exploit."

The CISO forwards the executive summary to the board. If they cannot read it in 90 seconds and understand the risk, rewrite it.

## Length

One page maximum. Two paragraphs of narrative + a short bulleted recommendation list. Anything longer loses the audience.
