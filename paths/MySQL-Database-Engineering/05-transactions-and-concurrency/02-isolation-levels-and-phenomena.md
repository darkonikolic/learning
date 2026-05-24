# Unit 02 — Isolation level ladder (conceptual reproduction)

Compare `READ UNCOMMITTED`, `READ COMMITTED`, `REPEATABLE READ`, `SERIALIZABLE` narratives.

MySQL / InnoDB default typically `REPEATABLE READ` — validate on your instance (`SHOW VARIABLES LIKE 'transaction_isolation';`).

Labs attempt dirty read / non-repeatable / phantom class demonstrations where engine semantics allow (some phenomena intentionally prevented—document outcomes truthfully).
