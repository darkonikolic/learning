# Unit 06 — HTTP, HTTPS, TLS handshake

## Theme

How browsers speak to TLS-terminated web servers.

## Study alignment

| Supplemental videos | Conditional |
|---------------------|-----------|
| “HTTPS explained” / “TLS handshake” style NetworkChuck or equivalent | Only if plaintext vs encrypted framing still fuzzy |

## Ubuntu / OpenSSL drills

```bash
curl -I https://example.com

echo | openssl s_client -connect example.com:443 -servername example.com 2>/dev/null \
  | openssl x509 -noout -issuer -subject -dates
```

Adapt `example.com` to a stable host your lab can reach ethically.

Observe:

- Issuer hierarchy sense  
- Validity intervals  
- **SNI** necessity on shared hosting patterns  

Repeat `openssl s_client` interactively reading handshake stage lines your build prints.

## Browser developer tools exercise

Inspect at least:

- Response status line  
- Notable security headers framing (even if benign site omits hardened set)  

## Topics mapping

Plain HTTP verbs & status families, redirection chains, symmetric vs asymmetric stage at high level during TLS handshake story, certificates vs ephemeral session keys shorthand.

## Learning outcome

Explain end-to-end: resolve name → TCP 443 → ClientHello clues → negotiated parameters class → encrypted HTTP semantics—still coarse, factually tethered.
