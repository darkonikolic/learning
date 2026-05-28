# 06 — ALB Monitoring i Troubleshooting

## ALB Access Logs

Access logs daju kompletnu sliku svakog requesta koji prođe kroz ALB. Neophodne za debugging i sigurnosnu analizu.

### Aktivacija

```
EC2 → Load Balancers → project-a-prod-alb
→ Attributes tab → Edit
→ Access logs: Enable
→ S3 bucket: project-a-alb-logs
→ Prefix: prod (preporuča se odvojiti prod/dev logove)
→ Save changes
```

S3 bucket mora biti u istoj regiji kao ALB. ALB kreira putanju:
```
s3://project-a-alb-logs/prod/AWSLogs/123456789/elasticloadbalancing/eu-west-1/2024/01/15/
```

**S3 bucket policy** (ALB treba permisiju da piše u bucket):
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "AWS": "arn:aws:iam::156460612806:root"
    },
    "Action": "s3:PutObject",
    "Resource": "arn:aws:s3:::project-a-alb-logs/prod/AWSLogs/123456789/*"
  }]
}
```

`156460612806` je AWS account ID za ELB servis u eu-west-1. Svaka regija ima drugačiji account ID — provjeri u AWS dokumentaciji.

### Format Access Loga

```
type timestamp elb client:port target:port request_processing_time target_processing_time response_processing_time elb_status_code target_status_code received_bytes sent_bytes "request" "user_agent" ssl_cipher ssl_protocol target_group_arn "trace_id" "domain_name" "chosen_cert_arn" matched_rule_priority request_creation_time "actions_executed" "redirect_url" "error_reason" "target:port_list" "target_status_code_list" classification classification_reason conn_trace_id

# Realni primjer:
https 2024-01-15T10:30:00.123456Z app/project-a-prod-alb/abc123 1.2.3.4:54321 10.0.3.50:9000 0.001 0.002 0.000 200 200 512 2048 "POST /api/v2/orders HTTP/1.1" "Mozilla/5.0 ..." ECDHE-RSA-AES128-GCM-SHA256 TLSv1.2 arn:aws:elasticloadbalancing:...:targetgroup/php-tg/xyz "Root=1-abc-def" "app.firma.com" "arn:aws:acm:...:certificate/cert123" 1 2024-01-15T10:30:00.120000Z "forward" "-" "-" "10.0.3.50:9000" "200" "-" "-" "-"
```

**Analiza logova:**

```bash
# Preuzmi log fajl
aws s3 cp s3://project-a-alb-logs/prod/AWSLogs/123456789/elasticloadbalancing/eu-west-1/2024/01/15/file.log.gz .
gunzip file.log.gz

# Top 10 najsporijih requestova (target_processing_time = kolona 6)
awk '{print $6, $12, $13}' file.log | sort -rn | head -10

# Svi 5XX od backenda (kolona 9 = target_status_code)
awk '$9 ~ /^5/' file.log | wc -l

# Requestovi po IP adresi (kolona 4, uzmi samo IP bez porta)
awk '{print $4}' file.log | cut -d: -f1 | sort | uniq -c | sort -rn | head -20

# Prosječno response time po endpoint-u
awk '{print $13, $6}' file.log | awk '{sum[$1]+=$2; count[$1]++} END {for(k in sum) print k, sum[k]/count[k]}' | sort -k2 -rn | head -20

