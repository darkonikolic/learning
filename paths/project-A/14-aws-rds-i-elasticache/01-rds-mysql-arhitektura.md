# 01 — RDS MySQL 8.0: Arhitektura i Produkcijski Odluke

## Managed vs Self-Managed MySQL

### Šta RDS rješava

RDS preuzima operativne zadatke koji u self-managed scenariju troše sate:

| Zadatak | Self-managed | RDS |
|---|---|---|
| OS patching | Manualno, downtime | Maintenance window, Multi-AZ bez downtime |
| Binlog/backup | Konfiguriraj sam | Automatski, PITR uključen |
| Failover | Build HA stack (MHA, Orchestrator) | Multi-AZ, automatski ~60s |
| Storage scaling | Resize + migracija | Storage autoscaling bez downtime |
| Minor verzije | Manualni upgrade + test | Automatski u maintenance window |

### Šta RDS ODUZIMA

Ovo su produkcijska ograničenja koja treba unaprijed znati:

**Nema OS pristupa** — ne možeš instalirati percona-toolkit direktno na server, ne možeš koristiti `pt-online-schema-change` s lokalnim socketom. Rješenje: pokreni alat s EKS Job-a koji se spoji na RDS endpoint.

**Parameter Group ograničenja** — određeni parametri su `static` (zahtijevaju reboot) ili su zaključani. Primjer: ne možeš mijenjati `innodb_log_file_size` na running instanci bez reboot-a. Na Aurora-i ovog problema nema jer je storage layer drugačiji.

**Superuser nije dostupan** — RDS admin user nema `SUPER` privilege u punom smislu. Za određene operacije (npr. `CHANGE MASTER TO` ručno) nisi ovlašten. AWS pruža stored procedure kao zamjenu (`mysql.rds_set_external_master`).

**Slow query log via CloudWatch** — ne čitaš direktno `/var/log/mysql/slow.log`, export ide u CloudWatch Logs što uvodi latenciju u pojavljivanju logova (~1 min).

---

## Multi-AZ vs Read Replica

Ovo je najčešće pogrešno shvaćena distinkcija u AWS produkcijskim setupima.

### Multi-AZ: Visoka dostupnost (HA), ne skaliranje

```
┌─────────────────────────────────────────────────────┐
│                   AWS Region                         │
│                                                      │
│   AZ-a                        AZ-b                  │
│  ┌─────────────────┐         ┌─────────────────┐    │
│  │  RDS Master     │────────▶│  RDS Standby    │    │
│  │  (active)       │ sync    │  (passive)      │    │
│  │                 │ repl    │                 │    │
│  └─────────────────┘         └─────────────────┘    │
│          │                                           │
│    DNS endpoint (master.cluster.rds.amazonaws.com)  │
│    (failover: DNS switch, ~60s)                     │
└─────────────────────────────────────────────────────┘
```

- **Standby ne prima read traffic** — aplikacija se NIKAD ne spaja direktno na standby
- **Replication je synchronous** — Amazon koristi internu mehaniku (ne standardni MySQL binlog) za garantovanu durabilnost
- **Failover trigger**: instance failure, AZ failure, OS maintenance, manual reboot with failover
- **Cijena**: 2x storage, 2x instance — ali je obavezno za prod

### Read Replica: Horizontalno skaliranje čitanja

```
┌──────────────┐     async binlog     ┌──────────────────┐
│  RDS Master  │ ──────────────────▶  │  Read Replica    │
│  (write+read)│                      │  (read-only)     │
└──────────────┘                      └──────────────────┘
       │                                      │
  master endpoint                      replica endpoint
  (writes)                             (reads)
```

- **Async replication** — postoji replication lag (millisekunde do sekunde u normalnom radu)
- **Replica endpoint** je poseban DNS — aplikacija mora eksplicitno koristiti ga za read workload
- Replica se može **promovirati** u standalone instancu (disaster recovery, migracija)
- Cross-region replica je moguća (DR strategija)

### Produkcijski zaključak: Trebamo OBA

```
Master (Multi-AZ)     — writes + HA failover
  └── Replica          — read queries (reports, batch jobs)
  └── Standby (Multi-AZ hidden) — automatski failover
```

---

## Replication Lag: Uzroci, Mjerenje, Handling

### Kako nastaje lag

MySQL async replication koristi binlog. Flow:

```
Master: commit transaction → write binlog → ACK client
Replica: IO thread (fetch binlog) → SQL thread (apply events)
                                         ↑
                                   Ovde nastaje lag
```

**Uzroci laga:**

