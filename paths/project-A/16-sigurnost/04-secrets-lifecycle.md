# 04 — Secrets Lifecycle

## Secrets audit — ko ima pristup čemu

Secrets lifecycle pokriva više od pohrane i rotacije: uključuje vidljivost, praćenje pristupa, i sposobnost brzog odgovora na incident.

### AWS SM permissions audit

```bash
#!/bin/bash
# scripts/audit-secret-access.sh
# Izvještaj: ko može čitati koji SM secret

SECRET_PREFIX="/project-a/prod"

# Listati sve secrets sa rotation statusom
aws secretsmanager list-secrets \
    --filters "[{\"Key\":\"name\",\"Values\":[\"$SECRET_PREFIX\"]}]" \
    --query 'SecretList[*].{Name:Name,RotationEnabled:RotationEnabled,LastRotated:LastRotatedDate}' \
    --output table

# Za svaki secret — listati ko ima GetSecretValue pristup
for SECRET_ARN in $(aws secretsmanager list-secrets \
    --filters "[{\"Key\":\"name\",\"Values\":[\"$SECRET_PREFIX\"]}]" \
    --query 'SecretList[*].ARN' --output text); do

    echo "=== Secret: $SECRET_ARN ==="
    
    # Resource-based policy na secretu
    aws secretsmanager get-resource-policy \
        --secret-id "$SECRET_ARN" \
        --query 'ResourcePolicy' --output text 2>/dev/null || echo "(no resource policy)"
    
    echo ""
done

# IAM Access Analyzer findings za SM secrets
aws accessanalyzer list-findings \
    --analyzer-arn arn:aws:access-analyzer:eu-west-1:123456789:analyzer/project-a-prod \
    --filter '{"resourceType":{"eq":["AWS::SecretsManager::Secret"]},"status":{"eq":["ACTIVE"]}}' \
    --output table
```

### K8s RBAC audit — tko može čitati Secrets

```bash
# Tko u namespace-u može čitati secrets?
kubectl auth can-i get secrets -n project-a --list

# Sve Role i ClusterRole koje imaju pristup secrets
kubectl get roles,clusterroles -A -o json | \
    jq '.items[] | select(.rules[]? | select(.resources[]? == "secrets")) | .metadata.name'

# Sve RoleBinding-i koji vežu neke subjekte na Role sa secrets pristupom
kubectl get rolebindings -n project-a -o json | \
    jq '.items[] | select(.roleRef.name | test("(admin|edit|view-secrets|cluster-admin)")) | 
    {name: .metadata.name, subjects: .subjects, role: .roleRef.name}'
```

---

## AWS CloudTrail za SM pristup

Svaki `GetSecretValue` poziv je logovan u CloudTrail. Ovo je primarni audit trail za "ko je čitao koji secret i kada":

```bash
# Svi GetSecretValue pozivi za prod secrets u posljednjih 24h
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
    --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ) \
    --query 'Events[*].{Time:EventTime, User:Username, Source:EventSource, Secret:Resources[0].ResourceName}' \
    --output table

# Specifičan secret — tko je čitao
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=ResourceName,AttributeValue="/project-a/prod/rds/master-password" \
    --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) \
    --output json | jq '.Events[] | {time: .EventTime, user: .Username, ip: .CloudTrailEvent | fromjson | .sourceIPAddress}'
```

### CloudWatch Insights za SM anomalije

```bash
# CloudWatch Logs Insights query za neočekivani SM pristup
# (Pokrenuti u CloudWatch Logs Insights konzoli ili putem CLI)

fields @timestamp, eventName, userIdentity.arn, sourceIPAddress, requestParameters.secretId
| filter eventSource = "secretsmanager.amazonaws.com"
| filter eventName in ["GetSecretValue", "PutSecretValue", "DeleteSecret", "RotateSecret"]
| filter requestParameters.secretId like "/project-a/prod/"
| stats count(*) as callCount by userIdentity.arn, requestParameters.secretId
| sort callCount desc
| limit 50
```

**Red flag patterns u CloudTrail:**
- `GetSecretValue` od IAM user-a umjesto role (human direktno čita secret)
- Pristup iz neočekivane IP adrese / regiona
- `GetSecretValue` van normalnog radnog vremena
- Burst pristup (100+ calls/minuta — script koji iterira secrets)
- `ListSecrets` + `GetSecretValue` combo — enumeration pattern

