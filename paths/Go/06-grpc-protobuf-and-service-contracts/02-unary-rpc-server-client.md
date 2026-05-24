# Unit 2 — Unary RPC choreography: codegen → server skeleton → exercised client harness

Practice service definition illustrative:

```
service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (Order);
  rpc GetOrder(GetOrderRequest) returns (Order);
}
```

Produce Go server registration + minimal client exercised via CLI or integration test—even if ephemeral `bufconn` in-process style acceptable learning accelerant.

Enumerate contrasts REST multi-roundtrip chatter vs aggregated RPC shapes trade spectrum avoiding tribal absolutes.

Interview drill: verbally justify synchronous RPC chaining latency hazards previewing saga / asynchronous queue bridging forward areas.
