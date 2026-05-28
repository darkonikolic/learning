# 07 — Incident Response: Kada Produkcija Pukne

## Mindset Prije Svega

Kad alerti zazvone, prve dvije minute su najvažnije. Greška broj 1: panika i slijepo klikanje/kucanje. Greška broj 2: solo heroj koji ništa ne komunicira.

**Protokol za prve 60 sekundi:**
1. Udahni. Jedna stvar u jednom trenutku.
2. Otvori Slack `#incidents` i napiši: *"Gledam alert: [opis]. Tražim uzrok."*
3. Tek onda počni triage.

Komunikacija je dio posla, ne ometanje od posla.

---

## Incident Triage: Prvih 5 Minuta

### Korak 1: Koji Pod-ovi Nisu Running?

```bash
# Brz pregled cijelog namespace-a
kubectl get pods -n project-a-prod

# Filtriraj samo problematične (nisu Running ili Completed)
kubectl get pods -n project-a-prod | grep -v -E 'Running|Completed'

# Watch mode (osvježava se automatski)
kubectl get pods -n project-a-prod -w
```

### Korak 2: Detalji Crashiranog Pod-a

```bash
# Events i status (najkorisniji command za triage)
kubectl describe pod <crashed-pod> -n project-a-prod

# Ključne sekcije u outputu:
# - "State: Waiting" + "Reason: CrashLoopBackOff" → app crashira odmah
# - "Last State: Terminated" + "Exit Code: 137" → OOM
# - "Events:" sekcija na dnu → šta Kubernetes vidi
```

### Korak 3: Logovi Prije Crasha

```bash
# Logovi trenutne instance pod-a
kubectl logs <pod-name> -n project-a-prod

# Logovi prethodne instance (najvažnije kod CrashLoopBackOff!)
kubectl logs <pod-name> -n project-a-prod --previous

# Ako pod ima više containera (sidecar pattern)
kubectl logs <pod-name> -c go-service -n project-a-prod --previous

# Zadnjih 100 linija
kubectl logs <pod-name> -n project-a-prod --previous --tail=100
```

### Korak 4: Grafana

- Error rate spike: koji endpoint, koji servis, od kada tačno?
- Latency spike: timeout problemi?
- Pod restarts: da li je samo jedan ili svi pod-ovi?
- Memory/CPU: da li je resource exhaustion uzrok?

### Korak 5: CloudWatch RDS Metrici

U AWS Console → RDS → instance → Monitoring:
- **CPUUtilization**: > 80% duže od 5 min je problem
- **DatabaseConnections**: blizu `max_connections` → connection exhaustion
- **ReplicaLag**: za read replica setup, lag > 30s je alarm
- **FreeStorageSpace**: ako pada prema 0, hitna akcija

```bash
# Iz CLI
aws cloudwatch get-metric-statistics \
  --namespace AWS/RDS \
  --metric-name DatabaseConnections \
  --dimensions Name=DBInstanceIdentifier,Value=project-a-prod \
  --start-time "$(date -u -v-1H +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Maximum
```

---

## Exit Code Mapa

Exit code govori **zašto** je container završio. Ovo je prva stvar koju čitaš iz `kubectl describe`.

| Exit Code | Uzrok | Akcija |
|-----------|-------|--------|
| **0** | Normalan izlaz | Nije greška — provjeri je li restart policy problem |
| **1** | Application error | Provjeri application logove, obično exception/panic |
| **2** | Misuse of shell command | Provjeri CMD u Dockerfilu |
| **137** | OOM Killed (SIGKILL = 128 + 9) | Povećaj memory limit ili nađi memory leak |
| **139** | Segmentation fault (SIGSEGV = 128 + 11) | Problematičan binary — rollback odmah |
| **143** | Graceful shutdown (SIGTERM = 128 + 15) | Normalno (Kubernetes shutdown), osim ako prerano |
| **255** | Exit status out of range | Provjeri init container ili entrypoint skriptu |

### OOM — Exit Code 137

