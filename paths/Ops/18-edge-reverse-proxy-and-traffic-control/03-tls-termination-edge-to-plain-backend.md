# TLS termination choreography

Outcome mindset: deepen **edge-before-app** reasoning—not stanza-perfect config memorisation alone.

**Practise focus**

- Terminate HTTPS outward; sane internal plaintext only within controlled trust envelopes you document honestly.
- `openssl s_client` validate chains; rehearse corrupted cert rollback.
