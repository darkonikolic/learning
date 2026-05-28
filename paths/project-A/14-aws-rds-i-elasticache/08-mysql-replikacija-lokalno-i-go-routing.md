# 08 — MySQL replikacija: mehanika, lokalni Docker setup i Go routing

## Pregled

Ovaj modul pokriva kompletnu replikacijsku sliku — od binlog internala do produkcijskog Go koda koji transparentno routuje read/write zahtjeve. Lokalni Docker setup je funkcionalna replika AWS RDS read-replica arhitekture iz modula 07.

---

## 1. MySQL replikacija — mehanika

### Kako replikacija zaista radi

```
Master:
  Svaki write (INSERT/UPDATE/DELETE/DDL) → Binary Log (binlog)
  Binlog = sekvencijalni log svih promjena sa pozicijom (file + offset)

Slave (IO Thread):
  Konektuje se na master koristeći replikacijski user
  Čita binlog od zadnje poznate pozicije
  Sprema podatke u lokalni Relay Log na disku

Slave (SQL Thread):
  Čita Relay Log sekvenčno
  Izvršava SQL operacije lokalno na slave instancei
  Replication lag = kašnjenje SQL threada za IO threadom

Tok podataka:
  [Client Write] → [Master binlog] → [Slave IO Thread] → [Relay Log] → [Slave SQL Thread] → [Slave data]
```

### Binlog formati

```
STATEMENT: Loguje originalni SQL — kompaktan, ali nedeterministički (NOW(), UUID(), rand())
ROW:       Loguje promijenjene redove — veći, ali deterministički i siguran
MIXED:     Automatski bira između STATEMENT i ROW — ne koristiti u produkciji

Preporuka: binlog_format = ROW za replikaciju
```

### GTID — Global Transaction Identifier

GTID je moderniji pristup koji eliminira pozicijsko trackiranje:

```
Format: server-uuid:transaction-number
Primjer: a3d1e2f0-1234-5678-abcd-ef0123456789:1-1000

Prednosti GTID vs pozicijskog trackinga:
  - Slave zna točno koje transakcije ima, ne treba binlog file+offset
  - Failover je trivijalan — novi master se automatski locira
  - Lakša detekcija duplikata i grešaka
  - Osnova za multi-source replikaciju

GTID set na masteru: pokazuje sve transakcije koje su se desile
GTID set na slaveu: pokazuje koje transakcije slave ima
Gap između ta dva seta = replika lag u transakcijama
```

---

## 2. Lokalni Docker Compose setup

### Struktura projekta

```
docker/
  mysql/
    master.cnf
    slave.cnf
    init-slave.sh
docker-compose.override.yml
.env
```

### docker-compose.override.yml

```yaml
services:
  mysql-master:
    image: mysql:8.0
    container_name: mysql-master
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: project_a
      MYSQL_USER: app
      MYSQL_PASSWORD: ${MYSQL_APP_PASSWORD}
      MYSQL_REPLICATION_USER: replicator
      MYSQL_REPLICATION_PASSWORD: ${MYSQL_REPLICATION_PASSWORD}
    volumes:
      - mysql-master-data:/var/lib/mysql
      - ./docker/mysql/master.cnf:/etc/mysql/conf.d/master.cnf:ro
    ports:
      - "3306:3306"
    networks:
      - app-network
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  mysql-slave:
    image: mysql:8.0
    container_name: mysql-slave
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_REPLICATION_PASSWORD: ${MYSQL_REPLICATION_PASSWORD}
    volumes:
      - mysql-slave-data:/var/lib/mysql
      - ./docker/mysql/slave.cnf:/etc/mysql/conf.d/slave.cnf:ro
      - ./docker/mysql/init-slave.sh:/docker-entrypoint-initdb.d/init-slave.sh:ro
    ports:
      - "3307:3306"
    networks:
      - app-network
    depends_on:
      mysql-master:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 60s

volumes:
  mysql-master-data:
  mysql-slave-data:

networks:
  app-network:
    driver: bridge
```

### docker/mysql/master.cnf

