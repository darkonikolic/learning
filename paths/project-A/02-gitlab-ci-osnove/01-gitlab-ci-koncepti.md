# 01 - GitLab CI: Koncepti i Zašto

## Problem koji CI/CD rješava

Zamislite situaciju bez automatizacije. Razvijate nginx hello-world aplikaciju. Napravite izmjenu u `index.html`, build-ujete Docker image ručno, logujete se na server, povlačite image, restartujete kontejner. Svaki put. Isti postupak. Ako pogriješite u jednom koraku — greška ide u produkciju bez provjere.

To je **manual deploy**. Skalira loše, greškama je sklon, i blokira tim jer samo onaj ko "zna komande" može deploovati.

**Continuous Integration (CI)** automatizuje provjeru koda: svaki push pokreće build i testove.
**Continuous Deployment (CD)** automatizuje isporuku: ako testovi prođu, kod ide na okruženje.

Rezultat: svaki developer može pushati kod i sigurno znati da će sistem provjeriti ispravnost i isporučiti ga — bez ručnog rada.

## Zašto GitLab CI za ovaj projekat

Postoje tri dominantna alata:

**Jenkins** — najstariji, nevjerovatno fleksibilan, ali zahtijeva zasebni server, kompleksnu konfiguraciju i mnogo održavanja. Previše overhead-a za novi projekat.

**GitHub Actions** — odlična integracija s GitHub-om, dobra zajednica. Ali koristimo GitLab za hosting koda i Container Registry, pa bi Actions značio rad između dva sistema.

**GitLab CI/CD** — ugrađen direktno u GitLab. Isti sistem gdje živi kod, container registry, merge requestovi, environments. Nema integracija koje treba podešavati. Pipeline konfiguracija je fajl u repou, verzionisan zajedno s kodom.

Za project-A: kod je na GitLab-u, image ide u GitLab Container Registry, pipeline je GitLab CI. Jedan sistem, nula eksternih dependency-ja.

## Anatomija pipeline-a

Kada napravite push, GitLab čita `.gitlab-ci.yml` iz korijena repoa i pokreće pipeline. Tok je uvijek isti:

```
TRIGGER → STAGES → JOBS → ARTIFACTS
```

**Trigger** — šta je pokrenulo pipeline: push na branch, merge request, ručno pokretanje, raspored (scheduled).

**Stages** — faze koje se izvršavaju sekvencijalno. Dok jedan stage ne završi (uspješno), sljedeći ne počinje. Tipično: `build → test → deploy`.

**Jobs** — konkretni zadaci unutar stage-a. Svi jobovi unutar istog stage-a izvršavaju se **paralelno** (ako ima dostupnih runnera). Job je ono što zapravo radi posao: izvršava shell komande unutar Docker kontejnera.

**Artifacts** — fajlovi koje job proizvede i preda dalje. Build job napravi Docker image i spremi digest, test job ga koristi, deploy job uzima taj isti image.

## GitLab Runner: izvršilac posla

GitLab Runner je zasebni proces koji čeka na poslove od GitLab-a i izvršava ih. GitLab.com nudi **shared runners** — slobodni resursi koje možete koristiti bez vlastitog servera.

Kada job počne, runner:
1. Povuče Docker image naveden u `image:` ključu joba
2. Pokrene kontejner
3. Klonira repo unutar kontejnera
4. Izvrši komande iz `script:`
5. Prikupi artifacts
6. Uništi kontejner

**Docker executor** znači da svaki job dobija svježi, čist kontejner. Nema zagađenja između jobova, nema "radi na mom računaru" problema. Kontejner se pokrene, uradi posao, nestane.

Važno razumjeti: runner ne pamti stanje između jobova (osim kroz artifacts i cache). Svaki job počinje od nule.

## Veza sa project-A

Svaki push na bilo koji branch pokreće pipeline za hello-world aplikaciju:

```
push index.html izmjene
    ↓
build job: docker build → image u registry
    ↓
test job: docker run → curl → provjeri HTTP 200
    ↓
deploy job: kubectl apply → ažuriraj K8s deployment
```

Na `main` branchu deploy ide na staging i (nakon odobravanja) prod. Na feature branchevima pipeline se zaustavi na testu — nema automatskog deploya. Na merge requestovima se kreira review environment (vidjet ćemo u kasnijim modulima).

Svaki inženjer u timu pushuje kod i pipeline garantuje da loš kod ne dođe do korisnika.