```bash
# Potvrda OOM-a
kubectl describe pod <pod> -n project-a-prod | grep -A5 "Last State"
# OOM bi trebao pisati: OOMKilled

# Trenutni limit koji ima
kubectl get pod <pod> -n project-a-prod -o yaml | grep -A5 resources

# Grafana: memory usage grafikon za taj pod — da li raste kontinuirano (leak)?

# Privremena akcija: povećaj memory limit u Helm values
# helm/project-a/values/prod.yaml:
# resources.limits.memory: 512Mi → 1Gi
```

---

## Rolling Restart Bez Downtime

```bash
# Restart svih pod-ova u deploymentu (zero-downtime rolling restart)
kubectl rollout restart deployment/go-service -n project-a-prod

# Prati napredak
kubectl rollout status deployment/go-service -n project-a-prod

# Provjeri da su novi pod-ovi zdravi
kubectl get pods -n project-a-prod -l app=go-service
```

`rollout restart` ne gasi sve pod-ove odjednom — prati RollingUpdate strategiju (stari pod živi dok novi nije Ready).

---

## Emergency Scale Up

```bash
# Hitno povećanje replika (za latency/capacity problem)
kubectl scale deployment go-service --replicas=5 -n project-a-prod

# Provjeri scaling napredak
kubectl get pods -n project-a-prod -l app=go-service -w

# Vrati na normalu nakon stabilizacije (ne zaboravi!)
kubectl scale deployment go-service --replicas=3 -n project-a-prod
```

**Napomena:** hitni scale-up je Nivo 3 operacija — zabilježi razlog. Skaliranje mijenja Helm managed state i može uzrokovati drift od IaC-a. Nakon incidenta update Helm values.

---

## Database Connection Exhaustion

Jedan od češćih production incidenat za project-a arhitekturu.

### Simptomi

- Go service logovi: `"too many connections"` ili `"dial tcp: connect: connection refused"`
- PHP service logovi: `"SQLSTATE[HY000] [1040] Too many connections"`
- Grafana: HTTP 5xx spike koji počinje postepeno, pa se ubrzava
- CloudWatch: `DatabaseConnections` blizu `max_connections` vrijednosti

### Dijagnoza

```bash
# Korak 1: Provjeri koliko konekcija ima prema MySQL
kubectl exec <mysql-pod-or-use-port-forward> -n project-a-prod -- \
  mysql -uroot -p -e "SHOW STATUS LIKE 'Threads_connected';"

# Korak 2: Ko drži konekcije?
kubectl exec <mysql-pod> -n project-a-prod -- \
  mysql -uroot -p -e "SHOW PROCESSLIST;"

# Korak 3: max_connections konfig
kubectl exec <mysql-pod> -n project-a-prod -- \
  mysql -uroot -p -e "SHOW VARIABLES LIKE 'max_connections';"

# Korak 4: Koliko replika Go servisa ima? (svaka replika = connection pool)
kubectl get deployment go-service -n project-a-prod -o jsonpath='{.spec.replicas}'
```

### Hitna Akcija

```bash
# Strategija: smanjiti broj instanci koje drže konekcije, dati MySQL-u da se "ohladi"
# 1. Smanjiti replike na minimum
kubectl scale deployment go-service --replicas=1 -n project-a-prod

# 2. Pričekati da konekcije padnu (10-30 sekundi)
kubectl exec <mysql-pod> -n project-a-prod -- \
  mysql -uroot -p -e "SHOW STATUS LIKE 'Threads_connected';"

# 3. Postepeno vraćati replike
kubectl scale deployment go-service --replicas=2 -n project-a-prod
# Provjeri DB connections... OK?
kubectl scale deployment go-service --replicas=3 -n project-a-prod
```

### Pravi Fix (Post-Incident)

Hitna akcija rješava simptom. Uzrok je obično:
- Connection pool size u aplikaciji je prevelik (`db.SetMaxOpenConns()` u Go)
- Memory leak koji sprječava graceful close konekcija
- Replika skala je porasla (CI deploy) bez promjene pool sizea

---

## Rollback Odluka: Kada Rollback vs Fix-Forward

Ovo je jedna od najtežih odluka u produkciji. Nema automatskog odgovora, ali postoji okvir:

### Rollback Odmah (Ne Čekaj)