```ini
[mysqld]
server-id                = 1
log_bin                  = mysql-bin
binlog_format            = ROW           # deterministički, siguran za sve write tipove
gtid_mode                = ON            # GTID replikacija umjesto pozicijskog trackinga
enforce_gtid_consistency = ON            # zabranjuje transakcije koje se ne mogu GTID-replicirati
binlog_do_db             = project_a     # repliciraj samo ovu bazu (filtriranje na masteru)
expire_logs_days         = 7             # čuvaj binlog 7 dana — dovoljno za recovery
max_binlog_size          = 100M          # rotacija fajla na 100MB
sync_binlog              = 1             # flush binlog na disk pri svakoj transakciji (sigurnost)
innodb_flush_log_at_trx_commit = 1       # ACID compliant, kombinacija sa sync_binlog
```

### docker/mysql/slave.cnf

```ini
[mysqld]
server-id                = 2             # mora biti jedinstven u replikacijskom skupu
relay_log                = mysql-relay-bin
log_bin                  = mysql-bin     # slave treba vlastiti binlog (za chain replikaciju)
gtid_mode                = ON
enforce_gtid_consistency = ON
read_only                = ON            # slave odbija direktne write-ove od regularnih usera
super_read_only          = ON            # čak ni root ne može pisati direktno (MySQL 5.7.8+)
log_slave_updates        = ON            # slave bilježi primljene promjene u vlastiti binlog
replica_preserve_commit_order = ON       # paralel replikacija uz očuvanje redosljeda commitova
```

### docker/mysql/init-slave.sh

```bash
#!/bin/bash
set -e

echo "=== MySQL Slave Initialization ==="

# Sačekaj da master bude spreman i dostupan
until mysql -h mysql-master -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SELECT 1" &>/dev/null; do
    echo "Waiting for master to be ready..."
    sleep 3
done

echo "Master is ready. Setting up replication user..."

# Kreiraj replikacijskog usera na masteru
mysql -h mysql-master -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL
    CREATE USER IF NOT EXISTS 'replicator'@'%'
        IDENTIFIED WITH mysql_native_password BY '${MYSQL_REPLICATION_PASSWORD}';
    GRANT REPLICATION SLAVE ON *.* TO 'replicator'@'%';
    FLUSH PRIVILEGES;
EOSQL

echo "Replication user created. Dumping master data..."

# Dump master podataka na slave — inicijalna sinkronizacija
# --single-transaction: konzistentan snapshot bez lock tablice
# --set-gtid-purged=OFF: ne uključuj GTID_PURGED u dump (slave će to sam riješiti)
mysqldump \
    -h mysql-master \
    -u root -p"${MYSQL_ROOT_PASSWORD}" \
    --single-transaction \
    --set-gtid-purged=OFF \
    --all-databases \
    | mysql -u root -p"${MYSQL_ROOT_PASSWORD}"

echo "Data dump complete. Configuring replication..."

# Konfiguriraj i pokrni slave replikaciju
mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL
    STOP REPLICA;
    RESET REPLICA ALL;
    CHANGE REPLICATION SOURCE TO
        SOURCE_HOST     = 'mysql-master',
        SOURCE_PORT     = 3306,
        SOURCE_USER     = 'replicator',
        SOURCE_PASSWORD = '${MYSQL_REPLICATION_PASSWORD}',
        SOURCE_AUTO_POSITION = 1;    -- GTID auto-position: slave traži transakcije koje nema
    START REPLICA;
EOSQL

echo "=== Slave replication started successfully ==="
```

### Provjera replikacije

```bash
# Status slave replikacije — svi važni fieldovi
docker exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SHOW REPLICA STATUS\G" \
  | grep -E "Replica_IO_Running|Replica_SQL_Running|Seconds_Behind_Source|Last_Error|Source_Host"

# Ispravno stanje mora biti:
# Replica_IO_Running: Yes
# Replica_SQL_Running: Yes
# Seconds_Behind_Source: 0
# Last_Error: (prazno)

# Funkcionalni test replikacije:
docker exec mysql-master mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "INSERT INTO project_a.users (email, password_hash) VALUES ('test@test.com', 'hash123');"

# Odmah provjeri na slaveu (mora biti < 1s za lokalni setup):
docker exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SELECT email FROM project_a.users WHERE email='test@test.com';"

# GTID status — provjera sinkronizacije:
docker exec mysql-master mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SELECT @@GLOBAL.gtid_executed\G"

docker exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SELECT @@GLOBAL.gtid_executed\G"
# Oba GTID setovi moraju biti identični za potpunu sinkronizaciju
```
> **Podman:** `podman exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SHOW REPLICA STATUS\G"` (i analogno za ostale `docker exec` pozive — zamijeni `docker` sa `podman`)

