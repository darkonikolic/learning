# Unit 5 — Capstone: Coverage and a Balanced Test Suite

## Concept

A balanced test suite has unit tests (fast, many, mock dependencies) and integration tests (slow, few, real DB). They do not duplicate each other — unit tests verify logic, integration tests verify DB behavior. Coverage percentage is a proxy metric, not a goal. 70% coverage of real business behavior is more valuable than 100% coverage of trivial getters. High coverage with weak assertions is worse than lower coverage with strong ones.

## Code

```makefile
# Makefile

.PHONY: test-unit test-integration test-all coverage

# Fast — runs on every save
test-unit:
	go test -race -count=1 ./...

# Slow — runs in CI, requires DB
test-integration:
	go test -tags=integration -race -count=1 -timeout=120s ./...

# Both
test-all: test-unit test-integration

# Coverage report — unit tests only
coverage:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html
	go tool cover -func=coverage.out | grep total
```

```
# Target test distribution for the order system:
#
# Unit tests (service layer, mocked deps):     ~15 tests, run in <1s
#   - OrderService.PlaceOrder: invalid user, empty items, success
#   - PricingService.Calculate: discount bounds, zero price
#   - StatusMachine.Transition: valid transitions, invalid transitions
#
# Integration tests (repository, real DB):      ~5 tests, run in ~10s
#   - OrderRepo.Create: round-trip, fields preserved
#   - OrderRepo.FindByID: not found returns ErrNotFound
#   - OrderRepo.PlaceOrder: transaction rollback on item failure
#
# Benchmarks:                                   ~2, run on demand
#   - BenchmarkOrderRepo_FindByID
#   - BenchmarkJSONMarshal_OrderResponse
```

## Exercise

**Build:** A complete test suite for your order system across three categories.
**Input:** The order system from modules 8-9.
**Output:** (1) 3 unit tests for service logic using mocked repositories. (2) 2 integration tests for repository against a real DB via Testcontainers. (3) 1 benchmark for the most-called query (`FindByID`).
**Acceptance:** `make test-unit` passes in under 2 seconds. `make test-integration` passes with Testcontainers running. `make coverage` shows at least 60% coverage of the service package. The integration tests are excluded from `make test-unit` (confirm via `-tags` absence).

## Interview

- What is the difference between a unit test and an integration test in your order system?
- Why would 100% unit test coverage with all dependencies mocked give you false confidence?
- A new developer asks "should I write a unit test or integration test for this query?" How do you answer?
