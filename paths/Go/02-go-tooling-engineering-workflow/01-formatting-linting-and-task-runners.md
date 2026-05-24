# Unit 1 — Toolchain rhythm: formatting, lint, vet, repeatable tasks

> **Suggested informational cadence:** two thematic blocks aligning with roughly two abbreviated “segments” originally described as tooling weeks—not strict calendar commitments.

## Learning outcomes

Operational habits settle so you reflexively normalize code before review—not after argument:

| Tool | Role |
|------|------|
| **`go fmt`** | canonical indentation / simplicity standard |
| **`goimports`** (or editor integration aligning to it) | import grouping + pruning unused |
| **`golangci-lint`** aggregator | umbrella running many analysers—you configure gradually consciously |
| **`staticcheck`** | higher-signal correctness + deprecation insight |
| **`go vet`** | suspicious constructs early |

Reproducibility via **`Makefile`** or **`Taskfile`** exposing targets like:

```
fmt tidy vet lint test build
```

## Practice spiral

Extend your **`go-lab`** / **`task-cli`** repository:

```
CLI change → golangci-lint → fmt/tidy gate → deterministic build artefact naming
```

## Interview prompts

Why CI duplication of editor format-on-save beats “trust humans”. When overly aggressive linters rot velocity—balancing signal vs noise articulated.

## Acceptance criteria

Demonstrate scripted sequence (conceptually documented if automation environment constrained elsewhere) reproducible identical commands invoked locally + CI analogue sketch.