---

## 3. Go service: read/write routing

### Osnovna struktura — database package

```go
// internal/database/db.go
package database

import (
    "context"
    "database/sql"
    "fmt"
    "time"

    _ "github.com/go-sql-driver/mysql"
)

// DB enkapsulira master i replica konekciju.
// Sav aplikacijski kod koristi ovu strukturu — nikada direktno *sql.DB.
type DB struct {
    master  *sql.DB
    replica *sql.DB
}

// Config drži DSN parametre za obje konekcije.
type Config struct {
    MasterDSN  string
    ReplicaDSN string
}

// New kreira i konfigurira DB sa connection poolovima.
func New(cfg Config) (*DB, error) {
    master, err := open(cfg.MasterDSN)
    if err != nil {
        return nil, fmt.Errorf("master connection: %w", err)
    }

    replica, err := open(cfg.ReplicaDSN)
    if err != nil {
        master.Close()
        return nil, fmt.Errorf("replica connection: %w", err)
    }

    return &DB{master: master, replica: replica}, nil
}

func open(dsn string) (*sql.DB, error) {
    db, err := sql.Open("mysql", dsn)
    if err != nil {
        return nil, err
    }

    // Connection pool konfiguracija — prilagodi prema load profilu
    db.SetMaxOpenConns(25)           // maksimalan broj otvorenih konekcija
    db.SetMaxIdleConns(5)            // konekcije u idle poolu
    db.SetConnMaxLifetime(5 * time.Minute)  // recycle konekcija (MySQL timeout prevention)
    db.SetConnMaxIdleTime(1 * time.Minute)  // zatvori idle konekcije brže od Lifetime

    return db, nil
}

// Write vraća master konekciju — uvijek koristi za INSERT/UPDATE/DELETE/DDL.
func (db *DB) Write() *sql.DB {
    return db.master
}

// Read vraća replica konekciju za SELECT upite.
// Fallback na master ako replika nije dostupna.
func (db *DB) Read() *sql.DB {
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    if err := db.replica.PingContext(ctx); err != nil {
        // Replica nije dostupna — transparentni fallback na master.
        // Ovo treba logovati jer indicira replikacijski problem.
        return db.master
    }
    return db.replica
}

// ReadCtx respektuje context koji signalizira recentni write.
// Koristi se za "read your own writes" pattern.
func (db *DB) ReadCtx(ctx context.Context) *sql.DB {
    if hasRecentWrite(ctx) {
        return db.master
    }
    return db.Read()
}

// Close zatvara obje konekcije.
func (db *DB) Close() error {
    masterErr := db.master.Close()
    replicaErr := db.replica.Close()
    if masterErr != nil {
        return fmt.Errorf("closing master: %w", masterErr)
    }
    if replicaErr != nil {
        return fmt.Errorf("closing replica: %w", replicaErr)
    }
    return nil
}

// HealthCheck provjerava obje konekcije i vraća status.
func (db *DB) HealthCheck(ctx context.Context) map[string]string {
    status := make(map[string]string)

    if err := db.master.PingContext(ctx); err != nil {
        status["master"] = fmt.Sprintf("unhealthy: %v", err)
    } else {
        status["master"] = "ok"
    }

    if err := db.replica.PingContext(ctx); err != nil {
        status["replica"] = fmt.Sprintf("unhealthy: %v", err)
    } else {
        // Provjeri replikacijski lag
        var lag sql.NullInt64
        row := db.replica.QueryRowContext(ctx,
            "SELECT TIMESTAMPDIFF(SECOND, MIN(ts), NOW()) FROM replication_heartbeat LIMIT 1")
        if err := row.Scan(&lag); err == nil && lag.Valid {
            if lag.Int64 > 30 {
                status["replica"] = fmt.Sprintf("lagging: %ds behind", lag.Int64)
            } else {
                status["replica"] = fmt.Sprintf("ok (lag: %ds)", lag.Int64)
            }
        } else {
            status["replica"] = "ok"
        }
    }

    return status
}
```

