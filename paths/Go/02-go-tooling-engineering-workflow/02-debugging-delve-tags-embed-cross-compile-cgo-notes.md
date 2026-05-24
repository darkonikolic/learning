# Unit 2 — Delve debugging, build tags, `embed`, cross-build, cautious CGO edges

## Learning outcomes

- Launch **`delve`** sessions—breakpoints, stepping, goroutine/stack inspection—not merely `fmt.Printf` archaeology when complexity spikes.
- Use **build tags** toggling backends / integration-heavy files without `#ifdef` chaos—predictable `-tags` combos documented.
- Package static assets thoughtfully using **`//go:embed`** (scope discipline: don’t inflate binaries absurdly unknowingly).
- Produce **Linux + Windows** (or analogous pair) artefacts through `GOOS` / `GOARCH` awareness.
- Respect **pure-Go** portability vs **`cgo`** introducing harder cross-compile + deployment coupling—articulate pragmatic trade-offs.

## Practice sequence

Conceptual rehearsal even if constrained:

```
linux artefact compile → alternate OS compile → seeded bug breakpoint fix narrative
```

## Interview prompts

Contrast debugging concurrent code vs sequential—breakpoint discipline hazards.

When **`cgo`** becomes unavoidable (hypothetical cryptography / libs) mitigation strategies (builder images, pinning).

## Acceptance criteria

Produce short written debugging story referencing **goroutine vantage** inspecting stuck worker scenario hypothetical.
