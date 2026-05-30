# 07 — Vežba: Priprema AI-okvira i sync (Secrets Manager)

Gradiš AI-okvir koji forsira „nema secrets u kodu" i verifikuješ da aplikacija čita tajne iz AWS Secrets Manager-a u runtime-u, bez ijednog plaintext secret-a u repou ili manifestima.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Postavljamo pravila koja sprečavaju plaintext tajne u repou, manifestima i env varijablama; verifikujemo da aplikacija dobija tajne kroz External Secrets Operator (ili ekvivalent) iz AWS Secrets Manager-a.

**Pretpostavke za potvrdu:**
- AWS Secrets Manager je dostupan i servis već ima secret kreiran
- External Secrets Operator ili slična integracija je ili instalirana ili je deo plana
- `kubectl` i `aws` CLI su konfigurisani

**Van opsega:**
- Pisanje rotation lambda funkcije od nule (samo verifikujemo da plan postoji)
- Migracija svih servisa odjednom — radimo jedan servis

**Prompt za diskusiju:**
```
Hoću da [servis] u Kubernetes-u dobija lozinke iz AWS Secrets Manager-a
bez plaintext-a u manifestima. Predloži pristup koristeći External Secrets Operator:
- Kako se SecretStore i ExternalSecret objekti definišu?
- Kako rotacija u SM-u automatski propagira u K8s Secret?
- Šta proveriti da nikad nije plaintext u env var-u (kubectl describe pod)?
Objasni svaki korak.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Servis čita tajne iz AWS Secrets Manager-a kroz K8s Secret koji kreira External Secrets Operator, bez ijednog plaintext secret-a u repou.

**Fajlovi koji se diraju:**
- `k8s/external-secret.yaml` — novi ExternalSecret manifest
- `k8s/secret-store.yaml` — novi SecretStore manifest
- `k8s/deployment.yaml` — ref na K8s Secret umesto hardcoded env

**Fajlovi koji se NE diraju:**
- `.env`, `.tfvars`, bilo koji fajl sa trenutnim plaintext secrets — ti fajlovi se brišu ili premještaju iz repoa

**AI okvir za ovu oblast:**

> **Cursor:** napravi/ažuriraj `.cursor/rules/secrets-hygiene.mdc`
> **Claude Code:** dodaj sekciju u `CLAUDE.md` ili napravi `.claude/rules/secrets-hygiene.md`

Sadržaj pravila (isti za oba alata):
```
- Nikad plaintext secret u repo (kod, .tfvars, compose, K8s manifesti).
- App dobija tajne preko SM/External Secrets u runtime-u, ne build-time.
- kubectl describe pod mora da pokazuje secretKeyRef, ne stvarnu vrednost.
- Predvideti rotaciju (rotation lambda ili managed rotation) — plan mora postojati.
- gitleaks pre svakog commit-a — nema merge-a ako detektuje secret.
```

Anti-sprawl: uvedi `secrets-hygiene` — rizik curenja je visok i ponavlja se kroz sve oblasti.

**Acceptance criteria:**
- [ ] `gitleaks` skenira repo i ne nalazi nijedan plaintext secret
- [ ] `kubectl describe pod <ime>` prikazuje `secretKeyRef`, ne stvarnu vrednost
- [ ] ExternalSecret objekat kreira K8s Secret povlačenjem iz AWS SM
- [ ] plan rotacije postoji (rotation je uključena ili postoji dokumentovan plan)
- [ ] sync zapisan u `decision_log.md` / `CLAUDE.md`

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Kreiramo SecretStore koji se autentifikuje prema AWS SM
- Kreiramo ExternalSecret koji povlači tajne i kreira K8s Secret
- Ažuriramo Deployment da koristi secretKeyRef umesto hardcoded env
- Verifikujemo gitleaks i kubectl describe

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta
> **Claude Code:** direktno u terminalu

Instaliraj External Secrets Operator ako već nije:

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace
```

Verifikuj da ESO radi:

```bash
kubectl get pods -n external-secrets
```

Primeni SecretStore i ExternalSecret:

```bash
kubectl apply -f k8s/secret-store.yaml
kubectl apply -f k8s/external-secret.yaml
kubectl get externalsecret -n <namespace>
kubectl get secret <ime-secret-a> -n <namespace>
```

Skeniraj repo na plaintext tajne:

```bash
docker run --rm -v "$PWD":/repo zricethezav/gitleaks detect --source=/repo
```

Verifikuj da pod ne izlaže plaintext vrednosti:

```bash
kubectl describe pod <ime-poda> -n <namespace>
# Tražiš: secretKeyRef: { name: ..., key: ... } — NE stvarnu vrednost
```

Ručno proveri vrednost iz SM-a (samo za potvrdu da sync radi — ne loguj output):

```bash
aws secretsmanager get-secret-value --secret-id <ime> --query SecretString
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- gitleaks ne nalazi plaintext secret u repou
- kubectl describe pod pokazuje secretKeyRef, ne vrednost
- ExternalSecret status je Synced
- plan rotacije postoji

Evo outputa:
[ovde lepiš: gitleaks output, kubectl describe pod isečak, kubectl get externalsecret status]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno fali?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | `kubectl describe pod <ime> -n <namespace>` | Prikazuje `secretKeyRef`, nikad plaintext vrednost |
| 2 | `kubectl get externalsecret -n <namespace>` | Status kolona pokazuje `SecretSynced` |
| 3 | `docker run --rm -v "$PWD":/repo zricethezav/gitleaks detect --source=/repo` | Nula nalaza — izlaz: `No leaks found` |
| 4 | U AWS konzoli: ažuriraj vrednost secret-a; sačekaj sync interval; restartuj pod; verifikuj da aplikacija radi sa novom vrednošću | Aplikacija radi korektno posle rotacije bez ponovnog deploy-a manifesta |
| 5 | `aws secretsmanager describe-secret --secret-id <ime>` | Polje `RotationEnabled` je `true` ili je dokumentovan manuelni plan rotacije |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/secrets-tooling.md` ili `CLAUDE.md`

```
## [datum] — Secrets Manager sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
