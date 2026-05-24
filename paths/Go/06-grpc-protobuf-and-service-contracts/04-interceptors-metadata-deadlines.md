# Unit 4 — Interceptors ↔ metadata ↔ deadlines (mirroring—but not cloning—HTTP middleware)

Implement cross-cutting auth header verification placeholder (explicitly insecure teaching stub—not production pattern misrepresented).

Practice propagating analogue **trace / request identifiers** bridging metadata headers cleanly.

Demonstrate layering deadlines (`context.WithTimeout` interplay) collapsing calls crossing configured budgets surfacing **`codes.DeadlineExceeded`** narrative mapping.

Interview nuance distinguishing unary interceptors chaining vs streaming RecvMsg interception complexity gradient awareness naming only minimally unless deeper dive chosen willingly.
