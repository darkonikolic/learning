# Unit 5 — Schema Evolution and Compatibility

## Concept

Proto field numbers are the wire contract — they are embedded in every serialized message. Changing or reusing a field number after removing the original field causes silent data corruption: old clients read the new field's bytes and interpret them as the old type. Field numbers are permanent. Safe changes: add a new field with a new number, rename a field (names are not on the wire). Unsafe: change field type, reuse a retired number, change `repeated` to singular. Use `reserved` to prevent future accidents when removing fields.

## Code

```proto
// product.proto — version 1 (original)
message Product {
  int64  id    = 1;
  string name  = 2;
  double price = 3;
  int32  stock = 4;
}
```

```proto
// product.proto — version 2 (safe evolution: new field added)
message Product {
  int64  id       = 1;
  string name     = 2;
  double price    = 3;
  int32  stock    = 4;
  string category = 5;  // NEW: safe — uses a new field number
}

// What happens when old client receives a v2 message:
// - Fields 1-4 are decoded normally (same numbers, same types)
// - Field 5 (category) is UNKNOWN to the old client — it is silently ignored
// - Old client sees a valid Product with category == "" (zero value)
// This is backward compatible.
```

```proto
// product.proto — version 3 (removing a field safely)
message Product {
  int64  id    = 1;
  string name  = 2;
  double price = 3;
  // stock removed — MUST reserve the number to prevent accidental reuse
  reserved 4;
  reserved "stock";  // reserve the name too (best practice)

  string category = 5;
  // WRONG (do not do this): reusing field 4 for a new field
  // string sku = 4;  // would decode old stock bytes as a string — silent corruption
}
```

```proto
// What breaks compatibility — do not do these:
message BadEvolution {
  int64  id    = 1;
  string name  = 2;
  // WRONG: changed field 3 from double to string
  string price = 3;  // old clients expect double bytes — silent corruption

  // WRONG: reused field 4 after removing stock
  string sku   = 4;  // old clients decode sku bytes as int32 stock
}
```

```go
// Verifying backward compatibility in a test:
// Serialize a v2 Product (with category), deserialize as v1 Product.
// Fields 1-4 must decode correctly. Field 5 (category) must be silently ignored.

func TestBackwardCompatibility(t *testing.T) {
	// v2 message with category set
	v2 := &productv2.Product{
		Id:       1,
		Name:     "Widget",
		Price:    9.99,
		Stock:    100,
		Category: "electronics",
	}

	// Serialize to bytes
	data, err := proto.Marshal(v2)
	if err != nil {
		t.Fatal(err)
	}

	// Deserialize as v1 (no category field)
	v1 := &productv1.Product{}
	if err := proto.Unmarshal(data, v1); err != nil {
		t.Fatal(err)
	}

	// v1 fields must be intact — category is ignored
	if v1.Id != 1 || v1.Name != "Widget" || v1.Price != 9.99 {
		t.Errorf("backward compat broken: %+v", v1)
	}
	// v1 does not have Category field — this is expected
}
```

## Exercise

**Build:** Add a `category string` field as field number 5 to your `Product` proto. Generate the new code. Write a backward compatibility test: serialize a v2 `Product` (with category set), deserialize it using the v1 generated struct (without the category field), assert that fields 1-4 are still correct.

**Input:** `Product{id:1, name:"Widget", price:9.99, stock:100, category:"electronics"}` serialized as v2.

**Output:** When deserialized as v1: `id=1, name="Widget", price=9.99, stock=100`. Category is ignored without error.

**Acceptance:** Test passes. Add a `reserved 6;` line to the proto for a field you plan to add later — this documents the intent. Run `go test ./...`.

## Interview

- Why is reusing a proto field number after removing the original field so dangerous?
- A colleague wants to rename field `price` to `unit_price` in the proto. Is this safe? What changes at the wire level versus the API level?
- What does `reserved` do in a proto file, and why should you add it when removing a field?
