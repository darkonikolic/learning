# Burp Suite, HTTP analysis & security-testing workflow — resources & environment

Outcome: you wield **Burp Suite as a repeatable debugging harness**—intercept, reshape, analyse **JWT OAuth HTTP API** traffic on systems you authorize—not aimless clicking through tabs.

| Anti-pattern | Target pattern |
|--------------|----------------|
| Memorise tab names without intent | Structured **intercept → analyse → mutate → replay** |

## Courses (ordering matters)

**Apprentice (first)**

- [Burp Suite Apprentice — Web App Pen Testing](https://www.udemy.com/course/burp-suite-apprentice-web-app-penetration-testing-course/)

**Practitioner (after Apprentice comfort)**

- [Burp Suite Practitioner — Web App Pen Testing](https://www.udemy.com/course/burp-suite-practitioner-web-app-penetration-testing-course/)

Treat Udemy syllabus sections as movable if the vendor restructures pages—anchor on **skills**, not timestamps.

## Practice labs parallel track

Every Academy theme you practise should see **paired Burp ergonomics**:

- [PortSwigger Web Security Academy](https://portswigger.net/web-security)

## Installer

- [Burp Suite download](https://portswigger.net/burp) — **Community** is adequate for foundational mechanics; note which workflows require paid features and substitute **curl/Repeater-only** rehearsals ethically.

## Local stack (authorised only)

Symfony (or comparable) demo API exposing **JWT** + **OAuth** flows you control  

Browser Developer Tools (**Network**)  

Trusted burp-proxy CA for your lab browser profile  

Intercept **only hosts you own**.

## Honour / ethics reminder

Laboratory artefacts only—respect OffSec assessment policy, CSP on third-party sites, contractual scopes.
