# OSCP Preparation Roadmap

Structured lab progression before enrolling in PEN-200. Enroll when you can solve Medium PG machines independently — not before.

## Phase 1: Foundations (4–6 weeks)

Goal: Build enumeration and basic exploitation instinct.

- Complete TryHackMe "Jr Penetration Tester" learning path (fully guided)
- Complete TryHackMe "Pre-Security" path if Linux/networking is shaky
- Solve 10 TryHackMe rooms: "Basic Pentesting", "Blue", "Ignite", "Pickle Rick", "Mr Robot CTF"
- Target: comfortable with nmap, gobuster, basic Metasploit, simple PrivEsc

## Phase 2: Independent Exploitation (6–8 weeks)

Goal: Solve machines without hints.

- Solve 20 OffSec Proving Grounds Practice machines: mix of Easy and Medium Linux
- Add 5 Medium Windows PG machines
- No hints for first 2 hours — check writeup only after genuine stuck
- Log every machine: what you tried, what worked, why
- Target: solving Easy machines in under 1 hour, Medium in under 2 hours

Recommended PG starting machines (Linux Easy): Potato, Shakabrah, Assertion101, Gaara
Recommended PG starting machines (Windows Easy): Algeron, Craft, WebSVN2

## Phase 3: Active Directory (4–6 weeks)

Goal: Execute full domain compromise independently.

- HTB Academy "Active Directory Enumeration & Attacks" module (free tier available)
- Solve HTB "Forest" (AS-REP roasting + DCSync path)
- Solve HTB "Sauna" (AS-REP + Autologon + DCSync)
- Solve HTB "Active" (Kerberoasting)
- Solve 5 AD-focused PG Practice machines
- Target: enumerate domain, find attack path, achieve DA without hints

## Phase 4: Exam Simulation (1–2 weeks)

Goal: Simulate exam conditions before enrolling.

- Time-box a 24-hour attempt: 3 standalone PG machines + 1 AD chain (GOAD or PG)
- No writeup lookup during the window
- Write a full exam-style report after
- Evaluate: Did you compromise 3 standalones? Did you get DA? Did you document everything?

## Enrollment Signal

You are ready to enroll in PEN-200 when:
- Solving Medium PG Practice machines in under 2 hours without hints
- Can enumerate and exploit AD without step-by-step guidance
- Have documented at least 20 machines in report format

Enrolling before this point means paying for the course while learning basics you could learn free. Enrolling after means you'll finish faster and more confidently.
