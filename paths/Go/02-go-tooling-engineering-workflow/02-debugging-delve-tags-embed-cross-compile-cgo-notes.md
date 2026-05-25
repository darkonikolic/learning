# Unit 2 — Debugging with Delve, Build Tags, and Cross-Compilation

## Concept

Delve is Go's debugger — you set breakpoints, step through code line by line, and inspect variables and goroutine stacks. It is far more useful than `fmt.Printf` archaeology when you have concurrent code or need to inspect state mid-execution. Build tags let you include or exclude files at compile time without `#ifdef` chaos — useful for integration tests, debug helpers, or platform-specific code. `CGO_ENABLED=0 GOOS=linux GOARCH=amd64` produces a fully static Linux binary from any machine.

## Code

```go
// cmd/go-lab/main.go — add a deliberate off-by-one bug for the debugging exercise
package main

import "fmt"

func sumFirstN(nums []int, n int) int {
	total := 0
	for i := 0; i <= n; i++ { // BUG: should be i < n — reads one past the end
		total += nums[i]
	}
	return total
}

func main() {
	nums := []int{10, 20, 30, 40, 50}
	fmt.Println(sumFirstN(nums, 3)) // panics: index out of range
}
```

```bash
# Delve session — commands as comments showing the workflow

dlv debug ./cmd/go-lab        # compile with debug info and drop into debugger

(dlv) break main.sumFirstN    # set breakpoint at function entry
(dlv) continue                # run until breakpoint
(dlv) print nums              # inspect the slice: [10 20 30 40 50]
(dlv) print n                 # 3
(dlv) next                    # step to next line
(dlv) print i                 # watch i increment — spot when it reaches n (3 = length - 2... wait)
(dlv) locals                  # print all local variables
(dlv) quit
```

```go
// Build tag: only compiled when -tags integration is passed
//go:build integration

package main

import "fmt"

func init() {
	fmt.Println("integration mode: using real external services")
}
```

```bash
# Cross-compile a static Linux binary from macOS
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o bin/go-lab-linux ./cmd/go-lab

# Verify it's statically linked
file bin/go-lab-linux   # should say: ELF 64-bit LSB executable, statically linked

# Run integration tests only
go test -tags integration ./...
```

## Exercise

**Build:** Add the `sumFirstN` function with the off-by-one bug to your `go-lab/` project. Use `dlv debug` to find the exact line where `i` goes out of bounds.

**Input:** Set a breakpoint in `sumFirstN`. Step through the loop watching `i` and `total`.

**Output:** Identify the line where the bug occurs. Fix it. Confirm `sumFirstN(nums, 3)` returns `60` (10+20+30).

**Acceptance:** Fix passes `go test ./...`. Add a `make cross-build` target that produces a Linux binary using `CGO_ENABLED=0`.

## Interview

- When would you use Delve over `fmt.Printf` for debugging?
- What does `CGO_ENABLED=0` do, and why does it matter for Docker deployments?
- How do build tags differ from `//go:generate` directives?
