# Unit 8 — Modules: reproducible graphs and dependency honesty (`go.mod`)

## Learning outcome

You operate **`go mod init`** + **`go mod tidy`** fluently—not mystically—including understanding **semver intent**, pinning vs floating trade-offs for learning reproducibility.

Add exactly **one** legitimate third-party library solving a mundane problem (**CLI flags**, **YAML/TOML config**, hashing/UUID—you choose) documenting:

- rationale,
- behavioural surface you rely on.

## Concepts to internalise

- **Module path uniqueness** anchors import strings.
- **Sum file integrity** reasoning (supply chain conscience).
- **Pseudo-versions / retracted versions**: awareness—they impact upgrade paths.

Avoid dependency shopping sprees—they expand attack surface mentally and operationally even if scanners quiet today.

## Lab written answer

Produce short risk note:

- hypothetical upgrade breakage scenario,
- how you'd bisect regressions responsibly (`go.mod` pinning strategies at learning scale).

## Interview prompts

- minimal dependency philosophy pragmatic cases,
- `replace` directives usage cautions (`go.mod` escapes),
- private module proxy awareness (conceptual readiness).
