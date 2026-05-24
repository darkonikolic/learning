# Unit 5 — Validation discipline: mistrust payloads structurally (`validator` toolkit)

Practice endpoint hardening **`POST /users`** (extend analogously orders/products iterating forward).

Typical validations:

```
required • string length sane bounds • basic email lexical pattern • numeric ranges
```

Articulate layering:

| Validation tier | Responsibility |
|-----------------|----------------|
| structural / schema | tags / explicit checks |
| business invariants deeper | possibly service enforcing cross-field rules |

## Lab adversity testing

Fabricate purposely malicious JSON bodies provoking:

```
400 coherent problem detail (shape stable)
versus leaking internal sentinel strings carelessly deprecating reviewer trust.
```

Interview emphasis: distinguishing **caller misuse** (4xx classification) versus **unexpected internal defect** disguised clumsily.
