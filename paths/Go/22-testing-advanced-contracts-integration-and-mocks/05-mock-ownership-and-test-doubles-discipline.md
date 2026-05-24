# Unit 5 — Mock ownership: when interfaces help vs when mocks lie


Mocks should verify **interaction contracts sparingly**, not emulate entire subsystems that still melt in prod.

Interview stance:

- Prefer **fakes/stubs** for deterministic collaborators.
- Use **mocks** for orchestration edges where you explicitly care about interaction shape.
- Don’t mock the universe—integration-test the seam where correctness is truly defined (`database/sql`, real migrations, HTTP to test server, clocks, RNG).
