# Unit 2 — Partial Failure Reality Check

## Concept

In distributed systems, a request can succeed on the server but the response never arrives. The client sees a network error and doesn't know if the server processed it or not. This is the fundamental problem that requires idempotency. Naive retry on any error causes double-processing — the server ran the work twice.

## Code

```go
package main

import (
	"errors"
	"fmt"
	"math/rand"
)

var processed int // counts how many times the charge actually ran

// simulateCharge processes 80% of the time but always returns a network
// error 20% of the time — even when the work was done.
func simulateCharge(amount int) error {
	processed++ // work is done before we know if the response succeeds
	if rand.Float64() < 0.20 {
		return errors.New("network error: response lost")
	}
	return nil
}

// naiveRetry retries on every error — demonstrates double-processing.
func naiveRetry(amount int) (int, error) {
	calls := 0
	for i := 0; i < 5; i++ {
		calls++
		if err := simulateCharge(amount); err == nil {
			return calls, nil
		}
	}
	return calls, errors.New("all attempts failed")
}

func main() {
	const trials = 1000
	totalProcessed := 0
	totalSuccessResponses := 0

	for i := 0; i < trials; i++ {
		processed = 0
		_, err := naiveRetry(100)
		totalProcessed += processed
		if err == nil {
			totalSuccessResponses++
		}
	}

	fmt.Printf("Trials: %d\n", trials)
	fmt.Printf("Total times charge actually ran: %d\n", totalProcessed)
	fmt.Printf("Total successful responses: %d\n", totalSuccessResponses)
	fmt.Printf("Double-charge ratio: %.2f\n", float64(totalProcessed)/float64(totalSuccessResponses))
}
```

## Exercise

**Build:** Run the program above and capture the output.
**Input:** 1000 trials of naiveRetry calling simulateCharge
**Output:** Print how many times the simulated charge executed vs how many times the caller received a success response. Show the ratio.
**Acceptance:** The double-charge ratio is greater than 1.0 — proving that naive retry on any error causes more charges than successful responses

## Interview

- A client retries a payment POST after a timeout. The server processed the first request. What happens?
- What is the difference between "at-most-once" and "at-least-once" delivery?
- Name the only piece of information a client needs to detect a duplicate before resending.
