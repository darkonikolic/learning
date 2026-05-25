# Python for ops — `02` Fajlovi, env, subprocess i data

**Zasto:** Svaka ops skripta čita konfiguraciju, parsuje JSON/YAML iz alata, i poziva shell komande. Ovo su osnove koje koristiš u svakom scriptu — naučiti ih jednom i koristiti svugdje.

---

## Env varijable

```python
import os
import sys

# Čitanje — nikad nemoj hardkodovati credentialse
db_host = os.environ["DB_HOST"]                         # Exception ako nije postavljeno
db_port = int(os.environ.get("DB_PORT", "5432"))        # Default vrijednost
api_token = os.environ.get("API_TOKEN")                 # None ako nije postavljeno

# Validacija na početku skripte
REQUIRED_ENV = ["DB_HOST", "APP_ENV", "IMAGE_TAG"]

def validate_env() -> None:
    missing = [var for var in REQUIRED_ENV if not os.environ.get(var)]
    if missing:
        print(f"ERROR: Nedostaju env varijable: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
```

---

## Fajlovi sa pathlib

```python
from pathlib import Path

# Osnove
p = Path("/opt/app/config")
p.exists()              # True/False
p.is_file()             # True/False
p.is_dir()              # True/False

# Čitanje i pisanje
content = Path("config.yaml").read_text()
Path("output.json").write_text('{"status": "ok"}')

# mkdir
Path("/opt/app/logs").mkdir(parents=True, exist_ok=True)  # uvijek exist_ok=True

# Glob
for log_file in Path("/var/log/app").glob("*.log"):
    print(log_file.name, log_file.stat().st_size)

# Relativno od skripte
SCRIPT_DIR = Path(__file__).parent
MANIFEST = SCRIPT_DIR / ".." / "deploy" / "deployment.yaml"
```

---

## JSON i YAML

```python
import json
import yaml  # pip install pyyaml

# JSON — iz string ili fajla
data = json.loads('{"status": "running", "replicas": 3}')
data = json.load(open("response.json"))
print(json.dumps(data, indent=2))

# Realni primjer — parsovanje kubectl outputa
import subprocess
result = subprocess.run(
    ["kubectl", "get", "deployment", "myapp", "-o", "json"],
    capture_output=True, text=True, check=True
)
deployment = json.loads(result.stdout)
image = deployment["spec"]["template"]["spec"]["containers"][0]["image"]
replicas = deployment["status"]["readyReplicas"]
print(f"Image: {image}, Ready: {replicas}")

# YAML — uvijek safe_load, nikad load (sigurnosni rizik)
with open("values.yaml") as f:
    values = yaml.safe_load(f)

values["image"]["tag"] = "v1.2.3"

with open("values.yaml", "w") as f:
    yaml.dump(values, f, default_flow_style=False)
```

---

## subprocess — pokretanje komandi

```python
import subprocess

# Osnova — capture_output=True da uhvatiš stdout/stderr
result = subprocess.run(
    ["kubectl", "get", "pods", "-n", "production"],
    capture_output=True,
    text=True,        # decode bytes → str automatski
    check=False       # ne baci exception na non-zero (mi provjeravamo ručno)
)

if result.returncode != 0:
    print(f"ERROR: kubectl failed:\n{result.stderr}", file=sys.stderr)
    sys.exit(1)

print(result.stdout)

# check=True — baci CalledProcessError na non-zero
try:
    result = subprocess.run(
        ["docker", "push", f"registry.example.com/myapp:{tag}"],
        capture_output=True, text=True, check=True
    )
except subprocess.CalledProcessError as e:
    print(f"Docker push failed: {e.stderr}", file=sys.stderr)
    sys.exit(1)

# NIKAD shell=True s korisničkim inputom — injection risk
# GREŠKA:
subprocess.run(f"kubectl delete pod {pod_name}", shell=True)  # injection ako pod_name = "x; rm -rf /"

# ISPRAVNO — lista argumenata
subprocess.run(["kubectl", "delete", "pod", pod_name], check=True)

# Čitanje jedne vrijednosti
sha = subprocess.run(
    ["git", "rev-parse", "--short", "HEAD"],
    capture_output=True, text=True, check=True
).stdout.strip()
```

---

## HTTP sa requests

```python
import requests

# GET sa timeoutom (uvijek postavi timeout!)
response = requests.get("https://api.example.com/health", timeout=10)
response.raise_for_status()  # baci exception za 4xx/5xx
data = response.json()

# POST JSON
response = requests.post(
    "https://hooks.slack.com/services/...",
    json={"text": "Deploy uspješan: v1.2.3 na staging"},
    timeout=10
)
response.raise_for_status()

# Auth
response = requests.get(
    "https://api.example.com/v1/pods",
    headers={"Authorization": f"Bearer {api_token}"},
    timeout=10
)

# Health check s retry
def wait_healthy(url: str, retries: int = 5, delay: int = 10) -> bool:
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                return True
        except requests.RequestException:
            pass
        
        if attempt < retries:
            import time
            time.sleep(delay)
    
    return False
```

---

## Vjezba

Napiši `manifest-updater.py`:
- Prima kao argumente: path do `deployment.yaml`, novi image tag
- Čita YAML, updateuje `spec.template.spec.containers[0].image` tag
- Validira da fajl postoji i da ima očekivanu strukturu (baci jasnu grešku ako ne)
- Pokrenuti `kubectl apply -f` na updateovanom fajlu putem subprocess
- Sačekati da rollout završi: `kubectl rollout status` (timeout 120s)
- Logging na stderr, exit 0/1
