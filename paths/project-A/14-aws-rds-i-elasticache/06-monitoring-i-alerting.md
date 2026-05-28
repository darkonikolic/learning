# 06 — Monitoring i Alerting

## RDS CloudWatch Metrike

### Ključne metrike i njihovo značenje

| Metrika | Opis | Prag za alert |
|---|---|---|
| `CPUUtilization` | % CPU korištenosti | WARNING > 80% (5min sustained) |
| `FreeStorageSpace` | Slobodan storage u bajtima | CRITICAL < 10GB |
| `FreeableMemory` | Slobodan RAM u bajtima | WARNING < 512MB |
| `ReplicaLag` | Lag replike u sekundama | WARNING > 30s, CRITICAL > 120s |
| `DatabaseConnections` | Aktivne konekcije | WARNING > 80% max_connections |
| `ReadIOPS` / `WriteIOPS` | I/O operacije per sekundi | Baseline + 3σ |
| `ReadLatency` / `WriteLatency` | Latencija I/O u sekundama | WARNING > 20ms |
| `BurstBalance` | Preostali I/O krediti (gp2) | WARNING < 20% |
| `DiskQueueDepth` | Queue čekajućih I/O operacija | WARNING > 1 (sustained) |

**Napomena za gp3**: `BurstBalance` ne postoji za gp3 — gp3 ima konzistentne 3000 IOPS bez burst mehanizma. Ovo je još jedan razlog za prelazak na gp3.

### Izračun max_connections limita

Za alert na DatabaseConnections treba znati stvarni limit:

```bash
# Provjeri trenutni max_connections
aws rds describe-db-parameters \
  --db-parameter-group-name project-a-prod-mysql8 \
  --query "Parameters[?ParameterName=='max_connections'].ParameterValue"

# Ako koristiš {DBInstanceClassMemory*3/4} formulu:
# db.t3.small (2GB RAM):  ~150 connections
# db.t3.medium (4GB RAM): ~300 connections
# db.r6g.large (16GB RAM): ~1200 connections

# Provjeri trenutni broj konekcija
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=project-a-prod-mysql-master \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum
```

---

## Terraform: CloudWatch Alarms + SNS

### SNS Topic

```hcl
# terraform/modules/monitoring/main.tf

resource "aws_sns_topic" "rds_alerts" {
  name = "project-a-${var.env_name}-rds-alerts"
  tags = local.common_tags
}

resource "aws_sns_topic_subscription" "rds_alerts_email" {
  topic_arn = aws_sns_topic.rds_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
  # Potvrda subscription-a stiže na email — mora se ručno potvrditi jednom
}
```

### CloudWatch Alarms

```hcl
# ─── ReplicaLag ───────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "replica_lag_warning" {
  count = var.create_replica ? 1 : 0

  alarm_name          = "project-a-${var.env_name}-rds-replica-lag-warning"
  alarm_description   = "RDS replica lag exceeds 30 seconds"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3      # 3 uzastopne evaluacije
  metric_name         = "ReplicaLag"
  namespace           = "AWS/RDS"
  period              = 60     # sekundi
  statistic           = "Average"
  threshold           = 30     # sekundi
  treat_missing_data  = "notBreaching"
  # notBreaching: ako nema podataka (replica nedostupna), ne alarmiraj za lag
  # Postoje posebni alarmi za replica availability

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.replica[0].identifier
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  ok_actions    = [aws_sns_topic.rds_alerts.arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "replica_lag_critical" {
  count = var.create_replica ? 1 : 0

  alarm_name          = "project-a-${var.env_name}-rds-replica-lag-critical"
  alarm_description   = "RDS replica lag exceeds 120 seconds - consider routing reads to master"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ReplicaLag"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Average"
  threshold           = 120
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.replica[0].identifier
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  ok_actions    = [aws_sns_topic.rds_alerts.arn]

  tags = local.common_tags
}

# ─── FreeStorageSpace ─────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "storage_space_critical" {
  alarm_name          = "project-a-${var.env_name}-rds-storage-critical"
  alarm_description   = "RDS free storage space below 10GB - immediate action required"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1      # Odmah alarmiraj, ne čekaj više perioda
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300    # 5 minuta
  statistic           = "Minimum"
  threshold           = 10737418240   # 10GB u bajtima (10 * 1024^3)
  treat_missing_data  = "breaching"
  # breaching: ako nema podataka za storage, alarmiraj (može znači instanca down)

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.master.identifier
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  ok_actions    = [aws_sns_topic.rds_alerts.arn]

  tags = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "storage_space_warning" {
  alarm_name          = "project-a-${var.env_name}-rds-storage-warning"
  alarm_description   = "RDS free storage space below 20GB"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Minimum"
  threshold           = 21474836480   # 20GB u bajtima
  treat_missing_data  = "breaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.master.identifier
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]

  tags = local.common_tags
}

# ─── DatabaseConnections ──────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "db_connections_warning" {
  alarm_name          = "project-a-${var.env_name}-rds-connections-warning"
  alarm_description   = "RDS connections exceed 80% of max_connections (160/200)"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 60
  statistic           = "Maximum"
  threshold           = 160    # 80% od 200 max_connections
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.master.identifier
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  ok_actions    = [aws_sns_topic.rds_alerts.arn]

  tags = local.common_tags
}

# ─── CPU ──────────────────────────────────────────────────────────────────────
resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "project-a-${var.env_name}-rds-cpu-high"
  alarm_description   = "RDS CPU sustained above 80% for 15 minutes"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3      # 3 × 5min = 15min sustained
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.master.identifier
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  ok_actions    = [aws_sns_topic.rds_alerts.arn]

  tags = local.common_tags
}
```

