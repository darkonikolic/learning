# 10 — Vežba: priprema AI-okvira i sync (shutdown i resume)

Postavljaš AI-okvir koji štiti od gubitka podataka pri gašenju okruženja, pa verifikuješ da su resursi stvarno zaustavljeni (ne samo tagged) i da se okruženje ispravno podiže.

---

## 1. Diskusija

Pre nego počneš, razjasni sa AI-om:

**Šta tačno radimo:**
Definišemo `safe-teardown-checklist` — šta snapshot-ovati, kojim redom gasiti/podizati, šta nikad ne rušiti (state bucket, persistentni podaci). Ovo je zaštita od skupih grešaka, ne optimizacija.

**Pretpostavke za potvrdu:**
- Okruženje je aktivno i ima resurse koji koštaju (EC2, RDS, NAT Gateway)
- Remote state (S3 + DynamoDB) postoji i ne sme biti obrisan
- Imaš dovoljno IAM dozvola za `rds:CreateDBSnapshot`, `ec2:CreateSnapshot`, `ec2:StopInstances`
- Znaš razliku između `stop` (zadržava resurs) i `terminate`/`destroy` (briše resurs)

**Van opsega:**
- Automatski scheduler za gašenje (EventBridge) — to je optimizacija, ovde radimo ručni kontrolisani proces
- Brisanje state bucket-a ili DynamoDB tabele — to je katastrofalna greška, nikad u ovom procesu
- Cold start optimizacija — fokus je na bezbednosti, ne performansama

**Prompt za diskusiju:**
```
Gasim okruženje project-A preko noći radi uštede troškova. Resursi su: [EC2, RDS, NAT Gateway, ELB]. Šta moram da snapshot-ujem pre gašenja, kojim redom da gasim da ne izgubim podatke, i šta apsolutno ne smem obrisati (state, podaci)? Napravi korak-po-korak checklist.
```

---

## 2. Plan

> **Cursor:** uključi Plan mode pre bilo koje izmene
> **Claude Code:** `/plan` u terminalu pre bilo koje izmene

**Cilj:** Verifikovati da backup/snapshot postoji pre gašenja, da su resursi stvarno zaustavljeni (ne samo planirani za zaustavljanje), i da resume vraća radno stanje.

**Fajlovi koji se diraju:**
- `.cursor/rules/safe-teardown-checks.mdc` (Cursor) — novo pravilo
- `CLAUDE.md` ili `.claude/rules/safe-teardown-checks.md` (Claude Code) — nova sekcija
- `docs/decisions/shutdown-resume-log.md` — zapis svakog gašenja/podizanja

**Fajlovi koji se NE diraju:**
- `backend.tf` i S3 state bucket — nikad
- `terraform.tfstate` — nikad ručno
- RDS instanca bez prethodnog snapshot-a — sačekaj potvrdu da snapshot postoji

**AI okvir za ovu oblast:**

> **Cursor:** napravi `.cursor/rules/safe-teardown-checks.mdc` (globs: `paths/project-A/**`)
> **Claude Code:** dodaj sekciju `## Safe teardown checklist` u `CLAUDE.md`, ili napravi `.claude/rules/safe-teardown-checks.md`

Sadržaj pravila (isti za oba alata):
```
# Pre destroy/stop:
- RDS: kreirati manual snapshot i potvrditi status "available" pre nastavka.
- EBS: kreirati snapshot za sve volume-e koji nisu ephemeral.
- Secrets Manager / Parameter Store: izvesti vrednosti ako su jedino mesto čuvanja.
- Potvrditi da S3 state bucket i DynamoDB lock tabela NISU u destroy planu.
- Redosled gašenja: ELB/ALB → EC2 → RDS → NAT Gateway (ne obrnuto).

# Resume:
- Redosled podizanja: NAT Gateway → RDS (restore from snapshot ako je terminiran) → EC2 → ELB.
- Posle podizanja: health check na svakom sloju pre sledećeg.
- Smoke test: HTTP request na aplikaciju ili DB konekcija test pre proglašenja uspeha.
```

Anti-sprawl: shutdown/resume je specifičan za oblast 09 ali je rizik gubitka podataka visok i ponavlja se sa svakim ciklusom — pravilo je opravdano.

**Acceptance criteria:**
- [ ] RDS snapshot postoji i status je `available` pre bilo kakvog gašenja
- [ ] EBS snapshots postoje za sve non-ephemeral volume-e
- [ ] `terraform plan -destroy` pregledan i state bucket/DynamoDB tabela nisu u destroy listi
- [ ] posle `stop` (ne `terminate`): EC2 instance status je `stopped`, ne `running`
- [ ] posle resume-a: smoke test prolazi (HTTP 200 ili DB konekcija uspešna)
- [ ] sync zapisan u decision log

