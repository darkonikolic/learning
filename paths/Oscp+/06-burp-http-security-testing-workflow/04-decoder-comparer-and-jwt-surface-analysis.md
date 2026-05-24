# Unit 04 — Decoder, Comparer & JWT structural literacy

Completing Apprentice Decoder + Comparer arcs.

Laboratory JWT (issuance you govern):

Inspect JSON claims such as illustrative:

```json
{ "sub": "123", "role": "admin" }
```

**Never** reuse production tokens—the exercise is comprehension of claim semantics & encoding layers (Base64url segments)—not glamourising secrets.

Discuss **automatic header rewriting** responsibly (Burp macros / Match rules where edition permits)—community edition may constrain; adapt with scripted curl if needed.

Symfony drill dimensions: tempered **exp**, **iss**, **aud** mutation attempts + signature acceptance outcomes you document factually without bypass cheerleading fiction.