---

## Slow Query Log

### Konfiguracija u Parameter Group

```hcl
# Ovo je već u Parameter Group iz modula, ali pojašnjenje:
parameter {
  name  = "slow_query_log"
  value = "1"
}

parameter {
  name  = "long_query_time"
  value = "1"
  # Log query-je koji traju duže od 1 sekunde
  # Za performance investigation: spusti na 0.5 ili 0.25 privremeno
}

parameter {
  name  = "log_queries_not_using_indexes"
  value = "1"
  # Loguj query-je koji ne koriste indeks, čak i ako su brži od long_query_time
  # Može generisati PUNO logova — uključi samo privremeno za audit
}
```

### Čitanje Slow Query Logova

```bash
# CloudWatch Log Group se kreira automatski
# Format: /aws/rds/instance/{db-identifier}/slowquery

# Pretraži slow queries u zadnjem satu
aws logs filter-log-events \
  --log-group-name "/aws/rds/instance/project-a-prod-mysql-master/slowquery" \
  --start-time $(date -d '1 hour ago' +%s000) \
  --filter-pattern "Query_time"

# Insights query za top 10 najsporijih query-ja
aws logs start-query \
  --log-group-name "/aws/rds/instance/project-a-prod-mysql-master/slowquery" \
  --start-time $(date -d '24 hours ago' +%s) \
  --end-time $(date +%s) \
  --query-string '
    fields @timestamp, @message
    | parse @message "Query_time: * Lock_time: * Rows_sent: * Rows_examined: *" as query_time, lock_time, rows_sent, rows_examined
    | stats avg(query_time) as avg_time, max(query_time) as max_time, count() as count by bin(5m)
    | sort max_time desc
    | limit 20
  '
```

---

## ElastiCache Metrike

### Ključne metrike

| Metrika | Opis | Prag |
|---|---|---|
| `CurrConnections` | Aktivne konekcije | WARNING > 1000 |
| `CacheHitRate` | % cache hits | WARNING < 80% |
| `Evictions` | Izbačeni ključevi (maxmemory policy) | WARNING > 1000/min |
| `FreeableMemory` | Slobodan RAM u bajtima | WARNING < 50MB |
| `NetworkBytesIn/Out` | Network throughput | Baseline monitoring |
| `ReplicationLag` | Lag replike u sekundama | WARNING > 10s |
| `EngineCPUUtilization` | CPU samo Redis engine thread-a | WARNING > 80% |

**Zašto `EngineCPUUtilization` a ne `CPUUtilization`?**

Redis 7 je single-threaded za command processing ali ima I/O helper threads. `CPUUtilization` mjeri sve thread-ove. `EngineCPUUtilization` mjeri samo command processing thread — relevantnija za Redis capacity planning.

### CloudWatch Alarms za ElastiCache

```hcl
resource "aws_cloudwatch_metric_alarm" "redis_cache_hit_rate" {
  alarm_name          = "project-a-${var.env_name}-redis-cache-hit-rate"
  alarm_description   = "Redis cache hit rate below 80%"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CacheHitRate"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Average"
  threshold           = 80
  treat_missing_data  = "notBreaching"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  tags          = local.common_tags
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "project-a-${var.env_name}-redis-evictions"
  alarm_description   = "Redis evictions rate is high - consider increasing memory"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = 300
  statistic           = "Sum"
  threshold           = 5000   # 5000 evictions u 5 minuta
  treat_missing_data  = "notBreaching"

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.redis.id
  }

  alarm_actions = [aws_sns_topic.rds_alerts.arn]
  tags          = local.common_tags
}
```

---

