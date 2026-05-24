# Unit 10 — Race detector: instrument, provoke, refactor—don’t shrug nondeterminism

## Operational command habits

Embed **`go run -race` / `go test -race`** into learning loops—even if slowdown painful—prefer catching unsynchronised accesses early morally cheaper than flaky prod heisenbugs exhausting teams.

Go race detector observes **happens-before** instrumentation approximations—still invaluable teaching discipline.

## Practice cycle

Purposefully synthesize deterministic race regressions—you know root cause consciously—observe detector reports reading until clarity appears—repair via:

- narrower ownership pipelines,
- channel handoff rewriting,
- explicit mutex guarding chosen deliberately.

Forbidden outcome: patching sleep durations hoping races vanish probabilistically—that’s folklore debugging punishment later.

## Lab deliverable checklist

Brief write-up interpreting race report lines mapping to offending source lines—even if abbreviated paraphrasing.

## Interview prompts

Instrumentation overhead magnitude expectation order-of-mouse-not-science-ballpark honesty.

Contrast property-based concurrency tests vs `-race` complementarity philosophies.
