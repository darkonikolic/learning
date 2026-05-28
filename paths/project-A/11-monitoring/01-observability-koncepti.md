# 01 — Observability koncepti

## Teorija

Observability je sposobnost razumijevanja unutrašnjeg stanja sistema
na osnovu njegovih vanjskih izlaza. Nisi tu da "gledalj" — tu si da možeš postavljati
pitanja o sistemu koja nisi predvidio unaprijed.

---

## Tri stuba observability-a

### Metrics

Numerički podaci o stanju sistema kroz vrijeme.

- CPU usage: 78%
- HTTP requests per second: 142
- Pod restart count: 3

Metrics su efikasni, komprimovani, idealni za alerting i dashboarde.
**Ne govore ti zašto** — govore ti da nešto nije normalno.

### Logs

Tekstualni zapisi konkretnih događaja.

```
2026-05-27T14:23:01Z [ERROR] Failed to connect to database: connection timeout
2026-05-27T14:23:02Z [INFO] Retrying connection (attempt 2/3)
2026-05-27T14:23:05Z [ERROR] Max retries exceeded. Service unavailable.
```

Logovi govore **šta se desilo** u specifičnom trenutku, na specifičnom servisu.

### Traces

Praćenje jednog zahtjeva kroz sve servise:

```
Request ID: abc123
  → nginx (2ms)
    → app-service (145ms)
      → database (140ms) ← bottleneck!
    → cache-service (1ms)
  Total: 148ms
```

Traces govore **gdje se troši vrijeme** i kako servisi interaguju.

---

## Monitoring vs Observability

**Monitoring**: znaš unaprijed što gledaš. Postavljaš dashboarde i alarme za
poznate metrike. "CPU > 80% → alarm". Reaktivno za poznate probleme.

**Observability**: možeš istražiti nepoznate probleme. Postaviš pitanje "zašto su
p95 latency spikes svaki petak u 17:00?" i imaš podatke da odgovoriš. Proaktivno
za nove probleme.

Za project-A: počinjemo sa monitoringom (postavljamo poznate metrike i alarme),
gradimo prema observability-u (korelacija metrics + logs).

---

## Zašto monitoring: znaš da nešto ne radi PRE korisnika

Bez monitoringa, redoslijed otkrića greške:

1. Korisnik ne može pristupiti aplikaciji
2. Korisnik kontaktira support
3. Support otvara ticket
4. Dev team dobija ticket
5. Dev team gleda logove da razumije problem
6. Prosječno: 45-90 minuta od incidenta do saznanja

Sa monitoringom i alertingom:

1. Pod pada u CrashLoopBackOff
2. Prometheus detektuje: `kube_pod_container_status_restarts_total > 0` za 5 minuta
3. Alertmanager šalje Slack poruku on-call inženjeru
4. Prosječno: 5-10 minuta od incidenta do saznanja

**MTTD** (Mean Time To Detect) pada sa 60 minuta na 5 minuta.
Korisnik često nikad ne sazna da je problem bio.

---

## Stack za project-A

```
Metrics:  Prometheus + Grafana
Logs:     Loki + Grafana (isti UI za oba!)
Alerts:   Alertmanager → Slack / Email
```

Sve se instalira jednom Helm komandom: `kube-prometheus-stack`.

Grafana je jedina UI koju inženjer treba da otvori:
- Dashboarde za metrics
- Explore za logs (Loki)
- Alerting management

---

## kube-prometheus-stack: šta instalirate jednom komandom

```
kube-prometheus-stack
├── Prometheus Operator     — CRD-driven konfiguracija
├── Prometheus              — metrics collection & storage
├── Grafana                 — vizualizacija & alerting
├── Alertmanager            — alert routing & deduplication
├── kube-state-metrics      — K8s objekt metrike
├── node-exporter           — hardware & OS metrike
└── PrometheusRule CRDs     — alert pravila kao K8s objekti
```

Sve u namespace-u `monitoring`. Jedna instalacija, sva infrastruktura za observability.

---

## Monitoring per environment

| Environment | Monitoring | Razlog |
|-------------|-----------|--------|
| kind (lokal) | Da | Vježbanje, ne troši AWS |
| dev | Da | Early detection, trendovi |
| staging | Obavezno | Mora biti identično produkciji |
| prod | Obavezno | Biznis zahtjev |

**Staging i prod moraju imati isti monitoring stack** — da bi anomalije koje se
jave u staging-u bile vidljive na isti način kao u prod-u.

---

## Veza sa project-A

Za project-A, monitoring stack odgovara na pitanja:

- Da li nginx servira zahtjeve? (nginx metrics)
- Koliko memorije troši helloworld Pod? (container metrics)
- Je li K8s cluster zdrav? (kube-state-metrics)
- Šta piše u nginx error logu? (Loki)
- Kad je zadnji put restartan Pod? (Alertmanager history)

Bez monitoringa, `kubectl get pods` je jedini uvid. Sa monitoringom, imaš
historiju, trendove i proaktivne alarme.
