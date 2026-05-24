# Unit 4 — RBAC / authorisation modelling in services

Separate **authentication** from **authorisation**:

```
roles / permissions
resource-scoped checks (“can this user settle this payment?”)
policy evaluation location (middleware vs service layer—both have trade-offs)
```

Practice: design a small permission matrix for admin vs merchant vs customer personas for `auth-service/`.
