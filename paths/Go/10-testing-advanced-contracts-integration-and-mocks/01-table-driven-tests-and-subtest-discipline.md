# Unit 1 — Table-Driven Tests and Subtest Discipline

## Concept

`t.Parallel()` on a subtest runs it concurrently with other parallel subtests — this speeds up slow test suites and exposes data races. `t.Helper()` marks a function as a test helper so that when it calls `t.Errorf`, the failure points to the caller's line, not the helper's line. In Go versions before 1.22, loop variables are shared across iterations — always capture `tc := tc` before calling `t.Run` with `t.Parallel()` to avoid all subtests running with the last loop value.

## Code

```go
package validation_test

import (
	"testing"

	"github.com/example/app/validation"
)

// assertNoError is a helper — t.Helper() makes failures point to the caller.
func assertNoError(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
}

func assertError(t *testing.T, err error, want error) {
	t.Helper()
	if err == nil {
		t.Fatal("expected error, got nil")
	}
}

func TestValidateEmail(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		wantErr bool
	}{
		{name: "valid email", input: "user@example.com", wantErr: false},
		{name: "missing @", input: "userexample.com", wantErr: true},
		{name: "empty string", input: "", wantErr: true},
		{name: "unicode local part", input: "用户@example.com", wantErr: false},
		{name: "very long email", input: string(make([]byte, 300)) + "@x.com", wantErr: true},
	}

	for _, tc := range tests {
		tc := tc // capture loop variable — required before Go 1.22
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel() // run subtests concurrently

			err := validation.ValidateEmail(tc.input)
			if tc.wantErr {
				assertError(t, err, nil)
			} else {
				assertNoError(t, err)
			}
		})
	}
}
```

## Exercise

**Build:** Convert 3 of your existing sequential tests to parallel subtests with `t.Helper()` assertion functions.
**Input:** Three existing test functions from your order system (pick ones that make sense to parallelize — no shared mutable state).
**Output:** Each uses `t.Parallel()`. Each uses a helper function with `t.Helper()`. Loop variable is captured before `t.Parallel()`.
**Acceptance:** Run `go test -race ./...` — zero data races reported. Remove `tc := tc` from one test — run `go test -race` again — observe the race or the wrong case running. Re-add it.

## Interview

- Why must you capture `tc := tc` before calling `t.Parallel()` in a table-driven test in Go 1.21?
- What is the visible difference in test output between a helper with `t.Helper()` and one without?
- When is `t.Parallel()` a bad idea on a subtest?