**AI pregled plana:**
```
Evo plana pre egzekucije:
- Kreirati RDS i EBS snapshot
- Pregledati terraform plan -destroy (verifikovati šta odlazi)
- Zaustaviti resurse redom: ELB → EC2 → RDS → NAT Gateway
- Verifikovati da su stvarno stopped (ne samo initiated)
- Resume: podići redom i smoke test

Da li su acceptance criteria merljivi i testabilni?
Šta fali ili je nejasno pre nego počnem?
```

---

## 3. Egzekucija

> **Cursor:** koristiš `/devops-engineer` agenta
> **Claude Code:** direktno u terminalu

```bash
# ===== SHUTDOWN =====

# 1. Kreiraj RDS snapshot pre gašenja
aws rds create-db-snapshot \
  --db-instance-identifier <rds-instance-id> \
  --db-snapshot-identifier project-a-snapshot-$(date +%Y%m%d)

# 2. Čekaj da snapshot postane available
aws rds wait db-snapshot-available \
  --db-snapshot-identifier project-a-snapshot-$(date +%Y%m%d)

# 3. Potvrdi da snapshot postoji
aws rds describe-db-snapshots \
  --db-instance-identifier <rds-instance-id> \
  --query "DBSnapshots[*].{ID:DBSnapshotIdentifier,Status:Status,Time:SnapshotCreateTime}" \
  --output table

# 4. Pregled destroy plana — proveri da state bucket NIJE u listi
terraform plan -destroy -out=destroy-plan
terraform show destroy-plan | grep -E "will be destroyed|aws_s3_bucket|aws_dynamodb"

# 5. Zaustavi EC2 instance (stop, ne terminate)
aws ec2 stop-instances --instance-ids <instance-id-1> <instance-id-2>

# 6. Verifikuj da su stopped (čekaj)
aws ec2 wait instance-stopped --instance-ids <instance-id-1> <instance-id-2>
aws ec2 describe-instances \
  --instance-ids <instance-id-1> \
  --query "Reservations[*].Instances[*].{ID:InstanceId,State:State.Name}" \
  --output table

# ===== RESUME =====

# 7. Pokreni instance
aws ec2 start-instances --instance-ids <instance-id-1> <instance-id-2>
aws ec2 wait instance-running --instance-ids <instance-id-1> <instance-id-2>

# 8. Verifikuj da infrastruktura odgovara state-u (očekuje se "no changes")
terraform plan

# 9. Smoke test
curl -f http://<app-url>/health || echo "FAIL: aplikacija ne odgovara"
```

---

## 4. AI validacija

```
Evo acceptance criteria iz plana:
- RDS snapshot postoji i status je available
- terraform plan -destroy: state bucket i DynamoDB tabela NISU u destroy listi
- EC2 instance status je stopped (ne running)
- posle resume-a: smoke test prolazi

Evo outputa komandi:
[ovde lepiš output describe-db-snapshots, describe-instances i smoke test]

Za svaki acceptance kriterijum: da ✓ ili ne ✗.
Ako ne — šta tačno nije zaustavljeno ili koji snapshot nedostaje?
```

---

## 5. UAT — ručna validacija

| # | Akcija | Očekivani rezultat |
|---|--------|--------------------|
| 1 | AWS konzola → RDS → Snapshots → filtriraj po DB instance identifier | Manual snapshot sa danas-datumom postoji, Status kolona pokazuje `Available` (zeleno) |
| 2 | AWS konzola → EC2 → Instances → filtriraj po project tagu | Sve instance imaju State `stopped` (narandžasto) — nema `running` instance |
| 3 | AWS konzola → EC2 → Instances → pokreni instance → sačekaj `running` → klikni na Public IP | Aplikacija odgovara na HTTP request ili SSH konekcija uspeva |
| 4 | AWS konzola → Billing → Cost Explorer → Today | Troškovi za EC2 i RDS su drastično niži ili nula u periodu dok su instance bile stopped |
| 5 | Pokreni `terraform plan` u terminalu posle resume-a | Output prikazuje `No changes. Infrastructure is up-to-date.` — state i stvarno stanje su sinhronizovani |

**Sync — zatvori petlju:**

> **Cursor:** zapiši u `.cursor/memory/decision_log.md`
> **Claude Code:** zapiši u `docs/decisions/shutdown-resume-log.md` ili `CLAUDE.md`

```
## [datum] — Shutdown/resume sync
- Urađeno:
- Naučeno:
- Šta bi promenio:
```
