# Unit 2 — Package Ownership vs Util Soup

## Concept

Package names should describe what they own, not what they do. `util`, `helpers`, `common`, and `misc` are symptoms of missing domain concepts — they are where code goes when you haven't decided who owns it. A package should have one reason to change: if you add a new feature and you're editing `util/`, the package name is wrong. Each function in `util` belongs in a specific domain package that owns that concept.

## Code

```go
// BAD: util package accumulates unrelated things
// util/util.go

package util

import (
	"fmt"
	"time"
	"strings"
)

func FormatMoney(amount float64) string { return fmt.Sprintf("$%.2f", amount) }
func IsValidEmail(s string) string      { return strings.Contains(s, "@") }
func ParseOrderDate(s string) time.Time { /* ... */ }
func TruncateText(s string, n int) string { /* ... */ }

// ---

// GOOD: each function belongs to the package that owns the concept

// money/money.go — owns currency formatting and arithmetic
package money

func Format(amount float64) string { return fmt.Sprintf("$%.2f", amount) }

// validation/email.go — owns input validation rules
package validation

func IsValidEmail(s string) bool { return strings.Contains(s, "@") && len(s) > 3 }

// domain/order.go — owns order parsing logic
package domain

func ParseOrderDate(s string) (time.Time, error) { return time.Parse(time.RFC3339, s) }

// display/text.go — owns presentation formatting
package display

func Truncate(s string, n int) string {
	if len(s) <= n { return s }
	return s[:n] + "…"
}
```

## Exercise

**Build:** A package audit and refactor of your `go-lab/` directory.
**Input:** Find every function in packages named `util`, `helpers`, `common`, or `misc`.
**Output:** Move at least 3 functions to correctly named packages. Each function's new home should be named after the concept it belongs to, not what it does.
**Acceptance:** Run `go build ./...` after the move — no compilation errors. The old package either no longer exists or contains only functions that genuinely belong together. Write a one-sentence comment at the top of each new package file: `// Package money owns currency arithmetic and formatting.`

## Interview

- A package named `util` has grown to 800 lines. What does that tell you about the design?
- How do you decide which package a function belongs in?
- Two packages both need the same helper function. Is the answer to put it in `common`?
