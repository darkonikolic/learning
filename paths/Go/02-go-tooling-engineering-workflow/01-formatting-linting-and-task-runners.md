# Unit 1 — Formatting, Linting, and Task Runners

## Concept

`gofmt` is non-negotiable — all Go code in the world is formatted the same way, and CI rejects unformatted diffs. `golangci-lint` runs dozens of analysers in one pass and catches real bugs: missing error checks, shadowed variables, incorrect mutex usage. A `Makefile` gives every team member and CI the same commands. Without it, "works on my machine" problems multiply fast.

## Code

```makefile
# Makefile — standard targets every Go service should have

.PHONY: build test lint fmt tidy run

build:
	go build -o bin/go-lab ./cmd/go-lab

test:
	go test -race -count=1 ./...

lint:
	golangci-lint run ./...

fmt:
	gofmt -w .
	goimports -w .

tidy:
	go mod tidy

run:
	go run ./cmd/go-lab

# Run all checks before committing
check: fmt tidy lint test
```

```yaml
# .golangci.yml — start with high-signal linters, add more as you go
linters:
  enable:
    - errcheck      # catches ignored errors (the #1 Go bug source)
    - govet         # suspicious constructs: misaligned printf, shadowed vars
    - staticcheck   # advanced correctness checks and deprecation warnings
    - gosimple      # simplification suggestions
    - unused        # dead code detection

linters-settings:
  errcheck:
    check-type-assertions: true   # flag unchecked `x.(T)` assertions

issues:
  max-issues-per-linter: 0
  max-same-issues: 0
```

## Exercise

**Build:** Add a `Makefile` and `.golangci.yml` to your `go-lab/` project with the targets above.

**Input:** Run `make lint` on your existing code. Then intentionally introduce two lint violations: ignore an error return from `NewProduct`, and add an unused variable.

**Output:** `make lint` reports both violations with file and line numbers.

**Acceptance:** Fix both violations, run `make check` — all targets pass with zero output from lint and all tests green.

## Interview

- Why does Go enforce a single formatting standard rather than letting teams configure it?
- What is the difference between `go vet` and `golangci-lint`? When would one catch something the other misses?
- A new engineer says "lint slows us down, let's disable it." What is the counterargument?
