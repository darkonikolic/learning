# 09 — Vežba: Priprema AI-okvira i sync (load balancer)

Gradiš AI-okvir koji pokriva ALB/ingress rutiranje, health check-ove i TLS higijenu, pa verifikuješ da saobraćaj prolazi kroz load balancer (ne direktno na pod IP), da health check-ovi detektuju nezdrave backend-e i da HTTPS redirect radi.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo pravila za load balancer konfiguraciju (ALB ili K8s Ingress), verifikujemo da saobraćaj nikad ne ide direktno na pod IP, da health check-ovi ispravno detektuju i isključuju nezdrave pod-ove, i da TLS konfiguracija zadovoljava minimalne standarde.

**Pretpostavke za potvrdu:**
- ALB ili K8s Ingress je već konfigurisan ili se konfigurišemo u ovoj vežbi
- DNS je usmeren na LB (ili koristimo `curl` sa `-H Host:` headerom za testiranje)
- TLS sertifikat postoji (ACM ili cert-manager)
- `curl` i `aws` CLI su dostupni lokalno

**Van opsega:**
- WAF pravila (posebna vežba)
- Autoscaling target grupe (posebna vežba)
- mTLS između servisa (to je service mesh tema)

**Prompt za diskusiju:**
```
Hoću ALB ispred [servisa] sa HTTPS, redirect-om sa HTTP i health check-om na /health.
Daj konfiguraciju (Terraform za ALB ili K8s Ingress YAML):
- Zašto health check treba da cilja /health, a ne /?
- Šta je deregistration delay i zašto je bitan pri rolling deploy-u?
- Koji TLS cipher i protokol je minimalni standard za 2025?
- Kako da verifikujem da curl prolazi kroz LB, a ne direktno na pod?
```

---

## 2. Plan

Aktiviraj plan mode: u Claude Code terminalu kucaj `/plan` pre bilo koje izmene.

**Cilj:** Sav saobraćaj prolazi kroz LB, health check-ovi ispravno isključuju nezdrave backend-e, HTTP se redirectuje na HTTPS, i TLS >= 1.2 je aktivan.

**Fajlovi koji se diraju:**
- `terraform/alb.tf` ili `k8s/ingress.yaml` — LB/Ingress konfiguracija
- `terraform/target-group.tf` — health check putanja, pragovi, deregistration delay
- `k8s/service.yaml` — Service objekat koji Ingress targetira

**Fajlovi koji se NE diraju:**
- `k8s/deployment.yaml` — Deployment ostaje; ne menjamo repliku count ovde
- `terraform/rds.tf` — baza nije u opsegu

**AI okvir za ovu oblast:**

Dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/lb-checks.md`

Sadržaj pravila:
```
- Health check cilja dedikovan /health endpoint, ne /; pragovi razumni (ne flapping: 2 healthy, 3 unhealthy).
- HTTP → HTTPS redirect obavezan; TLS >= 1.2; bez slabih cipher-a (RC4, DES, 3DES).
- Deregistration delay >= 30s da se in-flight zahtevi završe pri rolling deploy-u.
- curl test uvek kroz LB DNS/IP — nikad direktno na pod IP za verifikaciju.
- ALB/Ingress access log omogućen za audit saobraćaja.
```

Anti-sprawl: proširi postojeće `k8s-manifest-checks` ili `terraform-checks` — novi rule samo ako LB tema nije pokrivena.

**Acceptance criteria:**
- [ ] `curl -fsS https://<host>/health` vraća HTTP 200 kroz LB
- [ ] `curl -fsS http://<host>` daje redirect 301/302 na HTTPS
- [ ] `aws elbv2 describe-target-health` prikazuje sve targete kao `healthy`
- [ ] ukloni jedan pod; verifikuj da LB prestaje da šalje saobraćaj na taj pod; vrati pod; verifikuj da se ponovo registruje
- [ ] TLS scan pokazuje minimalnu verziju TLS 1.2 i nema kritičnih cipher slabosti
- [ ] Sync zapisan u `.claude/memory/decisions.md` ili `CLAUDE.md ## Decision log` / `CLAUDE.md`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Verifikujemo LB konfiguraciju (health check putanja, deregistration delay)
- Testiramo curl kroz LB za HTTP redirect i HTTPS /health
- Testiramo failover: uklanjamo jedan backend i pratimo target health
- Skeniramo TLS konfiguraciju

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

U Claude Code terminalu izvršavaš komande direktno — Claude ima pristup shellu.

Verifikuj da health endpoint vraća 200 kroz LB:

```bash
curl -fsS https://<host>/health
# Očekivano: HTTP 200 i JSON/tekst odgovor od servisa
```

Verifikuj HTTP → HTTPS redirect:

```bash
curl -v http://<host> 2>&1 | grep -E "Location|HTTP/"
# Očekivano: HTTP/1.1 301 ili 302, Location: https://...
```

Proveri status svih target-a u target grupi:

```bash
aws elbv2 describe-target-health \
  --target-group-arn <arn> \
  --query "TargetHealthDescriptions[*].{Target:Target.Id,Port:Target.Port,State:TargetHealth.State}"
# Svi moraju biti healthy
```

Failover test — ukloni jedan pod i verifikuj:

```bash
# Skaliraj na 1 manje da simuliraš pad pod-a
kubectl scale deployment <ime> --replicas=<n-1> -n <namespace>

# Sačekaj deregistration delay (~30s) pa proveri target health
sleep 35
aws elbv2 describe-target-health --target-group-arn <arn>
# Jedan target mora biti draining ili unhealthy

# Vrati repliku
kubectl scale deployment <ime> --replicas=<n> -n <namespace>
```

Skeniraj TLS konfiguraciju:

```bash
docker run --rm drwetter/testssl.sh https://<host>
# Tražiš: TLS 1.2+ OK, nema F ocenu, nema kritičnih cipher upozorenja
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- curl https://<host>/health vraća 200
- curl http://<host> daje redirect na HTTPS
- svi target-i su healthy
- failover test pokazuje da LB prestaje slati saobraćaj na uklonjeni pod
- TLS >= 1.2, nema kritičnih cipher slabosti

Evo outputa:
[ovde lepiš: curl output za /health i http redirect, aws elbv2 describe-target-health output pre i posle failover testa, testssl.sh summary]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `curl -fsS https://<host>/health` | HTTP 200; odgovor dolazi od servisa (ne od LB direktno) |
| 2 | `curl -v http://<host>` | HTTP 301/302 redirect na `https://` |
| 3 | `aws elbv2 describe-target-health --target-group-arn <arn>` | Svi targeti u stanju `healthy` |
| 4 | Skaliraj deployment na n-1; sačekaj 35s; ponovi `aws elbv2 describe-target-health` | Jedan target je `draining` ili `unhealthy`; saobraćaj ide na preostale pod-ove |
| 5 | `docker run --rm drwetter/testssl.sh https://<host>` | TLS 1.2 ili 1.3 je minimum; nema `F` ocenu; nema RC4/DES cipher-a |

**Sync — zatvori petlju:**

Zapiši u `.claude/memory/decisions.md` ili u `CLAUDE.md` sekciju `## Decision log`

```
## [datum] — Load balancer sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