## Prometheus-Based Monitoring Alternativa

Za timove koji već koriste Prometheus/Grafana stack (npr. kube-prometheus-stack), AWS CloudWatch alarms su redundantni. Bolji pristup: exporteri unutar K8s clustera.

### mysql_exporter kao Sidecar

```yaml
# k8s/base/go-service/deployment.yaml (dopunjeno)
spec:
  template:
    spec:
      containers:
        - name: go-service
          # ... (kao ranije)

        - name: mysql-exporter
          image: prom/mysqld-exporter:v0.15.0
          ports:
            - containerPort: 9104
              name: metrics
          env:
            - name: DATA_SOURCE_NAME
              valueFrom:
                secretKeyRef:
                  name: rds-credentials
                  key: MYSQL_EXPORTER_DSN
                  # Format: user:pass@tcp(endpoint:3306)/
          args:
            - "--collect.global_status"
            - "--collect.global_variables"
            - "--collect.slave_status"          # Replica lag
            - "--collect.info_schema.innodb_metrics"
            - "--collect.perf_schema.eventswaits"
          resources:
            requests:
              cpu: "10m"
              memory: "32Mi"
            limits:
              cpu: "100m"
              memory: "64Mi"
```

```yaml
# k8s/base/monitoring/servicemonitor-mysql.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: mysql-exporter
  namespace: project-a
spec:
  selector:
    matchLabels:
      app: go-service
  endpoints:
    - port: metrics
      path: /metrics
      interval: 30s
```

### Korisne Prometheus Metrike za RDS

```promql
# Replica lag
mysql_slave_status_seconds_behind_master{instance=~".*go-service.*"}

# Connection pool utilization (iz Go service)
go_sql_open_connections{db="master"} / go_sql_max_open_connections{db="master"} * 100

# Slow queries rate
rate(mysql_global_status_slow_queries[5m])

# InnoDB buffer pool hit rate
(
  rate(mysql_global_status_innodb_buffer_pool_reads[5m]) /
  rate(mysql_global_status_innodb_buffer_pool_read_requests[5m])
) * 100
# Trebalo bi biti > 99% za dobro konfigurisan innodb_buffer_pool_size
```

### redis_exporter

```yaml
# k8s/base/php-service/deployment.yaml (sidecar)
- name: redis-exporter
  image: oliver006/redis_exporter:v1.56.0
  ports:
    - containerPort: 9121
      name: redis-metrics
  env:
    - name: REDIS_ADDR
      value: "rediss://$(REDIS_HOST):6379"   # rediss:// za TLS
    - name: REDIS_PASSWORD
      valueFrom:
        secretKeyRef:
          name: redis-credentials
          key: REDIS_AUTH_TOKEN
  resources:
    requests:
      cpu: "10m"
      memory: "16Mi"
```

### Dashboard preporuka

Umjesto pisanja custom Grafana dashboarda, koristi gotove:
- **MySQL Overview**: Grafana Dashboard ID `7362` (mysql_exporter)
- **Redis Overview**: Grafana Dashboard ID `763` (redis_exporter)
- **RDS/ElastiCache CloudWatch**: AWS ima managed dashboarde u CloudWatch konzoli

---

## Troubleshooting Runbook

### Visok ReplicaLag (> 30s)

```bash
# 1. Provjeri slave status na replici
mysql -h $REPLICA_ENDPOINT -u admin -p -e "SHOW SLAVE STATUS\G" | grep -E "Seconds_Behind|Running|Error"

# 2. Provjeri ima li long-running queries na masteru koji blokiraju repliku
mysql -h $MASTER_ENDPOINT -u admin -p -e "SHOW PROCESSLIST" | grep -v Sleep

# 3. Provjeri instance metrics — je li replica CPU/IO saturiran?
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name CPUUtilization \
  --dimensions Name=DBInstanceIdentifier,Value=project-a-prod-mysql-replica \
  --start-time $(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average

# 4. Ako je lag prihvatljiv i nema grešaka, možda je samo heavy write burst
# Monitoruj trend — treba da se vrati na 0
```

### DatabaseConnections blizu limita

```bash
# Provjeri odakle dolaze konekcije
mysql -h $MASTER_ENDPOINT -u admin -p -e "
SELECT user, host, COUNT(*) as count, command
FROM information_schema.processlist
GROUP BY user, host, command
ORDER BY count DESC;"

# Ako Go service drži previše konekcija, provjeri pool config
# Ako ima mnogo Sleep konekcija s kratkim vremenom, možda je connection leak
mysql -e "SELECT * FROM information_schema.processlist WHERE COMMAND = 'Sleep' AND TIME > 60;"
```