### Context propagacija za recentne write-ove

```go
// internal/database/context.go
package database

import "context"

type contextKey string

const recentWriteKey contextKey = "db_recent_write"

// WithRecentWrite označava context kao "imao write operaciju".
// Koristi se u HTTP handler middleware-u ili service sloju.
func WithRecentWrite(ctx context.Context) context.Context {
    return context.WithValue(ctx, recentWriteKey, true)
}

func hasRecentWrite(ctx context.Context) bool {
    v, ok := ctx.Value(recentWriteKey).(bool)
    return ok && v
}
```

### Repository pattern — primjer

```go
// internal/repository/user_repository.go
package repository

import (
    "context"
    "database/sql"
    "errors"
    "fmt"
    "time"

    "github.com/yourorg/project-a/internal/database"
)

var ErrNotFound = errors.New("record not found")

type User struct {
    ID           int64
    Email        string
    PasswordHash string
    CreatedAt    time.Time
}

type UserRepository struct {
    db *database.DB
}

func NewUserRepository(db *database.DB) *UserRepository {
    return &UserRepository{db: db}
}

// Create upisuje novog korisnika na master.
func (r *UserRepository) Create(ctx context.Context, email, passwordHash string) (*User, error) {
    result, err := r.db.Write().ExecContext(ctx,
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, NOW())",
        email, passwordHash,
    )
    if err != nil {
        return nil, fmt.Errorf("insert user: %w", err)
    }

    id, err := result.LastInsertId()
    if err != nil {
        return nil, fmt.Errorf("last insert id: %w", err)
    }

    // Odmah čitaj SA MASTERA — "read your own writes" pattern.
    // Replika možda još nema ovaj red (replication lag).
    return r.findByIDOnMaster(ctx, id)
}

// FindByEmail čita sa replike — optimalan za read-heavy load.
func (r *UserRepository) FindByEmail(ctx context.Context, email string) (*User, error) {
    row := r.db.ReadCtx(ctx).QueryRowContext(ctx,
        "SELECT id, email, password_hash, created_at FROM users WHERE email = ?",
        email,
    )
    return scanUser(row)
}

// FindByID čita sa replike, ali respektuje recent-write context.
func (r *UserRepository) FindByID(ctx context.Context, id int64) (*User, error) {
    row := r.db.ReadCtx(ctx).QueryRowContext(ctx,
        "SELECT id, email, password_hash, created_at FROM users WHERE id = ?",
        id,
    )
    return scanUser(row)
}

// List čita listu korisnika sa replike — idealan za analytics/preglede.
func (r *UserRepository) List(ctx context.Context, limit, offset int) ([]*User, error) {
    rows, err := r.db.Read().QueryContext(ctx,
        "SELECT id, email, password_hash, created_at FROM users ORDER BY id LIMIT ? OFFSET ?",
        limit, offset,
    )
    if err != nil {
        return nil, fmt.Errorf("list users: %w", err)
    }
    defer rows.Close()

    var users []*User
    for rows.Next() {
        u := &User{}
        if err := rows.Scan(&u.ID, &u.Email, &u.PasswordHash, &u.CreatedAt); err != nil {
            return nil, fmt.Errorf("scan user: %w", err)
        }
        users = append(users, u)
    }
    return users, rows.Err()
}

// Update piše na master i označava context kao "imao write".
func (r *UserRepository) Update(ctx context.Context, id int64, email string) error {
    _, err := r.db.Write().ExecContext(ctx,
        "UPDATE users SET email = ? WHERE id = ?",
        email, id,
    )
    return err
}

// Delete briše na masteru.
func (r *UserRepository) Delete(ctx context.Context, id int64) error {
    result, err := r.db.Write().ExecContext(ctx,
        "DELETE FROM users WHERE id = ?", id,
    )
    if err != nil {
        return fmt.Errorf("delete user: %w", err)
    }
    affected, _ := result.RowsAffected()
    if affected == 0 {
        return ErrNotFound
    }
    return nil
}

// findByIDOnMaster čita direktno sa mastera — interno za post-write read.
func (r *UserRepository) findByIDOnMaster(ctx context.Context, id int64) (*User, error) {
    row := r.db.Write().QueryRowContext(ctx,
        "SELECT id, email, password_hash, created_at FROM users WHERE id = ?", id,
    )
    return scanUser(row)
}

func scanUser(row *sql.Row) (*User, error) {
    u := &User{}
    err := row.Scan(&u.ID, &u.Email, &u.PasswordHash, &u.CreatedAt)
    if err != nil {
        if errors.Is(err, sql.ErrNoRows) {
            return nil, ErrNotFound
        }
        return nil, fmt.Errorf("scan user: %w", err)
    }
    return u, nil
}
```

