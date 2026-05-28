# 01 — Principi i Strategije Shutdown-a

## Zašto je ephemeral infrastruktura važna

**Osnovno pravilo:** Ako ne možeš uništiti environment za 20 minuta, infrastruktura nije pod kontrolom.

Terraform `destroy` mora raditi pouzdano. Ako ne radi, to znači da:
- Resursi su kreirani izvan Terraforma (ručno, kroz konzolu)
- Postoje dependencies koje Terraform ne zna za njih (orphan resursi)
- State je desinhronizovan od stvarnog stanja u AWS-u

Za svaki `terraform apply` mora odmah uslijediti test `terraform destroy`. Ne čekaj kraj projekta.

---

## Troškovi ovog projekta

```
EKS control plane:    $0.10/h  × 8h = $0.80/dan
EKS node t3.medium:   $0.047/h × 8h = $0.38 × 2 nodova = $0.76/dan
RDS db.t3.micro:      $0.034/h × 8h = $0.27/dan
NAT Gateway:          $0.045/h × 8h = $0.36/dan
ALB:                 ~$0.022/h × 8h = $0.18/dan
─────────────────────────────────────────────────
Total 8h aktivnog rada: ~$2.37/dan
Total ako ostaviš upaljeno (24h): ~$7.12/dan
Total za cijeli radni tjedan (5× 8h): ~$11.85
Total ako zaboraviš ugasiti vikend: ~$14.24 ekstra
```

**Realni trošak nepažnje:** Zaboravljeni environment tokom vikenda = ~$14. Na mjesečnom nivou, environment koji radi 24/7 kosta ~$214/mj.

---

## Tri strategije shutdown-a

| Strategija | Kada koristiti | Trošak u pauzi | Resume time |
|------------|----------------|----------------|-------------|
| **Total reset** | Learning, nema pravih podataka | $0 | 15–20 min |
| **Snapshot + destroy** | Prod, rijetka upotreba | ~$2/mj (snapshot storage) | 15–20 min |
| **Compute-only destroy** | Prod, dnevna pauza | ~$5/mj (RDS stopped storage) | 8–10 min |

---

## Strategija 1: Total Reset (Learning Mode)

**Princip:** Uništi sve, kreiraj sve iznova. Nema podataka koje trebaš čuvati.

```
terraform destroy → $0 trošak → terraform apply → seed database
```

**Prednosti:**
- Garancija da infrastruktura kao kod radi od nule
- Primorava te da automatizuješ sve (seed, migracije, konfiguracija)
- Nema orphan resursa, nema stale statea
- Trošak: $0 dok ne radiš

**Mana:** Database se resetuje. Za learning — to je feature, ne bug.

---

## Strategija 2: Snapshot + Destroy (Production Mode)

**Princip:** Napravi snapshot RDS-a, uništi sve, pri resume-u restore iz snapshota.

```
RDS snapshot → helm uninstall → terraform destroy → $0
(resume) → terraform apply sa snapshot_identifier → helm install → app radi
```

**Troškovi dok je pausirano:**
- RDS snapshot 20GB gp3: ~$0.023/GB/mj × 20GB = ~$0.46/mj
- Sve ostalo: $0

**Primjena:** Produkcionо okruženje koje se koristi rijetko (jednom sedmično ili manje).

---

## Strategija 3: Compute-Only Destroy (Daily Pause)

**Princip:** Uništi skupo računarstvo (EKS nodovi, NAT Gateway), zaustavi RDS. Ostavi jeftinu infrastrukturu (VPC, EKS control plane, Security Groups).

```
EKS nodes scale → 0 → NAT Gateway delete → RDS stop
(resume) → terraform apply -target → RDS start → nodes scale up
```

**Troškovi dok je pausirano (8h):**
- EKS nodovi: $0 (skaliran na 0)
- NAT Gateway: $0 (obrisan)
- RDS stopped: $0 (samo storage billing)
- EKS control plane: $0.10/h × 16h = $1.60 (ako zadržiš)

**Primjena:** Tim koji radi svaki dan, želi brži resume (8–10 min vs 15–20 min).

---

## Odlučivanje: Koji pristup koristiti

```
Je li ovo learning environment?
  └── DA → Total Reset. Uvijek.

Je li ovo production?
  ├── Koristiš ga svaki dan?
  │   └── DA → Compute-Only Destroy (EOD pause)
  └── Koristiš ga rijetko?
      └── DA → Snapshot + Destroy
```

---

## Pravila kojih se mora držati

**Pravilo 1 — Test destroy odmah:**
```bash
# Nakon svakog modula koji uključuje terraform apply:
terraform destroy -var-file=dev.tfvars -auto-approve
# Ako ovo ne radi → STOP, istraži zašto, popravi, tek onda nastavi
```

**Pravilo 2 — Nikad ne ostavljaj environment upaljenom:**
```bash
# Svaki put kad završiš rad:
bash scripts/total-destroy.sh dev
# Ili barem:
bash scripts/eod-pause.sh dev
```

**Pravilo 3 — Provjeri trošak sljedeći dan:**
```bash
# Svako jutro, provjeri što je ostalo upaljeno
bash scripts/cost-check.sh dev
```

**Pravilo 4 — AWS Budget alarm mora biti aktivan:**
- Postavi alarm na $50/mj
- Alert na 80% ($40) — upozorenje
- Alert na 100% ($50) — akcija

Bez ovog alarma, ne pokreći nikakav AWS environment.