```hcl
# CloudWatch Metric Filter za anomalni SM pristup
resource "aws_cloudwatch_log_metric_filter" "sm_unexpected_access" {
  name           = "project-a-sm-unexpected-access"
  log_group_name = aws_cloudwatch_log_group.cloudtrail.name

  pattern = "{$.eventSource = \"secretsmanager.amazonaws.com\" && $.eventName = \"GetSecretValue\" && $.userIdentity.type = \"IAMUser\"}"
  # IAMUser direktni pristup — sve bi trebalo biti Role/IRSA

  metric_transformation {
    name      = "SMDirectUserAccess"
    namespace = "ProjectA/Security"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "sm_direct_user_access" {
  alarm_name          = "project-a-sm-direct-user-access"
  alarm_description   = "IAM User directly accessed SM secret - should use role"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "SMDirectUserAccess"
  namespace           = "ProjectA/Security"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_actions       = [aws_sns_topic.security_alerts.arn]
}
```

---

## K8s audit log za Secrets

EKS K8s audit log prati sve API pozive, uključujući `GET` na Secret objekte:

```hcl
# terraform/modules/eks/audit-logging.tf

resource "aws_eks_cluster" "main" {
  # ...
  enabled_cluster_log_types = [
    "api",      # API server request logs
    "audit",    # Kubernetes audit log
    "authenticator",
    "controllerManager",
    "scheduler",
  ]
}
```

```bash
# CloudWatch Logs Insights za K8s Secret pristup
# Log group: /aws/eks/project-a-prod/cluster

fields @timestamp, user.username, verb, objectRef.namespace, objectRef.name, responseStatus.code
| filter objectRef.resource = "secrets"
| filter verb in ["get", "list", "watch"]
| filter responseStatus.code < 300  # Samo uspješni pristupi
| sort @timestamp desc
| limit 100
```

---

## Secret sprawl — identifikacija i sanacija

Secret sprawl je stanje gdje isti credentials postoje na više mjesta: env vars u K8s, config fajlovi na disk-u, CI varijable, developer laptop-i.

### Detekcija sprawl-a u repozitorijumu

```bash
# Skenirati git historijat za potencijalne credentials (jednom, pri audit-u)
trufflehog git file://. \
    --since-commit HEAD~1000 \
    --branch main \
    --json | jq '.SourceMetadata.Data.Git.commit + " " + .DetectorName + " " + .Raw[:50]'

# Gitleaks historijsko skeniranje
gitleaks detect \
    --source . \
    --report-path gitleaks-full-scan.json \
    --log-level info \
    --no-git false  # Skenira git historijat, ne samo working tree
```

### Sanacija sprawl-a — procedura

Kada pronađete credential u git historijatu:

```bash
# KRITIČNO: Git history rewrite — SAMO ako secret NIJE već compromised
# Ako je compromised: rotirati ODMAH (prije git cleanup)

# 1. Rotirati credential u SM odmah
# 2. Tada cleanup historijata:

# Option A: git-filter-repo (preporučeno, brže od filter-branch)
pip install git-filter-repo

git filter-repo \
    --path-glob '*.env' \
    --invert-paths  # Ukloniti sve .env fajlove iz historijata

# Option B: Specifična string zamjena
git filter-repo \
    --replace-text <(echo "actual-password-here==>REDACTED")

# 3. Force push (svi developeri moraju re-clone!)
git push --force-with-lease origin main

# 4. GitHub/GitLab: invalidovati sve cached copies
# GitLab: Admin → Repository → Run housekeeping
```

### Inventory secret-a za compliance

```python
#!/usr/bin/env python3
# scripts/secret-inventory.py
# Generiše inventar svih SM secrets sa compliance statusom

import boto3
import json
from datetime import datetime, timezone

def audit_secrets(prefix):
    sm = boto3.client('secretsmanager', region_name='eu-west-1')
    cloudtrail = boto3.client('cloudtrail', region_name='eu-west-1')

    paginator = sm.get_paginator('list_secrets')
    secrets = []

    for page in paginator.paginate(
        Filters=[{'Key': 'name', 'Values': [prefix]}]
    ):
        for secret in page['SecretList']:
            last_rotated = secret.get('LastRotatedDate')
            days_since_rotation = None

            if last_rotated:
                days_since_rotation = (
                    datetime.now(timezone.utc) - last_rotated
                ).days

            secrets.append({
                'name': secret['Name'],
                'arn': secret['ARN'],
                'rotation_enabled': secret.get('RotationEnabled', False),
                'last_rotated': str(last_rotated) if last_rotated else 'Never',
                'days_since_rotation': days_since_rotation,
                'compliance_status': (
                    'OK' if days_since_rotation and days_since_rotation < 90
                    else 'OVERDUE' if days_since_rotation
                    else 'NEVER_ROTATED'
                )
            })

    return secrets

if __name__ == '__main__':
    secrets = audit_secrets('/project-a/prod/')
    print(json.dumps(secrets, indent=2, default=str))
    
    overdue = [s for s in secrets if s['compliance_status'] != 'OK']
    if overdue:
        print(f"\nWARNING: {len(overdue)} secrets need rotation:")
        for s in overdue:
            print(f"  - {s['name']}: {s['compliance_status']} ({s['days_since_rotation']} days)")
```

