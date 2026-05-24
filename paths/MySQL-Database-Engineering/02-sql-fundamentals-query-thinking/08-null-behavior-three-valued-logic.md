# Unit 08 — NULL semantics and defensive expressions

Use payment-like columns (`paid_at`, nullable `coupon_id`, `refund_reason`) to observe sentinel vs unknown distinctions.

Practice `COALESCE`, `NULLIF`, MySQL-specific `IFNULL` awareness (portability caveat).

Labs:

Explain why `NULL = NULL` is not true in SQL logic.

Contrast `COUNT(*)` grain vs `COUNT(column)` omission of NULL rows.

Interview: propagation of UNKNOWN in predicates; unintended outer-join fallout.
