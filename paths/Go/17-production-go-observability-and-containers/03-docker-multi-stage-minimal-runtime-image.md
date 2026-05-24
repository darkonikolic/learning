# Unit 3 — Multi-stage Docker builds: separate compile from runtime

## Anti-pattern

Shipping a compiler, build caches, test tooling, and dev-only files in the same image you deploy.

## Preferred shape (conceptual)

```
Stage A (builder): compile the Go binary reproducibly.

Stage B (runtime): copy the binary (+ any `embed` assets) into a small base image.
```

## Practice

Refactor Unit 2’s Dockerfile to multi-stage. Record **approximate image size change** (rough numbers are fine) and explain what disappeared from the final image layers.

## Interview prompts

Alpine vs Debian vs distroless trade-offs—especially around DNS/TLS certs, libc quirks, debugging difficulty—stay honest and check current docs for your chosen base.

