# AI Workflow za DevOps

## Zašto AI menja DevOps workflow

Tradicionalni DevOps zahtjeva pamćenje stotina komandi, sintakse različitih alata i
best practices koji se mijenjaju svakih godinu-dvije. AI ne zamjenjuje to znanje —
ali ubrzava implementaciju i smanjuje "koliko je sintaksa za ovu opciju?" kočnicu.

Razlika je ključna: inženjer koji razumije infrastrukturu + AI koji piše konfiguraciju
je produktivniji tim od inženjera koji samo kopira AI output bez razumijevanja.

**Šta AI mijenja:**
- Pisanje boilerplate koda (Terraform moduli, Helm chartovi, pipeline YAML)
- Debugging nepoznatih errora (paste log, dobij objašnjenje)
- Istraživanje opcija ("koji je best practice za X?")
- Provjera koda kojeg si napisao ("ima li sigurnosnih propusta?")

**Šta AI NE mijenja:**
- Arhitekturne odluke — ti odlučuješ da li VPC treba 2 ili 3 AZ-a
- Razumijevanje infrastrukture — kada pipeline pukne u 3 ujutro, AI neće debugovati umjesto tebe
- Sigurnosne politike — AI predlaže, ali sigurnosni tim (ili ti) potvrđuju
- Produkcione odluke — nikad ne deployas ono što nisi razumio

## Tri uloge AI-a u project-A

### 1. Generator

AI piše strukturu koda koji ti opisuješ. Koristiš ga kada:
- Kreiraš novi Terraform modul ("napiši VPC modul sa public/private subnets")
- Pišeš Helm template koji ima mnogo boilerplatea ("napiši Deployment sa svim best practice opcijama")
- Kreiras GitLab CI job koji nisi radio ranije ("napiši job koji radi Trivy scan i failuje na HIGH vulns")

Pravilo generatora: uvijek traži objašnjenje zajedno sa kodom. Prompt
"napiši X" je lošiji od "napiši X i objasni zašto svaki dio postoji".

### 2. Debugger

AI analizira greške koje dobijaš. Koristiš ga kada:
- Pod je u CrashLoopBackOff i ne znaš zašto — prijepi `kubectl describe pod` output
- Terraform apply failuje sa nejasnom greškom — prijepi cijeli error
- GitLab pipeline job failuje — prijepi failed job log

Pravilo debuggera: daj što više konteksta. Ne pitaj "zašto puca?", pitaj
"evo kubectl logs, evo deployment YAML, evo što sam zadnji put promenio — šta nije u redu?"

### 3. Reviewer

AI analizira kod koji si napisao (ili koji je on generisao). Koristiš ga kada:
- Završiš Terraform konfiguraciju — "pregledaj sa sigurnosnog aspekta"
- Napišeš pipeline — "identifikuj bottlenecke i predloži optimizacije"
- Spremaš se za produkciju — "šta može poći po zlu u ovom Helm chartu?"

Pravilo reviewera: budi specifičan o čemu tražiš review. "Pregledaj ovaj kod"
je lošije od "pregledaj ovaj Terraform za: sigurnosne propuste, previsoke troškove,
i sve što bi moglo pući pri terraform destroy".

## Kada NE koristiti AI bez razmišljanja

**Sigurnosne odluke**: AI može predložiti IAM politiku, ali ti moraš razumjeti svaku
permisiju. "Least privilege" nije samo fraza — svaka extra permisija je sigurnosni rizik.

**Produkcione promjene**: AI-generisan `terraform apply` na prod bez plan reviewa je
recept za incident. Uvijek: generiši → razumij → testiraj na dev → primijeni na prod.

**Rotacija secretsa**: AI ne zna tvoje produkcione credentialse (i ne bi trebao).
Pipeline variables, AWS IAM roleovi, kubeconfig — to setup ti, ne AI.

**Arhitektura datastore-a**: Odluka "koristimo RDS vs DynamoDB" ima dugoročne posljedice.
AI može objasniti tradeoff, ali odluka je tvoja sa kontekstom tvog projekta.

**Debugging u produkciji**: AI može biti vodič ("pokušaj ovo"), ali kada sistem gori,
ti moraš razumjeti šta radiš. Nasumično kopiranje AI komandi na prod je opasno.

## AI workflow kroz module project-A

Svaki modul u ovom putu ima AI workflow primjere. Evo pregleda:

| Modul | AI uloga | Primjer |
|-------|----------|---------|
| 01 Docker | Generator | "Napiši multi-stage Dockerfile za nginx sa custom config" |
| 04 Helm | Generator + Reviewer | "Generiši chart, potom pregledaj sa security aspekta" |
| 05 Terraform | Generator + Debugger | "Piši VPC modul" → "Plan failuje, evo errora" |
| 07 Terraform AWS | Generator + Reviewer | EKS modul + cost review |
| 08 Pipelines | Generator + Debugger | Pipeline YAML + failed job debug |
| 09 Monitoring | Generator | "Napiši PrometheusRule za nginx error rate alert" |
| 10 AI DevOps | Sve tri uloge | Ovaj modul — konkretni promptovi |
| 11 Graduation | Sve tri uloge | Kompletan projekt sa AI kroz sve faze |

## Princip: AI nije crna kutija

Svaki put kada koristiš AI output, moraš biti u stanju odgovoriti na:
1. Šta ovaj resurs/konfiguracija radi?
2. Šta se dešava ako ga obrišem/promijenim?
3. Da li ima alternativa i zašto je ovaj pristup bolji?

Ako ne možeš odgovoriti — to je signal da pitaš AI za objašnjenje prije nego što
nastaviš. "Objasni mi ovaj Terraform kod kao da učim infrastrukturu" je sasvim
validan prompt.