1. **Heavy write workload** na masteru — SQL thread ne stigne apply-ati
2. **Nedovoljno I/O na replici** — instance class je premal
3. **DDL operacije** — `ALTER TABLE` se fully replicira, blokira SQL thread
4. **Long-running transactions** — replica čeka dok se cijela transakcija ne commituje
5. **Network latency** između AZ-ova (Cross-region replica)

### Mjerenje

```sql
-- Na replici
SHOW SLAVE STATUS\G

-- Ključna polja:
-- Seconds_Behind_Master: sekunde laga (aproksimacija!)
-- Relay_Log_Space: ukupna veličina relay logova (raste = replica zaostaje)
-- Slave_IO_Running: Yes (mora biti)
-- Slave_SQL_Running: Yes (mora biti)
```

**Zašto `Seconds_Behind_Master` nije savršena metrika:**
- Mjeri razliku između timestamp eventa na masteru i trenutnog vremena na replici
- Ako master nema write aktivnosti, metrika pada na 0 čak i ako su prethodni eventi netom apply-ani
- Za precizniju metriku: CloudWatch `ReplicaLag` (AWS računa ga drugačije)

```sql
-- Preciznije: provjeri poziciju
SHOW MASTER STATUS;  -- na masteru: File + Position
SHOW SLAVE STATUS;   -- na replici: Relay_Master_Log_File + Exec_Master_Log_Pos
```

### Kako aplikacija treba handle-ovati stale reads

**Problem**: Nakon write-a, odmah čitaš s replike — možeš dobiti stale data.

**Strategija 1: Read-your-own-writes routing**
```go
// Go service zna koji endpoint koristiti po operaciji
func (db *Database) WriteUser(user User) error {
    return db.master.Exec("INSERT INTO users ...", user)
}

func (db *Database) GetUserForDisplay(id int) (User, error) {
    // Read-heavy, eventual consistency prihvatljiva
    return db.replica.QueryRow("SELECT * FROM users WHERE id = ?", id)
}

func (db *Database) GetUserAfterUpdate(id int) (User, error) {
    // Odmah nakon write-a — čitaj s mastera
    return db.master.QueryRow("SELECT * FROM users WHERE id = ?", id)
}
```

**Strategija 2: Lag threshold provjera**
```go
// Provjeri lag prije read-a (skupo, samo za kritične operacije)
func (db *Database) GetReplicaLag() (int, error) {
    var lag int
    row := db.replica.QueryRow("SELECT TIMESTAMPDIFF(SECOND, MAX(last_updated), NOW()) FROM replication_heartbeat")
    row.Scan(&lag)
    return lag, nil
}
```

**Strategija 3: Sticky session na master** za transakcije koje zahtijevaju konzistentnost.

---

## Go Service Connection Pattern

```go
// internal/database/connection.go
package database

import (
    "database/sql"
    "fmt"
    "time"
    _ "github.com/go-sql-driver/mysql"
)

type DB struct {
    Master  *sql.DB
    Replica *sql.DB
}

func NewDB(cfg Config) (*DB, error) {
    masterDSN := fmt.Sprintf(
        "%s:%s@tcp(%s:3306)/%s?parseTime=true&charset=utf8mb4&collation=utf8mb4_unicode_ci&timeout=5s&readTimeout=10s&writeTimeout=10s",
        cfg.Username, cfg.Password, cfg.MasterEndpoint, cfg.DBName,
    )

    replicaDSN := fmt.Sprintf(
        "%s:%s@tcp(%s:3306)/%s?parseTime=true&charset=utf8mb4&collation=utf8mb4_unicode_ci&timeout=5s&readTimeout=10s",
        cfg.Username, cfg.Password, cfg.ReplicaEndpoint, cfg.DBName,
    )

    master, err := sql.Open("mysql", masterDSN)
    if err != nil {
        return nil, fmt.Errorf("master connect: %w", err)
    }

    replica, err := sql.Open("mysql", replicaDSN)
    if err != nil {
        return nil, fmt.Errorf("replica connect: %w", err)
    }

    // Connection pool sizing: ne postavljaj PreMaxIdleConns > MaxOpenConns
    // Za db.t3.medium: max_connections = ~150 (ostavi buffer za admin sesije)
    for _, db := range []*sql.DB{master, replica} {
        db.SetMaxOpenConns(25)
        db.SetMaxIdleConns(10)
        db.SetConnMaxLifetime(5 * time.Minute)
        db.SetConnMaxIdleTime(2 * time.Minute)
    }

    return &DB{Master: master, Replica: replica}, nil
}
```

