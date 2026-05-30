# 08 — Vežba: Priprema AI-okvira i sync (sigurnost)

Gradiš AI-okvir koji forsira least-privilege RBAC, mrežnu izolaciju i čiste image-e, pa verifikuješ da klaster nema preširokih dozvola, da je default-deny mreža aktivna i da nema kritičnih CVE-a u image-ima.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Postavljamo cluster-security pravila (RBAC, NetworkPolicy, image scanning), pokrećemo SAST/dependency/container skenere i dokumentujemo nalaze sa planom remedijacije.

**Pretpostavke za potvrdu:**
- `kubectl` pristup klasteru postoji (bar read)
- GitLab CI pipeline je konfigurisan ili se može konfigurisati za security job-ove
- Trivy ili ekvivalent je dostupan lokalno ili u CI-u

**Van opsega:**
- Popravka svih HIGH/CRITICAL nalaza u ovoj vežbi — dokumentujemo ih sa planom
- Pisanje custom admission webhook-a (koristimo postojeće alate)

**Prompt za diskusiju:**
```
Daj least-privilege RBAC (Role + RoleBinding) za servis kome treba samo
read na ConfigMap-e u svom namespace-u, i default-deny NetworkPolicy.
Objasni:
- Zašto cluster-admin binding za aplikacijske ServiceAccount-e je opasan?
- Kako default-deny NetworkPolicy radi i koji pod-ovi su izuzeti?
- Koji Trivy finding pragovi su prihvatljivi za produkciju?
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Klaster ima least-privilege RBAC, default-deny NetworkPolicy i nema neprihvaćenih HIGH/CRITICAL image nalaza.

**Fajlovi koji se diraju:**
- `k8s/rbac.yaml` — Role i RoleBinding po servisu
- `k8s/network-policy.yaml` — default-deny + eksplicitni allow
- `k8s/deployment.yaml` — `runAsNonRoot`, `readOnlyRootFilesystem`, `securityContext`
- `.gitlab-ci.yml` — dodaj security scan stage

**Fajlovi koji se NE diraju:**
- `k8s/namespace.yaml` — namespace ostaje kao jeste
- Produkcijski secrets — ne diramo u ovoj vežbi

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/cluster-security-checks.mdc`
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/cluster-security-checks.md`

Sadržaj pravila (isti za oba alata):
```
- ServiceAccount po servisu; bez cluster-admin bindinga za aplikacije.
- Default-deny NetworkPolicy u svakom namespace-u, pa eksplicitni allow.
- Bez privileged/hostNetwork pod-ova; runAsNonRoot i readOnlyRootFilesystem gde može.
- Trivy scan u CI-u: blokira na CRITICAL; HIGH dokumentuje sa remedijacijom.
- kubectl auth can-i --list ne sme da pokazuje wildcard (*) za app ServiceAccount-e.
```

Anti-sprawl: uvedi `cluster-security-checks` — sigurnost je sistemska briga koja se ponavlja.

**Acceptance criteria:**
- [ ] `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>` ne pokazuje `*` ni `cluster-admin`
- [ ] default-deny NetworkPolicy aktivna u aplikacijskom namespace-u
- [ ] `trivy image` ne pokazuje neprihvaćene CRITICAL nalaze (HIGH su dokumentovani)
- [ ] GitLab Security dashboard prikazuje rezultate poslednjeg CI skena
- [ ] sync zapisan u `decision_log.md` / `CLAUDE.md`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Primenimo least-privilege Role + RoleBinding za app ServiceAccount
- Primenimo default-deny NetworkPolicy + eksplicitni allow za potreban saobraćaj
- Pokrenimo trivy lokalno i u GitLab CI
- Pregledamo GitLab Security dashboard nalaze

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta
> **Claude Code:** direktno u terminalu

Primeni RBAC i NetworkPolicy:

```bash
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/network-policy.yaml
```

Verifikuj dozvole za app ServiceAccount:

```bash
kubectl auth can-i --list --as=system:serviceaccount:<namespace>:<service-account>
# Nema wildcard (*); nema cluster-admin
```

Skeniraj image na ranjivosti:

```bash
docker run --rm aquasec/trivy image <slika>:<tag>
# Zabeleži sve CRITICAL i HIGH nalaze
```

Pokreni GitLab CI security scan job:

```bash
glab ci run --job container_scanning
# Ili pushuj branch i prati pipeline u GitLab UI
```

Proveri kube-bench CIS benchmark (opciono, ako je dostupno):

```bash
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml
kubectl logs job/kube-bench
```

Pregledaj GitLab Security dashboard:

```
GitLab → projekt → Security → Vulnerability Report
→ pregled svih nalaza → dokumentuj HIGH/CRITICAL sa statusom
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- kubectl auth can-i ne pokazuje wildcard za app ServiceAccount
- default-deny NetworkPolicy aktivna
- trivy bez neprihvaćenih CRITICAL nalaza
- GitLab Security dashboard prikazuje rezultate

Evo outputa:
[ovde lepiš: kubectl auth can-i output, kubectl get networkpolicy output, trivy summary, GitLab dashboard screenshot ili tekst]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>` | Lista dozvola bez `*`; nema `cluster-admin` |
| 2 | `kubectl get networkpolicy -n <namespace>` | Postoji `default-deny` policy; postoji eksplicitni allow policy |
| 3 | Pokušaj curl iz jednog pod-a prema drugom pod-u koji nije eksplicitno dozvoljen | Konekcija odbijena (timeout ili connection refused) |
| 4 | `docker run --rm aquasec/trivy image <slika>:<tag>` | Nula CRITICAL nalaza; svi HIGH su dokumentovani u decision log-u |
| 5 | GitLab → Security → Vulnerability Report | Prikazuje rezultate poslednjeg skena; svaki neprihvaćen nalaz ima assigned owner-a |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/sigurnost-tooling.md` ili `CLAUDE.md`

```
## [datum] — Sigurnost sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