| Situacija | Razlog |
|-----------|--------|
| Data corruption risk | Svaka sekunda više = više podataka u lošem stanju |
| Security issue (exposed credentials, SQLi) | Ne možeš si priuštiti čekati fix |
| Error rate > 30% | Sistem je efektivno neupotrebljiv za korisnike |
| Exit code 139 (segfault) | Problematičan binary, nema smisla debugovati u produkciji |
| Deploy je uzrok (korelacija je jasna) | Lako identificirati, lako reversirati |

```bash
helm rollback project-a -n project-a-prod
# Prati
kubectl rollout status deployment/go-service -n project-a-prod
```

### Fix-Forward (Nemoj Rollbackovati)

| Situacija | Razlog |
|-----------|--------|
| Config error (env var, ConfigMap) | Rollback ne pomaže — config je isti. Fix config, redeploy. |
| External dependency issue (3rd party API down) | Rollback ne pomaže — API je i dalje down |
| Database schema je vec migrirana | Rollback binaria sa novom shemom = veći problem |
| Infra issue (AWS, CloudFront) | Kod nije krivac |
| Greška u jednom podu, ostali rade | Rolling restart, ne rollback |

**Ključno pitanje za rollback odluku:** "Da se vrnem na prethodnu verziju, da li bi problem nestao?" Ako je odgovor "ne znamo" ili "možda ne" — razmisli o fix-forward-u.

---

## Post-Incident: Analiza Poslije

### Prikupljanje Evidence

```bash
# Sve events sortirane po vremenu
kubectl get events \
  --sort-by='.lastTimestamp' \
  -n project-a-prod \
  --output wide

# Events samo za specifičan pod
kubectl get events \
  -n project-a-prod \
  --field-selector involvedObject.name=<pod-name>

# Helm history (da vidiš koje izmjene su bile)
helm history project-a -n project-a-prod

# Provjeri CloudTrail za accese u periodu incidenta
aws cloudtrail lookup-events \
  --start-time "2024-01-13T14:00:00Z" \
  --end-time "2024-01-13T16:00:00Z" \
  --lookup-attributes AttributeKey=EventName,AttributeValue=StartSession
```

### Post-Incident Review (PIR) Template

Minimalni PIR za svaki produkcijski incident:

```
Incident: INC-456
Datum: 2024-01-13
Trajanje: 14:15 - 15:02 (47 minuta)
Impact: Go service 5xx, ~400 korisnika pogođeno

Timeline:
- 14:15 - Grafana alert: go-service 5xx rate > 5%
- 14:18 - Triage: CrashLoopBackOff na 2/3 go-service pod-ova
- 14:22 - Exit code 137 (OOM) identificiran
- 14:35 - Memory limit povećan na 1Gi, redeploy
- 15:02 - Sve pod-ove Running, error rate normalan

Root Cause: Memory leak u novoj verziji image-a (v1.2.5)
koji procesuira large payloade bez streaming-a.

Akcije:
- [ ] Fix memory leak u v1.2.6 (vlasnik: Marko, rok: 2 dana)
- [ ] Dodati memory trending alert u Grafanu (vlasnik: Ana, rok: 1 tjedan)
- [ ] Limit povećan u prod values trajno (done)
```

Blameless kultura: PIR nije da krivimo osobu, nego da poboljšamo sistem.

---

## Brzih Referenca Komandi za Incident

```bash
# Status svega
kubectl get all -n project-a-prod

# Crashirani pod-ovi
kubectl get pods -n project-a-prod | grep -v Running

# Logovi (prethodni container)
kubectl logs <pod> -n project-a-prod --previous --tail=100

# Detalji
kubectl describe pod <pod> -n project-a-prod

# Events (sortirano po vremenu)
kubectl get events --sort-by='.lastTimestamp' -n project-a-prod

# Rolling restart
kubectl rollout restart deployment/<name> -n project-a-prod

# Scale
kubectl scale deployment <name> --replicas=N -n project-a-prod

# Rollback
helm rollback project-a -n project-a-prod

# Prati rollout
kubectl rollout status deployment/<name> -n project-a-prod --timeout=5m
```
