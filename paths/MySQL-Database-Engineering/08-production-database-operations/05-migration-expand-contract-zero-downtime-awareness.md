# Unit 05 — Evolutionary schema migration posture

Articulate additive backward-compatible rollout patterns (expand phase, dual-write/read bridging, eventual contract tightening) referencing industry literature.

Avoid naïvely blocking `ALTER` on hypothetical 150M-row core fact table without phased plan—even if simulated only intellectually until you practise on clones.
