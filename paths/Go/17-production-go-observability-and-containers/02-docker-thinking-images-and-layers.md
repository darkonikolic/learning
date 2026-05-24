# Unit 2 — Container basics: images, layers, reproducible builds

## Outcomes

- Explain **layers** as cached build steps—and why careless `Dockerfile` ordering invalidates caches and slows CI.
- Distinguish **build toolchain image** vs **minimal runtime-only** carrier (expanded in Unit 3 with multi-stage patterns).

## Practice

Produce a runnable image for `prod-service/` from a **`golang`** base (single-stage acceptable for learning), run the binary inside the container, and verify behaviour matches host builds.

## Lab

Answer in prose:

- Why pinning **base image digests** matters for supply-chain reproducibility (even if you used a tag locally “for speed”).
- What changes between “dev ergonomics Dockerfile” vs “delivery Dockerfile” mentality.