### HTTP middleware za recent-write propagaciju

```go
// internal/middleware/db_context.go
package middleware

import (
    "net/http"

    "github.com/yourorg/project-a/internal/database"
)

// WriteAwareHandler je middleware koji postavlja recent-write flag
// u context na osnovu HTTP metode.
// Koristi se na route-ima gdje POST/PUT/PATCH odmah vraca 200 sa tijelom.
func WriteAwareHandler(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx := r.Context()

        switch r.Method {
        case http.MethodPost, http.MethodPut, http.MethodPatch, http.MethodDelete:
            // Mutating request — sve read operacije u ovom requestu idu na master
            ctx = database.WithRecentWrite(ctx)
        }

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}
```

---

## 4. Replication lag handling — trade-off, ne obaveza

**Ovo je trade-off, ne nešto što moraš uvijek implementirati.**

Replikacijski lag lokalno je < 1ms, na AWS RDS tipično < 5ms. Za 90% ecommerce operacija eventual consistency je prihvatljiva — korisnik ne primjeti ništa. Optimistic UI update (Vue ažurira lokalni state bez ponovnog čitanja) eliminira problem bez ijedne linije backend koda.

**Kada je problem stvaran:**
- Korisnik promijeni lozinku → page refresh → vidi staru lozinku na replici
- Plaćanje → redirect na "order confirmed" → order još nije na replici
- Kritične operacije gdje stale read = vidljivi bug za korisnika

**Preporuka: počni bez ovoga. Dodaj samo za konkretne endpoint-e gdje vidiš problem.**

```
Prioritet rješenja (od najjednostavnijeg):
1. Optimistic UI — Vue ažurira state lokalno, nema re-fetch
2. Force master samo za specifičan endpoint (login, order confirm)
3. Context propagacija — samo ako #2 nije dovoljno
```

---

### Problem: "read your own writes"

```
Vremenski slijed problema:
  t=0ms   POST /users — INSERT na master, response 201 Created
  t=1ms   GET /users/123 — SELECT na repliku — replika nema red jos!
  t=50ms  Replika dobija podatak (replication lag)

Rezultat: korisnik vidi 404 ili stare podatke odmah nakon kreacije.
Ucestalost: rijetko u praksi za vecinu ecommerce operacija.
```

### Rješenje 1 — direktno master čitanje post-write

```go
// UserService.Register uvijek vraca svježe podatke sa mastera
func (s *UserService) Register(ctx context.Context, email, password string) (*User, error) {
    hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
    if err != nil {
        return nil, err
    }

    // Create interno čita sa mastera (findByIDOnMaster)
    user, err := s.repo.Create(ctx, email, string(hash))
    if err != nil {
        return nil, err
    }

    // Označi context — sve daljnje read operacije u ovom requestu idu na master
    // Koristi se ako service layer dalje poziva druge read metode
    _ = database.WithRecentWrite(ctx)

    return user, nil
}
```

### Rješenje 2 — session-based sticky read