**Zašto `ConnMaxLifetime`?** RDS ima idle connection timeout na load balancer nivou (~8 sata). Bez `ConnMaxLifetime`, pool drži "mrtve" konekcije koje će failovati na prvom query-u.

**Multi-AZ failover pattern:**
```go
func (db *DB) QueryWithFallback(query string, args ...interface{}) (*sql.Rows, error) {
    rows, err := db.Replica.QueryContext(ctx, query, args...)
    if err != nil {
        // Replica nedostupna — fallback na master
        log.Warn("replica unavailable, falling back to master", "err", err)
        return db.Master.QueryContext(ctx, query, args...)
    }
    return rows, nil
}
```

---

## RDS Proxy: Kada Koristiti (i Kada NE)

### Šta RDS Proxy rješava

RDS Proxy stoji ispred RDS instance i multiplexira konekcije:

```
Mnogo kratkih konekcija (Lambda)    ──▶   RDS Proxy   ──▶  RDS (mali pool)
  conn1 connect/disconnect                 (pool 10)
  conn2 connect/disconnect
  conn3 connect/disconnect
```

**Idealan use case**: AWS Lambda — svaka invokacija otvara novu konekciju, bez Proxy-a brzo dostigneš `max_connections` limit.

### Za naš K8s setup: NE koristiti RDS Proxy

**Razlozi:**

1. **K8s pod pool je stabilan** — Go service pod ima `database/sql` connection pool koji perzistira za cijeli životni vijek Pod-a. Konekcije se ne otvaraju/zatvaraju per-request.

2. **Overhead bez benefita** — Proxy uvodi ~1ms latenciju per query. Za 1000 QPS = 1 sekunda extra latencije agregatno.

3. **Cijena** — RDS Proxy košta extra (~$0.015/hour za db.t3.medium = +$11/mj).

4. **Kompleksnost** — Još jedan AWS servis koji može failovati. Debugging postaje teži.

5. **Proxy ne riješava Multi-AZ failover bolje** — DNS propagacija je isti bottleneck.

**Kada bi imalo smisla**: Ako dodamo Lambda funkcije u arhitekturu (webhooks, event processing), tada Proxy za Lambda connections.

---

## Parameter Group: Ključni Parametri za Produkciju

### Kreiranje custom Parameter Group

**Nikad ne koristi default.mysql8.0** — ne možeš ga modificirati. Uvijek kreiraj custom.

```hcl
resource "aws_db_parameter_group" "mysql8" {
  family = "mysql8.0"
  name   = "project-a-mysql8-${var.env_name}"

  parameter {
    name  = "innodb_buffer_pool_size"
    value = "{DBInstanceClassMemory*3/4}"  # 75% RAM-a
  }

  parameter {
    name  = "max_connections"
    value = "200"
    # db.t3.medium ima 4GB RAM → default formula daje ~150
    # Postavi eksplicitno, ali pazi: previše konekcija = OOM
  }

  parameter {
    name  = "slow_query_log"
    value = "1"
  }

  parameter {
    name  = "long_query_time"
    value = "1"  # log sve query-je sporije od 1 sekunde
  }

  parameter {
    name  = "log_output"
    value = "FILE"  # FILE = CloudWatch Logs export, TABLE = mysql.slow_log tabela
  }

  parameter {
    name         = "innodb_flush_log_at_trx_commit"
    value        = "1"
    # 1 = ACID compliant (default, produkcija)
    # 2 = flush svake sekunde (brže, rizik od 1s gubitka podataka pri crash-u)
  }

  parameter {
    name  = "character_set_server"
    value = "utf8mb4"
  }

  parameter {
    name  = "collation_server"
    value = "utf8mb4_unicode_ci"
  }

  parameter {
    name  = "time_zone"
    value = "UTC"  # Uvijek UTC u bazi, timezone conversion u aplikaciji
  }
}
```

### Parametri koji zahtijevaju reboot (static)

| Parametar | Apply type | Napomena |
|---|---|---|
| `innodb_buffer_pool_size` | dynamic | Može se mijenjati bez reboot-a od MySQL 5.7.5 |
| `max_connections` | dynamic | Primjenjuje se odmah |
| `innodb_log_file_size` | static | **Reboot obavezan** — planiraj maintenance window |
| `character_set_server` | dynamic | Ali postoje sesijski overrides |

**Expert gotcha**: Kada mijenjaš Parameter Group na running instanci, `apply_method = "pending-reboot"` parametri se ne primjenjuju dok ne restartuješ. Terraform neće automatski restartovati RDS — moraš ručno ili kroz maintenance window.
