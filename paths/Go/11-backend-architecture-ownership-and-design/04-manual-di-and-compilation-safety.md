# Unit 4 — Manual dependency injection clarity (compilation-safe wiring discipline)

Contrast anti-pattern caricature scattering `NewWhatever()` globals mutating incidental shared state covertly thwarting deterministic tests.

Prefer constructor injections accepting collaborators explicitly enabling substitution under tests without reflection magic frameworks typically unnecessary idiomatic Go.

Practice composing `OrderService` wiring repository + structured logger collaborator minimalistically—defer heavy DI frameworks purposely unless organisational policy mandates externally later verify reality then.

Interview drill: verbally justify manual wiring simplicity trade spectrum vs heavyweight runtime container introspection complexity costs rarely justified early lifecycles.
