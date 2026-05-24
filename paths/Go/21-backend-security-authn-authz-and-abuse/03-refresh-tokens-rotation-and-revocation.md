# Unit 3 — Refresh tokens: rotation, replay detection, storage trade-offs

Design a refresh flow that tolerates:

```
stolen refresh token scenario (rotation + reuse detection conceptually)
multiple devices
revocation requirements
```

Interview prompt: why refresh tokens deserve **tighter storage & transport** hygiene than access tokens.
