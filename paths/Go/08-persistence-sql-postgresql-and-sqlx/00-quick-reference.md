# Quick Reference — PostgreSQL & sqlx

## Connect
db, err := sqlx.Connect("pgx", os.Getenv("DATABASE_URL"))
db.SetMaxOpenConns(25)
db.SetMaxIdleConns(5)
db.SetConnMaxLifetime(5 * time.Minute)

## Query patterns
db.GetContext(ctx, &dest, query, args...)    // one row
db.SelectContext(ctx, &dest, query, args...) // many rows
db.ExecContext(ctx, query, args...)          // no rows returned
db.NamedExecContext(ctx, query, struct{})    // named params

## Struct tags
type User struct {
    ID    int    `db:"id"`
    Email string `db:"email"`
}

## NULL handling
type NullableUser struct {
    Bio sql.NullString `db:"bio"`
}
// check: u.Bio.Valid before u.Bio.String

## Transaction
tx, _ := db.BeginTxx(ctx, nil)
defer tx.Rollback()
// ... work ...
tx.Commit()

## Error sentinel
errors.Is(err, sql.ErrNoRows) // not found
