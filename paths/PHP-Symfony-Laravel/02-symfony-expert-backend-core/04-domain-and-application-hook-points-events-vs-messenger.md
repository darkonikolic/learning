# Unit 4 — Events versus commands: coherence not buzzwords

Separate design lanes

| Concern kind | Typical shape |
| ------------- | ------------- |
| **Domain reaction** synchronous side-effect orchestration guarded by aggregate rules | Controlled inside application transaction |
| **Integration fan-out** | Message / event after consistent state persists |
| Observability augmentation | Lightweight listeners sparing global mutation |

Symfony EventDispatcher interplay

- Understand **stopped propagation semantics** pitfalls.
- Choose **callable listener wiring** ergonomics balancing discoverability versus explicit service definitions.
