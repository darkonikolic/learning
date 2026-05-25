# Quick Reference — Serialization

## JSON struct tags
`json:"name"`            // rename field
`json:"name,omitempty"` // skip if zero/nil/empty
`json:"-"`              // always skip

## Common pitfalls
- Unexported fields are silently ignored
- nil slice → null; empty slice → []  (know the difference)
- time.Time: marshals to RFC3339 by default
- Integers > 2^53 lose precision in JS — use string

## Protobuf field rules
- Never reuse or change a field number
- Safe: add new field, rename field, add new message
- Unsafe: change field type, change field number, remove required

## When to use what
JSON: external APIs, webhooks, config files, logs
Proto: internal RPC, high-throughput pipelines
