# Python for ops — `06` Integration project: deploy alat

**Zasto:** Sve prethodne lekcije su fragmenti. Ovdje ih spajamo u jedan alat koji se zaista koristi na poslu — CLI sa više komandi, boto3, K8s client, health check, notifikacije, testovi.

---

## Šta alat radi

`deploy-tool.py` — kompletni deploy alat:
- `deploy` — deploya na ECS Fargate ili K8s (konfiguriše se po env-u)
- `rollback` — vraća na prethodnu verziju
- `status` — ispiši stanje servisa

---

## Kompletna implementacija

```python
#!/usr/bin/env python3
"""deploy-tool.py — Application deployment tool"""

import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Optional

import boto3
import click
import requests
import yaml
from botocore.exceptions import ClientError, NoCredentialsError
from kubernetes import client as k8s_client, config as k8s_config


# ─── Exceptions ───────────────────────────────────────────────────────────────

class DeployError(Exception): pass
class ConfigError(Exception): pass
class HealthCheckError(Exception): pass


# ─── Logging ──────────────────────────────────────────────────────────────────

def setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )

log = logging.getLogger(__name__)


# ─── Config ───────────────────────────────────────────────────────────────────

ENV_CONFIG = {
    "staging": {
        "platform":   "ecs",
        "cluster":    "staging-cluster",
        "service":    "myapp-staging",
        "region":     "eu-central-1",
        "health_url": "https://staging.example.com/health",
    },
    "production": {
        "platform":   "k8s",
        "namespace":  "production",
        "deployment": "myapp",
        "health_url": "https://app.example.com/health",
    },
}

def get_config(env: str) -> dict:
    if env not in ENV_CONFIG:
        raise ConfigError(f"Nepoznat env: {env}. Dostupni: {list(ENV_CONFIG)}")
    return ENV_CONFIG[env]


# ─── Health check ─────────────────────────────────────────────────────────────

def wait_healthy(url: str, retries: int = 5, delay: int = 10) -> None:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                log.info("Health check OK (%s)", url)
                return
            log.warning("Health check attempt %d/%d: status %d", attempt, retries, r.status_code)
        except requests.RequestException as e:
            log.warning("Health check attempt %d/%d: %s", attempt, retries, e)
        
        if attempt < retries:
            time.sleep(delay)
    
    raise HealthCheckError(f"Servis nije zdrav nakon {retries} pokušaja: {url}")


# ─── Slack notifikacija ───────────────────────────────────────────────────────

def notify(message: str, success: bool = True) -> None:
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    
    color = "#36a64f" if success else "#d32f2f"
    payload = {
        "attachments": [{
            "color": color,
            "text": message,
            "footer": "deploy-tool",
        }]
    }
    
    try:
        requests.post(webhook, json=payload, timeout=5)
    except requests.RequestException:
        log.warning("Slack notifikacija neuspješna")


# ─── ECS deploy ───────────────────────────────────────────────────────────────

def deploy_ecs(tag: str, cfg: dict, dry_run: bool) -> None:
    session = boto3.Session(region_name=cfg["region"])
    ecs = session.client("ecs")
    
    log.info("ECS deploy: %s/%s → %s", cfg["cluster"], cfg["service"], tag)
    
    # Uzmi task definition da updateujemo image
    svc = ecs.describe_services(cluster=cfg["cluster"], services=[cfg["service"]])["services"][0]
    task_def_arn = svc["taskDefinition"]
    task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)["taskDefinition"]
    
    # Update image u task definition
    containers = task_def["containerDefinitions"]
    containers[0]["image"] = f"{containers[0]['image'].rsplit(':', 1)[0]}:{tag}"
    
    if dry_run:
        log.info("DRY-RUN: would register new task definition and update service")
        return
    
    # Registruj novu task definition
    new_td = ecs.register_task_definition(
        family=task_def["family"],
        containerDefinitions=containers,
        cpu=task_def["cpu"],
        memory=task_def["memory"],
        networkMode=task_def["networkMode"],
        requiresCompatibilities=task_def.get("requiresCompatibilities", []),
        executionRoleArn=task_def.get("executionRoleArn"),
        taskRoleArn=task_def.get("taskRoleArn"),
    )["taskDefinition"]["taskDefinitionArn"]
    
    ecs.update_service(
        cluster=cfg["cluster"],
        service=cfg["service"],
        taskDefinition=new_td,
    )
    
    # Čekaj stabilan state
    log.info("Čekam stabilan ECS servis...")
    deadline = time.time() + 300
    while time.time() < deadline:
        svc = ecs.describe_services(cluster=cfg["cluster"], services=[cfg["service"]])["services"][0]
        running  = svc["runningCount"]
        desired  = svc["desiredCount"]
        deploys  = len(svc["deployments"])
        log.debug("running=%d/%d, deployments=%d", running, desired, deploys)
        
        if running == desired and deploys == 1:
            break
        time.sleep(10)
    else:
        raise DeployError("ECS servis nije stabilan nakon 5min")


# ─── K8s deploy ───────────────────────────────────────────────────────────────

def deploy_k8s(tag: str, cfg: dict, dry_run: bool) -> None:
    k8s_config.load_kube_config()
    apps = k8s_client.AppsV1Api()
    
    dep = apps.read_namespaced_deployment(
        name=cfg["deployment"],
        namespace=cfg["namespace"]
    )
    
    old_image = dep.spec.template.spec.containers[0].image
    new_image = f"{old_image.rsplit(':', 1)[0]}:{tag}"
    
    log.info("K8s deploy: %s → %s", old_image, new_image)
    
    if dry_run:
        log.info("DRY-RUN: would patch deployment %s", cfg["deployment"])
        return
    
    patch = {"spec": {"template": {"spec": {"containers": [
        {"name": dep.spec.template.spec.containers[0].name, "image": new_image}
    ]}}}}
    
    apps.patch_namespaced_deployment(
        name=cfg["deployment"],
        namespace=cfg["namespace"],
        body=patch
    )
    
    result = subprocess.run(
        ["kubectl", "rollout", "status", f"deployment/{cfg['deployment']}",
         "-n", cfg["namespace"], "--timeout=5m"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise DeployError(f"Rollout neuspješan: {result.stderr}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

@click.group()
@click.option("--verbose", is_flag=True)
def cli(verbose: bool) -> None:
    setup_logging(verbose)


@cli.command()
@click.option("--env",     required=True, type=click.Choice(["staging", "production"]))
@click.option("--tag",     required=True)
@click.option("--dry-run", is_flag=True)
def deploy(env: str, tag: str, dry_run: bool) -> None:
    """Deploy novu verziju aplikacije."""
    try:
        cfg = get_config(env)
        
        if cfg["platform"] == "ecs":
            deploy_ecs(tag, cfg, dry_run)
        else:
            deploy_k8s(tag, cfg, dry_run)
        
        if not dry_run and cfg.get("health_url"):
            wait_healthy(cfg["health_url"])
        
        msg = f"✓ Deploy uspješan: `{tag}` na `{env}`"
        log.info(msg)
        notify(msg, success=True)
    
    except (DeployError, HealthCheckError) as e:
        log.error("Deploy neuspješan: %s", e)
        notify(f"✗ Deploy neuspješan na `{env}`: {e}", success=False)
        sys.exit(1)
    
    except ConfigError as e:
        log.error("Config greška: %s", e)
        sys.exit(2)


@cli.command()
@click.option("--env", required=True, type=click.Choice(["staging", "production"]))
def status(env: str) -> None:
    """Prikaži stanje servisa."""
    cfg = get_config(env)
    
    if cfg["platform"] == "ecs":
        session = boto3.Session(region_name=cfg["region"])
        ecs = session.client("ecs")
        svc = ecs.describe_services(
            cluster=cfg["cluster"], services=[cfg["service"]]
        )["services"][0]
        print(json.dumps({
            "env":     env,
            "running": svc["runningCount"],
            "desired": svc["desiredCount"],
            "status":  svc["status"],
        }, indent=2))
    else:
        k8s_config.load_kube_config()
        apps = k8s_client.AppsV1Api()
        dep = apps.read_namespaced_deployment(
            name=cfg["deployment"], namespace=cfg["namespace"]
        )
        print(json.dumps({
            "env":       env,
            "available": dep.status.available_replicas,
            "desired":   dep.spec.replicas,
            "image":     dep.spec.template.spec.containers[0].image,
        }, indent=2))


if __name__ == "__main__":
    cli()
```

---

## Vjezba

1. Pokreni `deploy --env staging --tag v1.0.0 --dry-run` — provjeri da ništa nije pozvano
2. Napiši 4 unit testa: deploy_ecs zove update_service, wait_healthy uspijeva na 3. pokušaju, ConfigError za nepoznat env, rollback poziva rollout undo
3. Dodaj `rollback` komandu koja poziva `kubectl rollout undo` ili ECS rollback na prethodnu task definition
4. Napiši `.gitlab-ci.yml` job koji poziva `deploy --env staging --tag $CI_COMMIT_SHA` i `deploy --env production --tag $CI_COMMIT_TAG` (samo na tagove)
