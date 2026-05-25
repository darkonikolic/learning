# Python for ops — `01` Setup, skeleton i CLI

**Zasto:** Python za ops se ne piše kao aplikacija — nema frejmvorka, nema klasa za sve, nema 10 fajlova. Pišeš skriptu koja ima jasan ulazni tačku, čita argumente, radi stvar, vraća exit kod. Ovo je šablon koji koristiš za svaki ops script.

---

## Setup: venv i requirements

```bash
# Napravi projekat
mkdir ops-scripts && cd ops-scripts
python3 -m venv .venv
source .venv/bin/activate

# requirements.txt — pin verzije za reproducibilnost
cat > requirements.txt <<EOF
boto3==1.34.0
requests==2.31.0
pyyaml==6.0.1
click==8.1.7
kubernetes==28.1.0
python-json-logger==2.0.7
EOF

pip install -r requirements.txt
```

U CI:
```yaml
# .gitlab-ci.yml
deploy:
  image: python:3.11-slim
  before_script:
    - pip install -r requirements.txt
  script:
    - python scripts/deploy.py --env staging --tag $CI_COMMIT_SHA
```

---

## Minimalni šablon za ops skriptu

```python
#!/usr/bin/env python3
"""
deploy.py — deploys application to Kubernetes
"""
import sys
import logging

import click


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,  # stderr — ne zagađuj stdout
    )

log = logging.getLogger(__name__)


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
@click.option("--verbose", is_flag=True, help="Debug output")
def cli(verbose: bool) -> None:
    setup_logging(verbose)


@cli.command()
@click.option("--env",   required=True, type=click.Choice(["staging", "production"]))
@click.option("--tag",   required=True, help="Docker image tag")
@click.option("--dry-run", is_flag=True, help="Print actions, don't execute")
def deploy(env: str, tag: str, dry_run: bool) -> None:
    """Deploy application to Kubernetes."""
    log.info("Deploying %s to %s (dry_run=%s)", tag, env, dry_run)
    
    if dry_run:
        log.info("DRY-RUN: would apply deployment with tag %s", tag)
        return
    
    # ... logika
    log.info("Deploy successful")


@cli.command()
@click.option("--env", required=True, type=click.Choice(["staging", "production"]))
def rollback(env: str) -> None:
    """Rollback to previous deployment."""
    log.info("Rolling back %s", env)
    # ... logika


# ─── Entry point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
```

```bash
# Pokretanje
python deploy.py deploy --env staging --tag v1.2.3
python deploy.py deploy --env staging --tag v1.2.3 --dry-run
python deploy.py --help
python deploy.py deploy --help
```

---

## Click osnove — sve što trebaš za ops

```python
# Obavezna opcija s validacijom
@click.option("--env", required=True, type=click.Choice(["staging", "production"]))

# Opcija s defaultom
@click.option("--namespace", default="default", show_default=True)

# Flag (boolean)
@click.option("--dry-run", is_flag=True)

# Opcija koja čita iz env varijable ako nije proslijeđena
@click.option("--token", envvar="API_TOKEN", help="API token (ili API_TOKEN env var)")

# Obavezni argument (positional)
@click.argument("filename")

# Više vrijednosti
@click.option("--tag", multiple=True)  # --tag v1 --tag v2
```

---

## Exit kodovi iz Clicka

```python
@cli.command()
def deploy(...):
    try:
        do_deploy()
    except DeployError as e:
        log.error("Deploy failed: %s", e)
        sys.exit(1)
    except ConfigError as e:
        log.error("Config error: %s", e)
        sys.exit(2)
```

CI čita exit kod — `sys.exit(1)` označava job kao neuspješan.

---

## Vjezba

Napiši `service-check.py` sa Click CLI-em:
- Komanda `check` — prima `--url` (više puta) i `--timeout` (default: 5s)
- Za svaki URL: HTTP GET, ispiši `[OK] url` ili `[FAIL] url (status 503)`
- Komanda `report` — čita listu URLova iz YAML fajla (`urls: [...]`) i radi isti check
- Izlazi s kodom 1 ako ijedan URL ne odgovara
- Logging na stderr, `[OK]/[FAIL]` linije na stdout
