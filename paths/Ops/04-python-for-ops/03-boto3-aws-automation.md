# Python for ops — `03` boto3: AWS automation

**Zasto:** Svaka AWS akcija koju radiš kliktanjem u konzoli može biti Python skripta u CI pipelinu. boto3 je zvanični AWS SDK za Python i temelj svakog ops automatizacije na AWS-u.

---

## Auth i session — osnova svega

```python
import boto3
import botocore.exceptions

# Kako boto3 traži credentials (prioritet):
# 1. Env varijable: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
# 2. ~/.aws/credentials (profili)
# 3. IAM instance role (EC2)
# 4. ECS task role
# 5. EKS pod role (IRSA)

# U produkciji NIKAD ne stavljaj ključeve u kod ili env varijable
# Koristiti IAM role (instance/task/pod role)

# Eksplicitna session — preporučeno, izbjegava globalni state
session = boto3.Session(
    region_name="eu-central-1",
    profile_name="staging",  # ~/.aws/credentials profil (samo lokalno)
)

ec2 = session.client("ec2")
s3  = session.client("s3")
ecs = session.client("ecs")

# Assume role — cross-account ili privilegovane operacije
def assume_role(role_arn: str, session_name: str = "ops-script") -> boto3.Session:
    sts = boto3.client("sts")
    creds = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
    )["Credentials"]
    
    return boto3.Session(
        aws_access_key_id=creds["AccessKeyId"],
        aws_secret_access_key=creds["SecretAccessKey"],
        aws_session_token=creds["SessionToken"],
    )
```

---

## Error handling — isti pattern za sve servise

```python
from botocore.exceptions import ClientError, NoCredentialsError

def safe_call(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except NoCredentialsError:
        print("ERROR: AWS credentials nisu konfigurisani", file=sys.stderr)
        sys.exit(2)
    except ClientError as e:
        code = e.response["Error"]["Code"]
        msg  = e.response["Error"]["Message"]
        print(f"ERROR: AWS API error [{code}]: {msg}", file=sys.stderr)
        raise

# Specifična greška — branch po kodu
try:
    s3.head_bucket(Bucket=bucket_name)
except ClientError as e:
    if e.response["Error"]["Code"] == "404":
        print(f"Bucket {bucket_name} ne postoji")
    elif e.response["Error"]["Code"] == "403":
        print(f"Nemaš pristup bucketu {bucket_name}")
    else:
        raise
```

---

## EC2 — najčešće operacije

```python
# Lista instanci sa filterima
def list_instances(env: str, session: boto3.Session) -> list[dict]:
    ec2 = session.client("ec2")
    paginator = ec2.get_paginator("describe_instances")
    
    instances = []
    for page in paginator.paginate(
        Filters=[
            {"Name": "tag:Environment", "Values": [env]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    ):
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                instances.append({
                    "id":         inst["InstanceId"],
                    "private_ip": inst.get("PrivateIpAddress", ""),
                    "state":      inst["State"]["Name"],
                    "tags":       {t["Key"]: t["Value"] for t in inst.get("Tags", [])},
                })
    return instances

# Stop instanci i čekanje
def stop_instances(instance_ids: list[str], session: boto3.Session) -> None:
    ec2 = session.client("ec2")
    ec2.stop_instances(InstanceIds=instance_ids)
    
    waiter = ec2.get_waiter("instance_stopped")
    waiter.wait(InstanceIds=instance_ids)
    print(f"Stopovano: {instance_ids}")
```

---

## S3 — backup i artefakti

```python
from datetime import datetime

def upload_backup(local_path: str, bucket: str, prefix: str, session: boto3.Session) -> str:
    s3 = session.client("s3")
    
    timestamp = datetime.utcnow().strftime("%Y/%m/%d")
    filename = Path(local_path).name
    key = f"{prefix}/{timestamp}/{filename}"
    
    s3.upload_file(
        local_path,
        bucket,
        key,
        ExtraArgs={"ServerSideEncryption": "AES256"},
    )
    print(f"Uploadovano: s3://{bucket}/{key}")
    return key

def cleanup_old_backups(bucket: str, prefix: str, keep_days: int, session: boto3.Session) -> int:
    s3 = session.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    
    cutoff = datetime.utcnow().timestamp() - (keep_days * 86400)
    to_delete = []
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            if obj["LastModified"].timestamp() < cutoff:
                to_delete.append({"Key": obj["Key"]})
    
    if to_delete:
        # Batch delete, max 1000 po pozivu
        for i in range(0, len(to_delete), 1000):
            s3.delete_objects(Bucket=bucket, Delete={"Objects": to_delete[i:i+1000]})
    
    return len(to_delete)
```

---

## ECS — deploy i monitoring

```python
def force_deploy(cluster: str, service: str, session: boto3.Session) -> None:
    ecs = session.client("ecs")
    ecs.update_service(
        cluster=cluster,
        service=service,
        forceNewDeployment=True,
    )
    print(f"Deploy pokrenut: {cluster}/{service}")

def wait_stable(cluster: str, service: str, session: boto3.Session, timeout: int = 300) -> None:
    import time
    ecs = session.client("ecs")
    
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = ecs.describe_services(cluster=cluster, services=[service])
        svc = resp["services"][0]
        
        running  = svc["runningCount"]
        desired  = svc["desiredCount"]
        deploys  = len(svc["deployments"])
        
        print(f"  running={running}/{desired}, deployments={deploys}")
        
        if running == desired and deploys == 1:
            print("Servis je stabilan")
            return
        
        time.sleep(10)
    
    raise TimeoutError(f"Servis nije stabilan nakon {timeout}s")

# Secrets Manager
def get_secret(secret_id: str, session: boto3.Session) -> dict:
    sm = session.client("secretsmanager")
    response = sm.get_secret_value(SecretId=secret_id)
    return json.loads(response["SecretString"])
```

---

## Vjezba

Napiši `aws-cleanup.py` sa Click CLI-em:
- Komanda `list-stopped` — lista sve stopovane EC2 instance u env-u (tag `Environment`)
- Komanda `terminate-old` — terminira stopovane instance starije od `--days` (default: 7), sa `--dry-run` opcionom
- Komanda `backup-logs` — uploaduje sve `.log` fajlove iz direktorija na S3, briše lokalne kopije starije od 3 dana
- Proper error handling za ClientError, logging, exit kodovi