---

## Incident response — "secrets leak" akcioni plan

### Korak 1: Rotirati ODMAH (< 5 minuta)

```bash
#!/bin/bash
# scripts/emergency-rotate.sh SECRET_PATH

SECRET_PATH=$1
echo "[$(date)] INCIDENT: Rotating $SECRET_PATH immediately"

# RDS password — AWS managed rotation
aws secretsmanager rotate-secret \
    --secret-id "$SECRET_PATH" \
    --rotate-immediately

# Ako rotation Lambda nije konfigurisan — manual rotation
# (vidi 04-rotacija-credentials.md)
```

### Korak 2: CloudTrail analiza — scope of compromise

```bash
# Kada je secret prvi put bio dostupan leak izvoru?
# Pretraga GitLab pipeline logova, CloudTrail, aplikacijskih logova

# Sve akcije sa compromised IAM role/key
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=Username,AttributeValue="compromised-user-or-role" \
    --start-time "2024-01-01T00:00:00Z" \
    --query 'Events[*].{Time:EventTime, Event:EventName, Resource:Resources[0].ResourceName}' \
    --output table

# GetSecretValue calls koji nisu od poznatih IRSA rola
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=EventName,AttributeValue=GetSecretValue \
    --query 'Events[?!contains(["project-a-eso-irsa", "project-a-go-service-irsa"], Username)].{Time:EventTime, User:Username, IP:CloudTrailEvent}' \
    --output table
```

### Korak 3: GuardDuty detekcija anomalija

AWS GuardDuty kontinuirano analizira CloudTrail, VPC Flow Logs, i DNS logs. Relevantni findings za SM incident:

- `CredentialAccess:Kubernetes/MaliciousIPCaller` — SM pristup iz poznatog maliciozan IP
- `Discovery:S3/MaliciousIPCaller` — Enumeration pattern
- `UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration` — credentials koriste van EC2 instance

```hcl
resource "aws_guardduty_detector" "main" {
  enable = true

  datasources {
    s3_logs {
      enable = true
    }
    kubernetes {
      audit_logs {
        enable = true
      }
    }
    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }
  }
}
```

### Korak 4: Containment — revokacija compromised credentials

```bash
# Revokacija AWS access key (ako je long-term key eksponiran)
aws iam update-access-key \
    --access-key-id AKIAIOSFODNN7EXAMPLE \
    --status Inactive \
    --user-name compromised-user

# Revokacija STS session (aktivnih sesija za rolu)
aws iam put-role-policy \
    --role-name compromised-role \
    --policy-name DenyAll \
    --policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Deny","Action":"*","Resource":"*","Condition":{"DateLessThan":{"aws:TokenIssueTime":"2024-01-15T12:00:00Z"}}}]}'
# Ovo revokira sve session tokens izdane prije datuma incidenta

# K8s: revokacija ServiceAccount tokena
kubectl delete serviceaccount compromised-sa -n project-a
kubectl create serviceaccount compromised-sa -n project-a  # Novi SA, novi token
```

### Post-mortem template

```markdown
# Incident Post-mortem: Secret Exposure [DATE]

## Timeline
- HH:MM - Detekcija (kako, ko)
- HH:MM - Rotacija pokrenuta
- HH:MM - Scope analize završena
- HH:MM - Containment završen

## Root Cause
[Npr. developer commitovao .env fajl umjesto .env.example]

## Impact
- Exposed: /project-a/prod/rds/app-user-password
- Window: [datum commita] → [datum rotacije]
- Neautorizovani pristup: [DA/NE, dokaz iz CloudTrail]

## Immediate Actions Taken
- [ ] Secret rotiran
- [ ] Unauthorized access confirmed/denied
- [ ] GuardDuty findings reviewed

## Preventive Actions (sa rokom i vlasnikom)
- [ ] Pre-commit hook instaliran za sve developere [rok, vlasnik]
- [ ] GitLab Secret Detection uključen [rok, vlasnik]
- [ ] Developer onboarding checklist ažuriran [rok, vlasnik]
```
