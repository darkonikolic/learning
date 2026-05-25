# Python for ops — `05` Error handling, logging i testiranje skripti

**Zasto:** Ops skripta koja pukne s `KeyError: 'InstanceId'` u 2 ujutro je problem. Dobro structurirani error handling znači da greška kaže gdje je nastala, zašto, i šta je skripta pokušala da uradi. Testovi znače da možeš refaktorisati bez straha.

---

## Error handling — specifičan, ne generalan

```python
# LOŠE — hvata sve, skriva pravi problem
try:
    do_deploy()
except Exception as e:
    print(f"Greška: {e}")
    sys.exit(1)

# DOBRO — specifične greške, jasne poruke
from botocore.exceptions import ClientError, NoCredentialsError
import subprocess

class DeployError(Exception):
    """Deployment neuspješan."""

class ConfigError(Exception):
    """Pogrešna konfiguracija ili nedostaju env varijable."""

def deploy(env: str, tag: str) -> None:
    try:
        _update_ecs_service(env, tag)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        raise DeployError(f"ECS update neuspješan [{code}]: {e}") from e
    except subprocess.CalledProcessError as e:
        raise DeployError(f"kubectl komanda pala (exit {e.returncode}): {e.stderr}") from e

def main():
    try:
        deploy(env, tag)
    except ConfigError as e:
        log.error("Konfiguracija: %s", e)
        sys.exit(2)
    except DeployError as e:
        log.error("Deploy neuspješan: %s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        log.warning("Prekinuto")
        sys.exit(130)
```

---

## Logging — strukturiran i koristan

```python
import logging
import sys
from pythonjsonlogger import jsonlogger  # pip install python-json-logger

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    
    handler = logging.StreamHandler(sys.stderr)
    
    # Produkcija — JSON format koji Loki može parsovati
    if os.environ.get("LOG_FORMAT") == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    else:
        # Lokalno — čitljiv format
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)-8s %(message)s",
            datefmt="%H:%M:%S",
        )
    
    handler.setFormatter(formatter)
    logging.basicConfig(level=level, handlers=[handler])

log = logging.getLogger(__name__)

# Upotreba — uvijek s kontekstom, ne samo s porukom
log.info("Pokrećem deploy", extra={"env": env, "tag": tag})
log.warning("Health check neuspješan, pokušavam ponovo", extra={"attempt": 2, "url": url})
log.error("Deploy pao", extra={"error": str(e), "service": service_name})
```

---

## Context manager za cleanup

```python
import tempfile
import shutil
from contextlib import contextmanager

@contextmanager
def temp_workspace():
    """Temp direktorij koji se uvijek briše, i na grešci."""
    tmpdir = tempfile.mkdtemp(prefix="ops-deploy-")
    try:
        yield Path(tmpdir)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

# Upotreba
def deploy_with_manifest(tag: str) -> None:
    with temp_workspace() as workspace:
        manifest = workspace / "deployment.yaml"
        shutil.copy("deploy/deployment.yaml", manifest)
        
        # yq update
        subprocess.run(
            ["yq", "-i", f'.spec.template.spec.containers[0].image |= sub(":.*", ":{tag}")', str(manifest)],
            check=True
        )
        
        subprocess.run(["kubectl", "apply", "-f", str(manifest)], check=True)
    # tmpdir je već obrisan čak i ako subprocess pukne
```

---

## Testiranje ops skripti

Ops skripte nisu aplikacije, ali se mogu testirati. Cilj: testirati logiku bez pozivanja AWS/kubectl.

```python
# tests/test_deploy.py
import pytest
from unittest.mock import MagicMock, patch

# Testiraj logiku, mock-aj external calls
def test_validate_env_missing():
    with pytest.raises(SystemExit) as exc:
        with patch.dict("os.environ", {}, clear=True):
            validate_env()
    assert exc.value.code == 2

def test_deploy_updates_correct_image():
    mock_ecs = MagicMock()
    
    with patch("boto3.Session") as mock_session:
        mock_session.return_value.client.return_value = mock_ecs
        
        deploy_to_ecs("staging", "v1.2.3")
        
        mock_ecs.update_service.assert_called_once_with(
            cluster="staging-cluster",
            service="myapp",
            forceNewDeployment=True,
        )

def test_wait_stable_succeeds():
    mock_ecs = MagicMock()
    mock_ecs.describe_services.return_value = {
        "services": [{
            "runningCount": 2,
            "desiredCount": 2,
            "deployments": [{"status": "PRIMARY"}],
        }]
    }
    
    # Ne smije baciti exception
    wait_stable("cluster", "service", mock_ecs, timeout=30)

# Pokretanje
# pytest tests/ -v
```

---

## Vjezba

Uzmi `aws-cleanup.py` iz prethodne lekcije i:
1. Dodaj custom exception klase: `AWSError`, `ConfigError`
2. Refaktoriši error handling — nikad goli `except Exception`
3. Dodaj JSON logging kad je `LOG_FORMAT=json` u env-u
4. Napiši 3 testa za `terminate-old` logiku koristeći mock boto3 — testiraj: dry-run ne terminira, instance mlađe od `--days` se preskačaju, error handling za ClientError