```go
// Za web aplikacije: stavi flag u session cookie nakon write-a
// Handler čita flag i proslijedi ga u context
func (h *UserHandler) RegisterHandler(w http.ResponseWriter, r *http.Request) {
    user, err := h.service.Register(r.Context(), email, password)
    if err != nil {
        http.Error(w, err.Error(), http.StatusBadRequest)
        return
    }

    // Postavi session flag — sljedeći request ovog usera čita sa mastera
    session := getSession(r)
    session.Values["read_from_master_until"] = time.Now().Add(500 * time.Millisecond).Unix()
    session.Save(r, w)

    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(user)
}
```

### Rješenje 3 — GTID-based wait (napredni pattern)

```go
// Nakon write-a na masteru, sačekaj da replika ima taj GTID
// Ovo garantuje konzistentnost bez hard-coding na master
func (db *DB) WaitForReplication(ctx context.Context, gtid string, timeoutSec int) error {
    // SOURCE_POS_WAIT čeka da replika dostigne zadati GTID
    var result sql.NullInt64
    row := db.replica.QueryRowContext(ctx,
        "SELECT WAIT_FOR_EXECUTED_GTID_SET(?, ?)",
        gtid, timeoutSec,
    )
    if err := row.Scan(&result); err != nil {
        return fmt.Errorf("gtid wait: %w", err)
    }
    if !result.Valid || result.Int64 == -1 {
        return fmt.Errorf("replica did not catch up within %d seconds", timeoutSec)
    }
    return nil
}

// Dohvati GTID zadnje transakcije sa mastera
func (db *DB) LastGTID(ctx context.Context) (string, error) {
    var gtid string
    row := db.master.QueryRowContext(ctx, "SELECT @@GLOBAL.gtid_executed")
    if err := row.Scan(&gtid); err != nil {
        return "", err
    }
    return gtid, nil
}
```

---

## 5. Monitoring replikacije

### SQL provjera replikacijskog statusa

```sql
-- Na slave instancei — pregled ključnih metrika:
SHOW REPLICA STATUS\G

-- Kritični fieldovi:
-- Replica_IO_Running:     Yes  (IO thread čita master binlog)
-- Replica_SQL_Running:    Yes  (SQL thread primjenjuje promjene)
-- Seconds_Behind_Source:  0    (0=ok, >10=warning, >60=critical)
-- Last_IO_Error:          ""   (prazno = nema greške)
-- Last_SQL_Error:         ""   (prazno = nema greške)
-- Source_Host:            mysql-master
-- Executed_Gtid_Set:      (treba biti jednak masteru za punu sinkronizaciju)

-- Provjera GTID gap-a:
SELECT 
    @@GLOBAL.gtid_executed AS slave_gtid,
    (SELECT @@GLOBAL.gtid_executed FROM mysql_master) AS master_gtid;

-- Heartbeat tablica za precizno mjerenje laga (kreirati na masteru):
CREATE TABLE IF NOT EXISTS replication_heartbeat (
    server_id  INT         NOT NULL PRIMARY KEY,
    ts         TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Cron na masteru (svakih 5s):
INSERT INTO replication_heartbeat (server_id, ts) VALUES (1, NOW())
ON DUPLICATE KEY UPDATE ts = NOW();

-- Mjerenje laga na slaveu:
SELECT TIMESTAMPDIFF(SECOND, ts, NOW()) AS lag_seconds
FROM replication_heartbeat
WHERE server_id = 1;
```

### Prometheus mysql-exporter konfiguracija

```yaml
# docker-compose.override.yml — dodati u services sekciju
  mysql-exporter-slave:
    image: prom/mysqld-exporter:v0.15.0
    container_name: mysql-exporter-slave
    environment:
      DATA_SOURCE_NAME: "exporter:${MYSQL_EXPORTER_PASSWORD}@(mysql-slave:3306)/"
    command:
      - --collect.slave_status          # Replica_IO_Running, Seconds_Behind_Source, itd.
      - --collect.heartbeat             # Precizni lag iz heartbeat tablice
      - --collect.info_schema.processlist
      - --collect.engine_innodb_status
    ports:
      - "9105:9104"
    networks:
      - app-network
    profiles: [monitoring]
    depends_on:
      mysql-slave:
        condition: service_healthy

  mysql-exporter-master:
    image: prom/mysqld-exporter:v0.15.0
    container_name: mysql-exporter-master
    environment:
      DATA_SOURCE_NAME: "exporter:${MYSQL_EXPORTER_PASSWORD}@(mysql-master:3306)/"
    command:
      - --collect.binlog_size           # Binlog rast (indicira write load)
      - --collect.info_schema.processlist
      - --collect.engine_innodb_status
    ports:
      - "9104:9104"
    networks:
      - app-network
    profiles: [monitoring]
```

