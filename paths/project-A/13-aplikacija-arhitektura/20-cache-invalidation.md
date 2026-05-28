# 20 — Cache Invalidation: Strategije i Produkcijski Paterni

Cache invalidation je jedan od najtežih problema u programiranju. Redis TTL je osnova, ali nije dovoljno za sve slučajeve — potrebna je kombinacija strategija ovisno o tipu podataka.

---

## Tri strategije invalidacije

```
1. TTL-based (expiry):    Cache istekne nakon N sekundi
   Pros: jednostavno     Cons: stale data N sekundi

2. Event-based:           Cache se briše/ažurira kada se podaci promijene
   Pros: uvijek svježe   Cons: mora biti implementirano za svaki event

3. Cache-aside pattern:  App upravljaju cache-om ručno
   Pros: kontrola        Cons: kompleksnost
```

U praksi se kombinuju: TTL kao sigurnosna mreža, event-based za kritične podatke.

---

## Cache-aside pattern u Go

```go
type UserCache struct {
    redis *redis.Client
    db    *database.DB
}

const userCacheTTL = 5 * time.Minute

func (c *UserCache) GetUser(ctx context.Context, id int64) (*User, error) {
    // 1. Pokušaj iz cache-a
    key := fmt.Sprintf("user:%d", id)
    cached, err := c.redis.Get(ctx, key).Bytes()
    if err == nil {
        var user User
        if err := json.Unmarshal(cached, &user); err == nil {
            return &user, nil  // Cache hit
        }
    }

    // 2. Cache miss: dohvati iz DB
    user, err := c.db.Read().QueryRowContext(ctx,
        "SELECT id, email, is_active FROM users WHERE id = ?", id,
    ).Scan(...)
    if err != nil {
        return nil, err
    }

    // 3. Spremi u cache
    data, _ := json.Marshal(user)
    c.redis.SetEx(ctx, key, data, userCacheTTL)

    return user, nil
}

// Invalidacija pri promjeni:
func (c *UserCache) UpdateUser(ctx context.Context, user *User) error {
    // 1. Ažuriraj DB
    _, err := c.db.Write().ExecContext(ctx,
        "UPDATE users SET email=?, updated_at=NOW() WHERE id=?",
        user.Email, user.ID,
    )
    if err != nil {
        return err
    }

    // 2. Invalidate cache (ne ažuriraj — briši!)
    key := fmt.Sprintf("user:%d", user.ID)
    c.redis.Del(ctx, key)
    // Sljedeći GetUser će učitati svježe iz DB

    return nil
}
```

**Zašto brisati umjesto ažurirati:** Ažuriranje cache-a nakon DB write-a može unijeti race condition — drugi request može pročitati stari podatak između DB write-a i cache write-a. Brisanje je sigurnije: sljedeći read uvijek ide na DB.

---

## Write-through pattern

```go
func (c *UserCache) UpdateUserWriteThrough(ctx context.Context, user *User) error {
    // Transakcija: DB update
    tx, _ := c.db.Write().BeginTx(ctx, nil)
    defer tx.Rollback()

    _, err := tx.ExecContext(ctx, "UPDATE users SET ...", ...)
    if err != nil {
        return err
    }

    if err := tx.Commit(); err != nil {
        return err
    }

    // Update cache sa novim podacima
    data, _ := json.Marshal(user)
    c.redis.SetEx(ctx, fmt.Sprintf("user:%d", user.ID), data, userCacheTTL)

    return nil
}
```

Write-through smanjuje cache miss nakon write-a, ali povećava latenciju write operacije. Koristiti za podatke koji se odmah čitaju nakon pisanja (npr. user profil nakon update-a).

---

## Bulk invalidacija — lista korisnika

```go
// Kada se promijeni rola, invalidate sve liste koje sadrže tog korisnika
func (c *UserCache) InvalidateUserRelated(ctx context.Context, userID int64) error {
    // Pattern brisanje — obrisati sve ključeve koji se odnose na korisnika
    keys, err := c.redis.Keys(ctx, fmt.Sprintf("*user:%d*", userID)).Result()
    if err != nil {
        return err
    }
    if len(keys) > 0 {
        c.redis.Del(ctx, keys...)
    }

    // Invalidate liste (npr. user listing cache)
    c.redis.Del(ctx, "users:list:*")  // Wildcard briše sve liste

    return nil
}
```

