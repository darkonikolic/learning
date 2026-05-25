# Quick Reference — Advanced Testing

## Subtest parallel capture (pre-1.22)
for _, tc := range cases {
    tc := tc  // REQUIRED: loop var capture
    t.Run(tc.name, func(t *testing.T) {
        t.Parallel()
    })
}

## t.Helper() — always call in assertion helpers
func assertEqual(t *testing.T, got, want int) {
    t.Helper()
    if got != want { t.Errorf(...) }
}

## Mock vs stub distinction
// Stub: returns canned data, no expectations
// Mock: asserts interactions (gomock EXPECT)
// Use mocks sparingly — integration tests > mocks

## Contract testing
// Consumer defines contract (expected request/response shape)
// Provider verifies it on their side
// Tooling: pact-go

## Flake prevention
// Never sleep in tests — use wait strategies
// Isolate state: each test gets its own DB schema or transaction
// Use t.Cleanup for guaranteed teardown