### Ključne Prometheus metrike

```
# Replikacijski lag (kritična metrika):
mysql_slave_status_seconds_behind_master
  Alert: > 10 = warning, > 60 = critical

# IO i SQL thread status (1=running, 0=stopped):
mysql_slave_status_slave_io_running
mysql_slave_status_slave_sql_running
  Alert: == 0 = critical (replikacija stala)

# Binlog veličina na masteru (write load indikator):
mysql_binlog_size_bytes

# Connection pool iskorištenost (Go aplikacija):
go_sql_open_connections
go_sql_idle_connections
go_sql_wait_duration_seconds
```

### Grafana alert pravila

```yaml
# alerts/mysql-replication.yml
groups:
  - name: mysql_replication
    rules:
      - alert: MySQLReplicationStopped
        expr: mysql_slave_status_slave_io_running == 0 OR mysql_slave_status_slave_sql_running == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "MySQL replication stopped on {{ $labels.instance }}"
          description: "IO or SQL thread is not running. Check SHOW REPLICA STATUS."

      - alert: MySQLReplicationLagHigh
        expr: mysql_slave_status_seconds_behind_master > 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "MySQL replication lag > 30s"
          description: "Current lag: {{ $value }}s. Reads from replica may return stale data."

      - alert: MySQLReplicationLagCritical
        expr: mysql_slave_status_seconds_behind_master > 120
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "MySQL replication lag > 2 minutes"
          description: "Application should switch all reads to master immediately."
```

---

## 6. Produkcija — AWS RDS vs lokalni Docker

| Aspekt | Lokalni Docker | AWS RDS |
|--------|---------------|---------|
| Setup | docker-compose + init script | Terraform `aws_db_instance` |
| Master endpoint | `mysql-master:3306` | `project-a.xxxxx.eu-west-1.rds.amazonaws.com:3306` |
| Replica endpoint | `mysql-slave:3306` | `project-a-ro.xxxxx.eu-west-1.rds.amazonaws.com:3306` |
| Failover | Ručni (za učenje i dev) | Automatski Multi-AZ (< 60s) |
| Replication lag | < 1ms (isti Docker network) | 0–10ms tipično, do 100ms pod opterećenjem |
| Backup | `mysqldump` skripte | Automatski snapshots, point-in-time recovery |
| Certificates | Nije potrebno | SSL/TLS obvezno (`tls=custom` u DSN) |
| Monitoring | Prometheus + Grafana lokalno | CloudWatch + RDS Performance Insights |
| Skaliranje | Ručno (novi container) | Read replica dodana jednom Terraform linijom |

### Go DSN primjeri

```go
// internal/config/config.go
package config

import "os"

type DatabaseConfig struct {
    MasterDSN  string
    ReplicaDSN string
}

func LoadDatabaseConfig() DatabaseConfig {
    // Dev: environment varijable iz .env fajla
    // Prod: environment varijable iz AWS Secrets Manager ili SSM Parameter Store
    return DatabaseConfig{
        MasterDSN:  buildDSN(
            os.Getenv("DB_MASTER_HOST"),
            os.Getenv("DB_PORT"),
            os.Getenv("DB_USER"),
            os.Getenv("DB_PASSWORD"),
            os.Getenv("DB_NAME"),
        ),
        ReplicaDSN: buildDSN(
            os.Getenv("DB_REPLICA_HOST"),
            os.Getenv("DB_PORT"),
            os.Getenv("DB_USER"),
            os.Getenv("DB_PASSWORD"),
            os.Getenv("DB_NAME"),
        ),
    }
}

func buildDSN(host, port, user, password, dbname string) string {
    // parseTime=true: automatski parse MySQL DATETIME u time.Time
    // loc=UTC: sve timezone vrijednosti kao UTC
    // timeout=5s: konekcijski timeout
    // readTimeout=30s: read timeout per query
    // writeTimeout=30s: write timeout per query
    return fmt.Sprintf(
        "%s:%s@tcp(%s:%s)/%s?parseTime=true&loc=UTC&timeout=5s&readTimeout=30s&writeTimeout=30s",
        user, password, host, port, dbname,
    )
}
```

