# 08 — Vežba: Monitoring (Prometheus, Grafana, Loki)

Validiraš AI-okvir za observability stack: Prometheus alert pravila prolaze `promtool` validaciju, dashboard paneli imaju jedinice i opise, a svaki alert ima runbook link.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Uvodimo rule `observability-checks` koji pokriva alert higijenu (for:, severity, runbook) i dashboard standarde. Validiramo konfiguracije alatima pre deploy-a.

**Pretpostavke za potvrdu:**
- Prometheus i Alertmanager su pokrenuti (lokalno ili u klasteru)
- Grafana dashboard postoji i ima barem jedan panel za proveru
- `promtool` i `amtool` su instalirani i dostupni u PATH-u

**Van opsega:**
- Podešavanje Loki pipelines i log parsinga
- Kreiranje novih dashboard-a od nule
- PagerDuty/OpsGenie integracija

**Prompt za diskusiju:**
```
Hoću SLO-based alert za [servis] (npr. 99.9% dostupnost).
Daj Prometheus pravilo sa error-budget burn rate i objasni pragove.
Uključi for:, severity label i annotations.runbook_url.
Potom objasni razliku između simptom-alertinga i uzrok-alertinga.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene  
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Uvesti `observability-checks` rule i dokazati da sve alert konfiguracije prolaze validaciju bez grešaka.

**Fajlovi koji se diraju:**
- `rules/*.yml` — Prometheus alert pravila
- `prometheus.yml` — glavna konfiguracija
- `alertmanager.yml` — Alertmanager konfiguracija
- `.cursor/rules/observability-checks.mdc` ili `CLAUDE.md` — novi rule

**Fajlovi koji se NE diraju:**
- `grafana/` dashboards JSON direktno — provera je ručna, ne automatska izmena
- `docker-compose.yml` — stack ostaje nepromenjen

**AI okvir za ovu oblast:**

> **Cursor:** napravi `.cursor/rules/observability-checks.mdc`  
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/observability-checks.md`

Sadržaj pravila (isti za oba alata):
```
# observability-checks
- Alert: ima `for:`, `severity` label, i `annotations.runbook_url`.
- Bazirati alert na simptomu (SLO burn rate), ne na uzroku gde god je moguće.
- Dashboard panel: definisane jedinice (ms, %, req/s) i opis; bez magičnih pragova bez objašnjenja.
- Svaki novi alert ima odgovarajući runbook dokument (makar stub).
```

Anti-sprawl: uvodi se jer monitoring okvir koriste i oblast 22 (deploy metrics) — zajednički rule ima smisla.

**Acceptance criteria:**
- [ ] `promtool check rules rules/*.yml` prolazi bez grešaka
- [ ] `promtool check config prometheus.yml` prolazi
- [ ] `amtool check-config alertmanager.yml` prolazi
- [ ] Svaki alert ima `for:`, `severity` i `annotations.runbook_url`
- [ ] Barem jedan dashboard panel ima definisane jedinice i opis
- [ ] Runbook URL vodi na postojeći dokument (ne 404)
- [ ] Sync zapisan

**AI pregled plana:**
```
Evo plana pre egzekucije:
1. Napraviti observability-checks rule
2. Pokrenuti promtool check rules i config
3. Pokrenuti amtool check-config
4. Ručno proveriti dashboard panele u Grafani
5. Verifikovati da svaki alert ima runbook link koji radi

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta  
> **Claude Code:** direktno u terminalu

Validacija alert pravila:

```bash
promtool check rules rules/*.yml
```

Validacija Prometheus konfiguracije:

```bash
promtool check config prometheus.yml
```

Validacija Alertmanager konfiguracije:

```bash
amtool check-config alertmanager.yml
```

Proveri da li postoje alert pravila bez obaveznih polja:

```bash
grep -rL "runbook_url" rules/*.yml
grep -rL "severity" rules/*.yml
```

Test da alert puca na simuliranom uslovu (ako postoji test file):

```bash
promtool test rules tests/*.yml
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- promtool check rules prolazi bez grešaka
- promtool check config prolazi
- amtool check-config prolazi
- Svaki alert ima for:, severity i runbook_url
- Dashboard panel ima jedinice i opis
- Runbook URL ne vraća 404

Evo outputa / diff-a / konfiguracije:
[ovde lepiš: output sva tri alata, grep output za runbook_url i severity, screenshot Grafana panela sa jedinicama]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | Otvori Grafana, navigiraj do dashboard-a za servis | Dashboard se učitava bez grešaka |
| 2 | Klikni na panel i otvori Edit | Panel ima definisane jedinice (npr. ms, %) i opis u polju Description |
| 3 | U Alertmanager UI provjeri listu aktivnih alert-a | Vidljivi su severity i annotations |
| 4 | Klikni na runbook link u nekom alert-u | Otvara se runbook dokument, ne 404 |
| 5 | Simuliraj test uslov za jedan alert (npr. spusti threshold) | Alert pređe u Firing stanje u Prometheus UI |
| 6 | Vrati threshold na normalu | Alert se razreši i pređe u Resolved |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`  
> **Claude Code:** zapiši u `docs/decisions/monitoring-tooling.md` ili `CLAUDE.md`

```
## [datum] — Monitoring sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
