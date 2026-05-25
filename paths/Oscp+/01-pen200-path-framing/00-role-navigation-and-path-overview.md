# OSCP+ Learning Path — Role Navigation

## Four Roles This Path Covers

| Tag | Role |
|-----|------|
| `[AppSec]` | Application Security / Secure SDLC Engineer |
| `[Blue]` | Blue Team / SOC Analyst |
| `[Pentest]` | Junior Pentester |
| `[Red]` | Offensive Security / Red Team |

---

## Complete Phase Map

| # | Phase | AppSec | Blue | Pentest | Red |
|---|-------|--------|------|---------|-----|
| 01 | Path framing & pedagogy | REQ | REQ | REQ | REQ |
| 02 | Linux foundations | REQ | REQ | REQ | REQ |
| 03 | Networking foundations | REQ | REQ | REQ | REQ |
| 04 | Cyber pre-security | REQ | REQ | REQ | REQ |
| 05 | Web / auth / backend security | REQ | REQ | REQ | REQ |
| 06 | Burp HTTP testing workflow | REQ | OPT | REQ | REQ |
| 07 | Windows / AD enterprise | OPT | REQ | REQ | REQ |
| 08 | Kali Linux tooling | SKP | OPT | REQ | REQ |
| 09 | Enumeration methodology | OPT | OPT | REQ | REQ |
| 10 | Labs progression → PEN-200 | SKP | SKP | REQ | REQ |
| 11 | Exploitation fundamentals | SKP | OPT | REQ | REQ |
| 12 | Privilege escalation | SKP | REQ | REQ | REQ |
| 13 | Active Directory attacks | SKP | REQ | REQ | REQ |
| 14 | Post-exploitation & lateral movement | SKP | REQ | REQ | REQ |
| 15 | Pivoting & tunneling | SKP | OPT | REQ | REQ |
| 16 | Blue team / SOC / incident response | REQ | REQ | OPT | REQ |
| 17 | AppSec / Secure SDLC | REQ | OPT | OPT | OPT |
| 18 | Industry-standard tooling reference | REQ | REQ | REQ | REQ |
| 19 | Report writing & documentation | REQ | OPT | REQ | REQ |
| 20 | Advanced lab challenges | SKP | SKP | REQ | REQ |

`REQ` = Required &nbsp;|&nbsp; `OPT` = Optional / recommended &nbsp;|&nbsp; `SKP` = Skip or defer

---

## Tracks — Sequence by Role

### AppSec / Secure SDLC Track
```
01 → 02 → 03 → 04 → 05 → 06 → 16(IR basics) → 17 → 18(AppSec section) → 19
```
Estimated total: ~4–5 months at steady pace.

### Blue Team / SOC Analyst Track
```
01 → 02 → 03 → 04 → 05 → 07 → 09(enumeration to understand attacks) → 12 → 13 → 14 → 16 → 18(defensive section)
```
Estimated total: ~4–6 months at steady pace.

### Junior Pentester Track
```
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 18(offensive section) → 19 → 20(easy labs)
```
Estimated total: ~6–8 months to PEN-200 readiness.

### Offensive Security / Red Team Track
```
01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15 → 16 → 18 → 19 → 20
```
Estimated total: ~10–14 months for solid depth.

---

## Competency Coverage by Role

| Competency | AppSec | Blue | Pentest | Red |
|-----------|--------|------|---------|-----|
| Linux / CLI fluency | 85% | 80% | 95% | 95% |
| Networking fundamentals | 80% | 90% | 90% | 90% |
| Web security (OWASP) | 95% | 75% | 85% | 80% |
| Auth / API security | 95% | 70% | 80% | 75% |
| Windows / AD structure | 50% | 85% | 85% | 95% |
| Exploitation technique | 40% | 55% | 90% | 95% |
| Privilege escalation | 30% | 70% | 90% | 95% |
| AD attack chains | 20% | 80% | 90% | 95% |
| Post-exploitation / lateral | 20% | 85% | 80% | 95% |
| Pivoting / tunneling | 10% | 50% | 85% | 95% |
| Blue team / IR | 65% | 95% | 50% | 80% |
| AppSec / SDLC tooling | 95% | 50% | 40% | 40% |
| Industry tooling literacy | 80% | 80% | 90% | 95% |
| Report writing | 90% | 65% | 90% | 80% |

---

## Phase Groups (logical clusters)

### Group A — Foundations (Phases 01–04)
Universal baseline. All roles start here.

### Group B — Web & Application Security (Phases 05–06)
Core for AppSec and Pentest. Blue team reads defensively.

### Group C — Infrastructure & Enterprise (Phases 07–09)
Windows/AD understanding, Kali toolchain, enumeration discipline.

### Group D — Offensive Techniques (Phases 10–15)
Pentest and Red team primary track. Blue team reads to understand attack perspective.

### Group E — Defensive & AppSec Specialisations (Phases 16–17)
Blue team and AppSec primary. Offensive roles read for detection awareness.

### Group F — Professional Skills (Phases 18–19)
Tooling literacy and reporting. Required across all roles.

### Group G — Lab Mastery (Phase 20)
Practical lab challenge progression. Pentest and Red team.

---

## Industry Certification Alignment

| Cert | Relevant phases |
|------|----------------|
| OSCP / PEN-200 | 01–15, 18, 19, 20 |
| CEH | 01–11, 18 |
| CompTIA Security+ | 01–07, 16, 17 |
| GWAPT / GPEN | 05–06, 09, 11, 18, 19 |
| CRTO (Red Team Ops) | 11–15, 18, 20 |
| BTL1 (Blue Team) | 02–05, 07, 16, 18 |
| CSSLP / Secure SDLC | 04–06, 16, 17, 19 |