### .env fajl (dev)

```bash
# .env — nikad ne commituj u git!
MYSQL_ROOT_PASSWORD=dev_root_pass_change_in_prod
MYSQL_APP_PASSWORD=dev_app_pass_change_in_prod
MYSQL_REPLICATION_PASSWORD=dev_repl_pass_change_in_prod
MYSQL_EXPORTER_PASSWORD=dev_exporter_pass

# Go aplikacija koristi ove varijable:
DB_MASTER_HOST=mysql-master
DB_REPLICA_HOST=mysql-slave
DB_PORT=3306
DB_USER=app
DB_PASSWORD=dev_app_pass_change_in_prod
DB_NAME=project_a
```

---

## 7. Česti problemi i rješenja

### Slave ne starta replikaciju

```bash
# Greška: "Got fatal error 1236 from master when reading data from binary log"
# Uzrok: binlog pozicija na masteru je resetovana (restart bez GTID, ili purge)

# Rješenje: reset slave i reinicijalizacija
docker exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL
    STOP REPLICA;
    RESET REPLICA ALL;
    RESET MASTER;
EOSQL

# Pa ponovo pokreni init-slave.sh proceduru
```
> **Podman:** `podman exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL ...`

### super_read_only blokira write

```bash
# Greška: "ERROR 1290 (HY000): The MySQL server is running with the --super-read-only option"
# Uzrok: pokušaj direktnog write-a na slave (bug u aplikaciji ili pogrešan DSN)

# Dijagnoza — provjeri koji query pokušava pisati na slaveu:
docker exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" \
  -e "SHOW PROCESSLIST\G" | grep -v Sleep
```
> **Podman:** `podman exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" -e "SHOW PROCESSLIST\G" | grep -v Sleep`

### Replication lag raste

```bash
# Dijagnoza: provjeri što SQL thread izvršava
docker exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL
    SHOW REPLICA STATUS\G
    -- Gledaj: Exec_Master_Log_Pos vs Read_Master_Log_Pos gap
    -- Ako je gap veliki i raste = SQL thread ne može pratiti IO thread

    -- Provjeri aktivne procese:
    SHOW PROCESSLIST\G
EOSQL

# Česti uzroci:
# 1. Bulk write na masteru (batch INSERT) — normalno, privremeno
# 2. Nedostaje index na slaveu (rare, ali moguće ako slave ima drugačiju shemu)
# 3. Slave server nema dovoljno resursa (CPU/IOPS)
# 4. Lock contention na slaveu

# Rješenje za IOPS: omogući parallel replication (MySQL 8.0+)
# U slave.cnf:
# replica_parallel_workers = 4
# replica_parallel_type = LOGICAL_CLOCK
```
> **Podman:** `podman exec mysql-slave mysql -u root -p"${MYSQL_ROOT_PASSWORD}" <<-EOSQL ... EOSQL`

---

## Sažetak

| Komponenta | Lokacija | Svrha |
|-----------|---------|-------|
| `master.cnf` | `docker/mysql/master.cnf` | GTID + ROW binlog konfiguracija |
| `slave.cnf` | `docker/mysql/slave.cnf` | read-only + relay log konfiguracija |
| `init-slave.sh` | `docker/mysql/init-slave.sh` | Automatska inicijalizacija replikacije |
| `database.DB` | `internal/database/db.go` | Write/Read routing sa fallback logikom |
| `WithRecentWrite` | `internal/database/context.go` | "Read your own writes" context pattern |
| `UserRepository` | `internal/repository/` | Primjer pravilne upotrebe routing-a |
| `WriteAwareHandler` | `internal/middleware/` | HTTP middleware za automatski context |

Isti Go kod i iste environment varijable rade i lokalno i na AWS RDS — samo se `DB_MASTER_HOST` i `DB_REPLICA_HOST` varijable mijenjaju između okruženja.
