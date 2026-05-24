# Unit 1 — Serialization & protocol layering between REST(JSON) ⇄ gRPC(Protobuf)

## Learning outcome

Articulate transport + encoding **as explicit architecture choices**—not accidental defaults drifting.

## Comparative lenses

| Concern | JSON / REST typical | Protobuf / gRPC typical |
|---------|---------------------|---------------------------|
| human debug agility | strengths | tooling mitigations (`grpcurl`/reflection hazards) |
| payload efficiency | variability | tendency strength |
| contract evolution coupling | swagger/OpenAPI ecosystem cultural momentum | codegen + breaking change vigilance intensified |
| browser friendliness | direct | gateways/bff patterns often necessary |

Practice narrative vignette rewriting simplistic JSON REST synergy service pair into internal protobuf-backed RPC emphasizing **explicit compatibility contract maintenance tax** acceptance.

Interview focal phrases:

```
protobuf vs JSON trade matrix (no caricature extremes)
streaming-only-when-justified discipline
backward compatibility philosophies bridging HTTP OpenAPI ecosystems vs protobuf field numbering regimes
internal vs external gateway boundary clarity
```

This unit intentionally **dense prose** consolidating earlier HTTP + gRPC arc glue—reuse as rehearsal sheet before interviewing narratively bridging both worlds.
