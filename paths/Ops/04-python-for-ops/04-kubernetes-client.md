# Python for ops — `04` Kubernetes Python client

**Zasto:** `kubectl` u bash skripti je dovoljno za 80% slučajeva. Python K8s client trebaš kad logika postane složena — filtriranje po više kriterija, reagovanje na stanje clustera, custom automation koja kubectl teško izražava.

---

## Setup i konekcija

```python
from kubernetes import client, config, watch

# Iz lokalnog kubeconfig (~/.kube/config)
config.load_kube_config()

# Iz in-cluster service accounta (u K8s podu)
# config.load_incluster_config()

# API klijenti — po grupi resursa
v1      = client.CoreV1Api()       # pods, services, configmaps, secrets, nodes
apps_v1 = client.AppsV1Api()       # deployments, statefulsets, daemonsets
batch   = client.BatchV1Api()      # jobs, cronjobs
```

---

## Čitanje stanja clustera

```python
# Lista podova
pods = v1.list_namespaced_pod(namespace="production")
for pod in pods.items:
    name    = pod.metadata.name
    phase   = pod.status.phase
    node    = pod.spec.node_name
    ready   = all(c.ready for c in (pod.status.conditions or []) if c.type == "Ready")
    print(f"{name:40} {phase:10} {node}")

# Filter po labelu
pods = v1.list_namespaced_pod(
    namespace="production",
    label_selector="app=myapp,version=v2"
)

# Restartovi i problemi
def find_crashing_pods(namespace: str) -> list[dict]:
    problems = []
    pods = v1.list_namespaced_pod(namespace=namespace)
    
    for pod in pods.items:
        for container in (pod.status.container_statuses or []):
            if container.restart_count > 5:
                problems.append({
                    "pod":      pod.metadata.name,
                    "container": container.name,
                    "restarts": container.restart_count,
                    "state":    str(container.state),
                })
    return problems

# Logovi
logs = v1.read_namespaced_pod_log(
    name="myapp-abc123",
    namespace="production",
    tail_lines=100,
    container="app",  # ako pod ima više containera
)
print(logs)
```

---

## Update deploymenta

```python
def update_image(deployment: str, namespace: str, new_image: str, dry_run: bool = False) -> None:
    """Zamijeni image u prvom containeru deploymenta."""
    
    # Čitaj trenutno stanje
    dep = apps_v1.read_namespaced_deployment(name=deployment, namespace=namespace)
    old_image = dep.spec.template.spec.containers[0].image
    
    print(f"{deployment}: {old_image} → {new_image}")
    
    if dry_run:
        print("DRY-RUN: nije primijenjeno")
        return
    
    # Patch — samo šalje razliku
    patch = {
        "spec": {
            "template": {
                "spec": {
                    "containers": [{"name": dep.spec.template.spec.containers[0].name, "image": new_image}]
                }
            }
        }
    }
    apps_v1.patch_namespaced_deployment(name=deployment, namespace=namespace, body=patch)
    print("Patch primijenjen")


def wait_rollout(deployment: str, namespace: str, timeout: int = 300) -> None:
    """Čekaj da rollout završi — polling na deployment status."""
    import time
    deadline = time.time() + timeout
    
    while time.time() < deadline:
        dep = apps_v1.read_namespaced_deployment(name=deployment, namespace=namespace)
        desired    = dep.spec.replicas
        updated    = dep.status.updated_replicas or 0
        available  = dep.status.available_replicas or 0
        
        print(f"  updated={updated}/{desired}, available={available}/{desired}")
        
        if updated == desired and available == desired:
            print("Rollout završen")
            return
        
        time.sleep(10)
    
    raise TimeoutError(f"Rollout nije završen za {timeout}s")
```

---

## Watch — reaguj na promjene u clusteru

```python
def watch_pods(namespace: str, label_selector: str) -> None:
    """Stream eventova o podovima — korisno za monitoring i debugging."""
    w = watch.Watch()
    
    for event in w.stream(
        v1.list_namespaced_pod,
        namespace=namespace,
        label_selector=label_selector,
        timeout_seconds=300,
    ):
        event_type = event["type"]         # ADDED, MODIFIED, DELETED
        pod = event["object"]
        phase = pod.status.phase
        name = pod.metadata.name
        
        print(f"{event_type}: {name} ({phase})")
        
        if phase == "Failed":
            print(f"  ALERT: Pod {name} pao!")
            # Pošalji notifikaciju, uzmi logove...
```

---

## Čišćenje starih jobova

```python
def cleanup_completed_jobs(namespace: str, dry_run: bool = False) -> int:
    """Briši završene K8s jobove — čest maintenance task."""
    jobs = batch.list_namespaced_job(namespace=namespace)
    deleted = 0
    
    for job in jobs.items:
        succeeded = job.status.succeeded or 0
        if succeeded > 0:
            print(f"Brišem završeni job: {job.metadata.name}")
            
            if not dry_run:
                batch.delete_namespaced_job(
                    name=job.metadata.name,
                    namespace=namespace,
                    body=client.V1DeleteOptions(propagation_policy="Foreground"),
                )
            deleted += 1
    
    return deleted
```

---

## Vjezba

Napiši `cluster-health.py` sa Click CLI-em:
- Komanda `pods` — ispiši tabelu: namespace, ime, status, restartovi, node; sortiramo po restartima
- Komanda `images` — listu svih unique imaga u clusteru (svi deploymenti, svi namespacei)
- Komanda `cleanup-jobs` — briši completed jobove, `--dry-run` podrška
- Ako nađeš pod s > 10 restartatova, ispiši zadnjih 50 linija loga i upozorenje