# Athena query (za produkcijsku analizu velikih logova)
# Kreira se tabela u Athena koja čita direktno iz S3
```

**AWS Athena za ALB logove (production standard):**

```sql
-- Kreiraj tabelu (jednom)
CREATE EXTERNAL TABLE alb_logs (
  type string, time string, elb string,
  client_ip string, client_port int,
  target_ip string, target_port int,
  request_processing_time double, target_processing_time double,
  response_processing_time double,
  elb_status_code int, target_status_code int,
  received_bytes bigint, sent_bytes bigint,
  request string, user_agent string,
  ssl_cipher string, ssl_protocol string,
  target_group_arn string
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.RegexSerDe'
WITH SERDEPROPERTIES ("input.regex" = '([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*):([0-9]*) ([^ ]*)[:-]([0-9]*) ([-.0-9]*) ([-.0-9]*) ([-.0-9]*) (|[-0-9]*) (-|[-0-9]*) ([-0-9]*) ([-0-9]*) \"([^ ]*) ([^ ]*) (- |[^ ]*)\" \"([^\"]*)\" ([A-Z0-9-_]+) ([A-Za-z0-9.-]*) ([^ ]*)')
LOCATION 's3://project-a-alb-logs/prod/AWSLogs/123456789/elasticloadbalancing/eu-west-1/';

-- Upiti
SELECT target_ip, COUNT(*) as requests, AVG(target_processing_time) as avg_time
FROM alb_logs
WHERE time > '2024-01-15T10:00:00Z'
  AND elb_status_code >= 500
GROUP BY target_ip
ORDER BY requests DESC;
```

---

## CloudWatch Metrike

### Ključne metrike i šta znače

| Metrika | Namespace | Šta mjeri | Alarm prag |
|---|---|---|---|
| `RequestCount` | AWS/ApplicationELB | Ukupan broj requestova | info metrika |
| `TargetResponseTime` | AWS/ApplicationELB | Latencija backend-a (p50, p95, p99) | p99 > 2s = upozorenje |
| `HTTPCode_Target_5XX_Count` | AWS/ApplicationELB | 5XX greške od targeta (backend problem) | > 5 u 1 min = alarm |
| `HTTPCode_ELB_5XX_Count` | AWS/ApplicationELB | 5XX greške od ALB-a (nema healthy targeta, timeout) | > 0 = kritično |
| `HTTPCode_ELB_4XX_Count` | AWS/ApplicationELB | 4XX od ALB-a (loš request format) | spike = istraga |
| `HealthyHostCount` | AWS/ApplicationELB | Broj zdravih targeta u TG | < 1 = katastrofa |
| `UnHealthyHostCount` | AWS/ApplicationELB | Broj nezdravih targeta | > 0 = upozorenje |
| `ActiveConnectionCount` | AWS/ApplicationELB | Aktivne konekcije | neobičan spike |
| `NewConnectionCount` | AWS/ApplicationELB | Nove konekcije/s | za capacity planning |
| `ProcessedBytes` | AWS/ApplicationELB | Saobraćaj u bajtima | za troškove i anomalije |

### Postavljanje Alarmova

```bash
# KRITIČNI alarm: 0 zdravih targeta = total outage
aws cloudwatch put-metric-alarm \
  --alarm-name "alb-prod-no-healthy-targets" \
  --alarm-description "ALB prod: nema zdravih targeta - TOTAL OUTAGE" \
  --metric-name HealthyHostCount \
  --namespace AWS/ApplicationELB \
  --statistic Minimum \
  --period 60 \
  --threshold 1 \
  --comparison-operator LessThanThreshold \
  --dimensions \
    Name=LoadBalancer,Value=app/project-a-prod-alb/abc123 \
    Name=TargetGroup,Value=targetgroup/php-tg/xyz \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:eu-west-1:123:pagerduty-critical \
  --treat-missing-data breaching

# UPOZORENJE: visoka latencija
aws cloudwatch put-metric-alarm \
  --alarm-name "alb-prod-high-latency" \
  --metric-name TargetResponseTime \
  --namespace AWS/ApplicationELB \
  --extended-statistic p99 \
  --period 300 \
  --threshold 2.0 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=LoadBalancer,Value=app/project-a-prod-alb/abc123 \
  --evaluation-periods 3 \
  --alarm-actions arn:aws:sns:eu-west-1:123:slack-alerts

# 5XX alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "alb-prod-5xx-errors" \
  --metric-name HTTPCode_Target_5XX_Count \
  --namespace AWS/ApplicationELB \
  --statistic Sum \
  --period 60 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=LoadBalancer,Value=app/project-a-prod-alb/abc123 \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:eu-west-1:123:slack-alerts
```

---

## Česti Problemi i Dijagnoza

### 502 Bad Gateway

**Znači:** ALB je proslijedio request na target, ali target nije vratio validan HTTP response ili je zatvorio konekciju.

```bash
# Koraci dijagnoze:
# 1. Provjeri health status targeta
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:eu-west-1:123:targetgroup/php-tg/xyz

# 2. Provjeri pod logs
kubectl logs -n project-a-prod -l app=php-service --tail=50

# 3. Test direktno na pod (zaobiđi ALB)
kubectl exec -n project-a-prod deployment/php-service -- \
  curl -s localhost:9000/health

# 4. Provjeri memory/CPU limite
kubectl top pods -n project-a-prod
kubectl describe pod <pod-name> -n project-a-prod | grep -A 5 "Limits\|Requests"
```

**Uzroci 502:**
- Pod crashuje (OOM Killer, unhandled exception) — provjeri pod events i logs
- PHP-FPM timeout (dugi SQL query) — gledaj target_processing_time u ALB logovima
- Pod ima memory limit prekoračen — `kubectl describe pod` → OOMKilled events
- Upstream timeout (PHP čeka Go servis predugo) — provjeri inter-service latenciju

### 504 Gateway Timeout

**Znači:** ALB čekao odgovor od targeta duže od ALB idle timeout (default 60s).

```bash
# ALB timeout konfiguracija:
aws elbv2 modify-load-balancer-attributes \
  --load-balancer-arn arn:aws:elasticloadbalancing:... \
  --attributes Key=idle_timeout.timeout_seconds,Value=120

# Via Ingress annotation:
# alb.ingress.kubernetes.io/load-balancer-attributes: idle_timeout.timeout_seconds=120
```

**Uzroci 504:**
- Spori database query (N+1 problem, missing index) — provjeri MySQL slow query log
- External API call bez timeout-a — PHP/Go mora imati timeout na svim external callovima
- File upload bez streaming — large payload uzrokuje timeout

**ALB timeout vs application timeout:** ALB čeka 60s (default). Tvoja aplikacija mora obaviti operaciju unutar tog vremena ILI streami response. Za long-running operacije (batch processing), prebaci na async pattern: request → queue job → vrati job ID → klijent polluje status.

### 503 Service Unavailable

**Znači:** ALB nema nijednog healthy targeta kojima može proslijediti request.

```bash
# Immediate triage:
kubectl get pods -n project-a-prod
# Jesu li podovi Running?

kubectl get endpoints php-service -n project-a-prod
# Ima li endpoints? Prazna lista = nema ready podova

kubectl describe deployment php-service -n project-a-prod
# Provjeri ReplicaSet events

# ALB target health:
aws elbv2 describe-target-health \
  --target-group-arn arn:aws:elasticloadbalancing:...
# Reason: Unhealthy → pogledaj HealthCheckReason

# Provjeri ALB Controller logove (možda postoji Ingress greška)
kubectl logs -n kube-system deployment/aws-load-balancer-controller --tail=30
```

**Uzroci 503:**
- Svi podovi crashuju pri startu (bad deployment) → `kubectl rollout undo`
- Imagepull greška → `kubectl describe pod` → Events
- Greška pri migraciji baze → nova verzija ne može se spojiti, health check faila
- Scaling down na 0 replika (za dev env overnight savings) → scale up

### Connection Refused / Security Group Problemi

```bash
# Provjeri security group rules
aws ec2 describe-security-groups \
  --group-ids sg-worker-node-sg \
  --query 'SecurityGroups[*].IpPermissions'

# Treba vidjeti inbound rule koja dozvoljava ALB SG:
# FromPort: 9000 (ili koji port koristiš)
# IpRanges: [] (nema direct IP)
# UserIdGroupPairs: [{GroupId: sg-alb-project-a-prod}]

# Test konekcije iz K8s poda prema ALB IP-u (reverse test)
kubectl run nettest --image=nicolaka/netshoot -it --rm --restart=Never -- \
  nmap -p 443 project-a-prod-alb-123.eu-west-1.elb.amazonaws.com
```

### Tracing End-to-End Request

ALB dodaje `X-Amzn-Trace-Id` header na svaki request:

```
X-Amzn-Trace-Id: Root=1-5e1b0d5c-47dab0d02c5f3831e19d3b9d
```

```bash
# Pronađi request u ALB logu po trace ID
grep "Root=1-5e1b0d5c" /path/to/alb/access.log

# Isti trace ID treba biti u tvojim aplikacijskim logovima ako propagiraš header
# PHP: $_SERVER['HTTP_X_AMZN_TRACE_ID']
# Go: r.Header.Get("X-Amzn-Trace-Id")

# AWS X-Ray integracija: ALB automatski kreira X-Ray segment
# Možeš vidjeti cijeli request flow u X-Ray konzoli
```

---

## WAF Integracija

Za produkciju, WAF (Web Application Firewall) je ispred ALB-a i blokira napade prije nego dođu do aplikacije.

```bash
# Kreiraj WAF ACL
aws wafv2 create-web-acl \
  --name project-a-prod-waf \
  --scope REGIONAL \
  --region eu-west-1 \
  --default-action Allow={} \
  --visibility-config SampledRequestsEnabled=true,CloudWatchMetricsEnabled=true,MetricName=project-a-prod \
  --rules file://waf-rules.json

# Primjer WAF rules (waf-rules.json):
# - AWS managed rule: AWSManagedRulesCommonRuleSet (SQL injection, XSS, etc.)
# - AWS managed rule: AWSManagedRulesKnownBadInputsRuleSet
# - Rate limiting: 1000 req/5min per IP
# - Geo blocking: zatvori pristup iz rizičnih zemalja ako nije potrebno

# Attach WAF na ALB
aws wafv2 associate-web-acl \
  --web-acl-arn arn:aws:wafv2:eu-west-1:123:regional/webacl/project-a-prod-waf/xyz \
  --resource-arn arn:aws:elasticloadbalancing:eu-west-1:123:loadbalancer/app/project-a-prod-alb/abc

# Via Ingress annotation:
# alb.ingress.kubernetes.io/wafv2-acl-arn: arn:aws:wafv2:eu-west-1:123:regional/webacl/...
```

**WAF troškovi:** $5/mj po Web ACL + $1/mj per rule + $0.60 per 1M requestova. Za aplikaciju sa 10M req/mj, WAF kosta ~$15-20/mj. Vrijedi za produkciju.

**WAF u count mode pri uvođenju:** Uvijek prvo aktiviraj WAF rules u "Count" modu (loguje ali ne blokira), provjeri da li blokira legitimne requestove, tek onda prebaci na "Block". Preuranjeno blokiranje može uhvatiti i prave korisnike.

---

## Korisni Dashboard — CloudWatch

```
Preporučeni CloudWatch Dashboard za ALB monitoring:

Widget 1: RequestCount (1min) — vidjet ćeš normalne patterne i anomalije
Widget 2: TargetResponseTime p99 (1min) — latencija 99th percentile
Widget 3: HTTPCode_Target_5XX_Count i HTTPCode_ELB_5XX_Count zajedno
Widget 4: HealthyHostCount za svaki Target Group
Widget 5: ActiveConnectionCount — korisno za DDoS detection
Widget 6: ProcessedBytes — bandwidth trends
```

```bash
# Brzi pregled metrika iz CLI (zadnjih 5 minuta)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApplicationELB \
  --metric-name TargetResponseTime \
  --dimensions Name=LoadBalancer,Value=app/project-a-prod-alb/abc123 \
  --start-time $(date -u -v-5M +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 60 \
  --statistics Average p99 \
  --query 'sort_by(Datapoints, &Timestamp)[].[Timestamp,Average,ExtendedStatistics.p99]' \
  --output table
```
