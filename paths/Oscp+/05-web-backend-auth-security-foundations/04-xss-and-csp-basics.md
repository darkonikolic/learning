# Unit 04 — XSS, CSP, and output-context discipline

Labs: reflected, stored, and DOM XSS arcs; SSTI introductions when your Academy path exposes them—template injection boundaries bleed into careless dynamic evaluation.

Defense lenses:

- Context-aware escaping (HTML vs attribute vs JS vs URL—not one magic sanitizer).

- CSP as **layered friction**, not a single silver directive paste.

Starter header awareness: CSP tightening tradeoffs; frame embedding controls (`X-Frame-Options`/`frame-ancestors` migration mental map); referrer policy narrowing cautiously.

## Local audit prompt

Locate template `|raw` / unescaped bridging in Symfony/Twig (or equivalents). Classify misuse risk tier honestly.