---

## Redis SCAN za wildcard brisanje (produkcija-safe, ne KEYS!)

```go
// NIKAD ne koristiti KEYS * u produkciji (blokira Redis)
// Koristiti SCAN:
func (c *UserCache) DeletePattern(ctx context.Context, pattern string) error {
    var cursor uint64
    for {
        var keys []string
        var err error
        keys, cursor, err = c.redis.Scan(ctx, cursor, pattern, 100).Result()
        if err != nil {
            return err
        }
        if len(keys) > 0 {
            c.redis.Del(ctx, keys...)
        }
        if cursor == 0 {
            break
        }
    }
    return nil
}
```

`KEYS *` je O(N) i blokira Redis event loop dok ne vrati sve ključeve. Na produkciji sa milionima ključeva može uzrokovati timeout za sve ostale operacije. `SCAN` iterira po 100 ključeva u svakom pozivu, ne blokira.

---

## Session cache invalidacija

```go
// Logout: obriši sve sesije korisnika
func (s *AuthService) Logout(ctx context.Context, userID int64, refreshToken string) error {
    // 1. Obriši refresh token
    s.redis.Del(ctx, "refresh:"+refreshToken)

    // 2. Obriši user cache (da se promjene odmah vide)
    s.redis.Del(ctx, fmt.Sprintf("user:%d", userID))

    return nil
}

// Promjena lozinke: invalidate SVE sesije korisnika
func (s *AuthService) ChangePassword(ctx context.Context, userID int64, newPass string) error {
    // ... update DB ...

    // Invalidate sve refresh tokene ovog korisnika
    s.DeletePattern(ctx, fmt.Sprintf("refresh:*"))
    // Note: precizniji pristup - čuvati set refresh tokena po userID-u

    // Invalidate user cache
    s.redis.Del(ctx, fmt.Sprintf("user:%d", userID))

    return nil
}
```

**Precizniji pristup za invalidaciju svih sesija jednog korisnika:** Čuvati `Set` u Redisu sa svim refresh tokenima po userID-u (`user_tokens:{userID}`). Pri promjeni lozinke, dohvatiti set i obrisati sve tokene. Izbjegava SCAN po cijelom namespace-u.

---

## TTL strategija po tipu podataka

```go
const (
    UserProfileTTL     = 5 * time.Minute    // Korisnik profil (relativno stabilno)
    SessionTTL         = 15 * time.Minute   // JWT access token trajanje
    RefreshTokenTTL    = 7 * 24 * time.Hour // Refresh token
    FeatureFlagsTTL    = 1 * time.Minute    // Feature flags (brza promjena)
    StaticConfigTTL    = 1 * time.Hour      // Rijetko mijenjana konfiguracija
    EmailVerifyTTL     = 24 * time.Hour     // Verifikacijski token
)
```

TTL uskladiti sa poslovnim zahtjevima: koliko dugo možemo tolerisati stale data? Za feature flags 1 minuta — nova zastavica se aktivira za maksimalno 1 minutu. Za user profil 5 minuta je prihvatljivo.

---

## Monitoring cache hit rate

```go
var (
    cacheHits   = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "cache_hits_total"}, []string{"key_type"})
    cacheMisses = prometheus.NewCounterVec(prometheus.CounterOpts{Name: "cache_misses_total"}, []string{"key_type"})
)

// PromQL za cache hit rate:
// rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
// Target: > 80% hit rate
```

Ako hit rate padne ispod 80%, ili je TTL prekratak, ili se cache prečesto invalidira, ili nema dovoljno memorije i Redis eviktuje ključeve (provjeri `maxmemory-policy`).

---

## Sažetak: kada koristiti koju strategiju

| Situacija | Strategija |
|---|---|
| Podaci se rijetko mijenjaju | TTL (duži interval) |
| Podaci se mijenjaju i odmah čitaju | Write-through |
| Podaci se mijenjaju, read nije odmah | Cache-aside + invalidate on write |
| Jedna promjena utječe na mnogo ključeva | Event-based bulk invalidation sa SCAN |
| Session/auth tokeni | Explicit delete pri logout/password change |
