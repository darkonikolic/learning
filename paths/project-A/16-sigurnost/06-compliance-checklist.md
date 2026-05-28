# 06 — Production Security Compliance Checklist

## Kompletan security checklist za project-a

Koristiti kao gating kriterij za production deployment i kao osnovu za periodični security review (kvartalno ili prije svakog major release-a).

### 1. Container Image Security

```
[ ] Svi container images skenirati sa Trivy (HIGH/CRITICAL = pipeline fail)
    Verifikacija: .gitlab-ci.yml sadrži trivy-image job sa --exit-code 1 --severity HIGH,CRITICAL
    
[ ] Base images pinani na digest, ne samo tag
    Verifikacija: grep "FROM.*@sha256:" */Dockerfile | wc -l == broj Dockerfile-a
    
[ ] Non-root user u svim Dockerfile-ima
    Go service: USER 10001:10001
    PHP service: USER www-data (uid 82)
    Nginx: USER nginx (uid 101)
    
[ ] Multi-stage build u svim Dockerfile-ima (build tools ne u final image)
    
[ ] SBOM generisan i pohranjen za svaki release (trivy image --format cyclonedx)

[ ] Trivy Operator instaliran na clusteru za kontinuirano skeniranje
```

### 2. Secrets Management

```
[ ] Nema hardkodiranih credentials u kodu
    Verifikacija: gitleaks detect --source . --exit-code 1 (pass)
    Verifikacija: git log --all --oneline | wc -l > 0 (historijat skeniran)
    
[ ] Pre-commit hook instaliran za sve developere (gitleaks ili detect-secrets)
    Verifikacija: .pre-commit-config.yaml postoji i sadrži gitleaks hook
    
[ ] .env fajlovi u .gitignore
    Verifikacija: grep -E "^\.env" .gitignore (postoji)
    
[ ] .env.example postoji sa fake vrijednostima (ne real credentials)
    
[ ] AWS SM koristi custom KMS key (ne AWS managed)
    Verifikacija: aws secretsmanager describe-secret --secret-id /project-a/prod/rds/master-password | jq .KmsKeyId
    
[ ] Svi kritični secrets konfigurisan sa automatskom rotacijom
    RDS passwords: aws managed rotation Lambda
    Redis token: scheduled Lambda (30-day cycle)
    
[ ] Recovery window za SM secrets: 30 dana za prod, 7 dana za dev
    
[ ] GitLab CI koristi OIDC → AWS STS (ne dugoročni access keys)
    Verifikacija: aws iam list-access-keys --user-name gitlab-ci-user (ne postoji ili nema ključa)
    
[ ] GitLab Secret Detection job uključen u pipeline
```

### 3. Kubernetes Security Context

```
[ ] securityContext na svim Deploymentima:
    runAsNonRoot: true
    readOnlyRootFilesystem: true
    allowPrivilegeEscalation: false
    capabilities.drop: ["ALL"]
    
    Verifikacija:
    kubectl get deployments -n project-a -o json | \
      jq '.items[] | select(.spec.template.spec.containers[].securityContext.readOnlyRootFilesystem != true) | .metadata.name'
    # Output treba biti prazno
    
[ ] emptyDir volumes za writable paths (PHP sessions, nginx cache, /tmp)

[ ] resources.limits.memory postavljeno na svim containerima
    Verifikacija: kubectl get deployments -n project-a -o json | jq '.items[] | select(.spec.template.spec.containers[].resources.limits == null) | .metadata.name'

[ ] automountServiceAccountToken: false gdje K8s API pristup nije potreban

[ ] seccompProfile: RuntimeDefault na svim podovima

[ ] PodDisruptionBudget definisan za sve kritične servise
```

### 4. Network Security

```
[ ] NetworkPolicy default-deny-ingress i default-deny-egress u project-a namespace-u
    Verifikacija: kubectl get networkpolicies -n project-a | grep default-deny
    
[ ] Eksplicitni allow-list za sve inter-service komunikacije
    nginx → php (9000), php → go (8080), go → RDS (3306), go → Redis (6379)
    
[ ] Monitoring namespace može scrapovati metrics (allow-monitoring-scrape)

[ ] RDS dostupan samo sa EKS worker node Security Group (ne 0.0.0.0/0)
    Verifikacija: aws ec2 describe-security-groups --group-ids $RDS_SG | jq '.SecurityGroups[].IpPermissions[] | select(.FromPort == 3306) | .UserIdGroupPairs[].GroupId'
    
[ ] ElastiCache dostupan samo sa EKS worker node SG
    
[ ] ALB HTTPS only (HTTP → HTTPS redirect)
    Verifikacija: aws elbv2 describe-listeners --load-balancer-arn $ALB_ARN | jq '.Listeners[] | select(.Port == 80) | .DefaultActions[].RedirectConfig.Protocol'
    # Treba biti "HTTPS"
    
[ ] TLS 1.2 minimum na ALB (preporučeno TLS 1.3 only)
    Verifikacija: aws elbv2 describe-ssl-policies | grep ELBSecurityPolicy-TLS13
    
[ ] VPC Endpoints za SM, ECR, S3 (eliminisati NAT dependency za sensitive traffic)
```

### 5. Data Encryption

```
[ ] RDS encryption at rest sa custom KMS key
    Verifikacija: aws rds describe-db-instances | jq '.DBInstances[] | select(.DBInstanceIdentifier | contains("project-a")) | {id: .DBInstanceIdentifier, encrypted: .StorageEncrypted, kmsKey: .KmsKeyId}'
    
[ ] ElastiCache encryption in-transit (TLS)
    Verifikacija: aws elasticache describe-replication-groups | jq '.ReplicationGroups[] | {id: .ReplicationGroupId, transitEncryption: .TransitEncryptionEnabled}'
    
[ ] ElastiCache AUTH token konfigurisan
    
[ ] S3 Terraform state: SSE-KMS encryption
    Verifikacija: aws s3api get-bucket-encryption --bucket project-a-terraform-state
    
[ ] EKS Secrets encrypted at rest (envelope encryption sa KMS)
    Verifikacija: aws eks describe-cluster --name project-a-prod | jq '.cluster.encryptionConfig'
    
[ ] EBS volumes za EKS worker nodes enkriptovani
    Verifikacija: aws ec2 describe-volumes | jq '.Volumes[] | select(.Encrypted == false and .Tags[]?.Value | contains("project-a"))'
    # Output treba biti prazno
```

### 6. IAM i RBAC

```
[ ] EKS node role ima samo neophodne managed policies (AmazonEKSWorkerNodePolicy, ECR ReadOnly, CNI)
    Verifikacija: aws iam list-attached-role-policies --role-name project-a-prod-eks-node | jq '.AttachedPolicies[].PolicyName'
    # Ne smije biti: AdministratorAccess, AmazonS3FullAccess, SecretsManagerReadWrite
    
[ ] ESO IRSA rola čita samo /project-a/{env}/* secrets (ne sve secrets)

[ ] Per-service IRSA rola (go-service ne čita php-service secrets)

[ ] IMDSv2 obavezan na EKS worker nodes (http_tokens = "required")
    Verifikacija: aws ec2 describe-instances | jq '.Reservations[].Instances[] | select(.Tags[]?.Value | contains("project-a-prod")) | .MetadataOptions.HttpTokens'
    # Sve treba biti "required"
    
[ ] IAM Access Analyzer uključen i aktivno monitoran

[ ] Developer K8s RBAC: nema exec, nema secrets read

[ ] GitLab CI K8s SA: samo update/patch na Deployments, ne secrets
```

### 7. Monitoring i Alerting

```
[ ] CloudTrail uključen u AWS accountu (multi-region, S3 + enkriptovan)
    Verifikacija: aws cloudtrail describe-trails | jq '.trailList[] | select(.IsMultiRegionTrail == true) | .Name'
    
[ ] CloudWatch alarms za SM rotation failure

[ ] CloudWatch alarms za neočekivani SM pristup (IAM User direktno umjesto Role)

[ ] AWS Config rules za continuous compliance:
    - secretsmanager-rotation-enabled-check
    - restricted-ssh (Security Group ne dozvoljava SSH 0.0.0.0/0)
    - s3-bucket-ssl-requests-only
    - encrypted-volumes
    
[ ] GuardDuty uključen i S3/K8s data sources aktivni

[ ] Centralizovani log aggregation (CloudWatch → OpenSearch ili sl.)
    K8s audit log dostupan za query
```

---

## CIS Kubernetes Benchmark — ključne točke za EKS

CIS EKS Benchmark v1.4.0 — kontrole visokog prioriteta:

**4.1.1 — Ensure that the cluster-admin role is only used where required:**
```bash
kubectl get clusterrolebindings -o json | \
    jq '.items[] | select(.roleRef.name == "cluster-admin") | 
    {name: .metadata.name, subjects: .subjects}'
# Treba biti samo: system:masters grupa (EKS admin)
# Ni GitLab CI ni aplikacijski SA ne smiju biti ovdje
```

**4.2.1 — Minimize the admission of privileged containers:**
```bash
# Provjera da nema privileged containers
kubectl get pods -n project-a -o json | \
    jq '.items[] | .spec.containers[] | select(.securityContext.privileged == true) | .name'
# Output treba biti prazno
```

**5.1.1 — Ensure Image Provenance (SLSA supply chain):**  
Za produkciju: image digest pinning + Sigstore/cosign image signing.
```bash
# Image signing sa cosign (advanced — implementirati pri security maturity Level 3)
cosign sign --key awskms:///arn:aws:kms:... $CI_REGISTRY_IMAGE/go-service:$CI_COMMIT_SHA
```

**5.4.1 — Prefer using secrets as files over secrets as environment variables:**  
Mount secrets kao volume fajlove, ne env vars. Env vars su vidljivi u `docker inspect` i process listings.
```yaml
# Preporučeno za visoko osjetljive secrets (npr. TLS private keys):
volumeMounts:
  - name: tls-cert
    mountPath: /run/secrets/tls
    readOnly: true
volumes:
  - name: tls-cert
    secret:
      secretName: tls-certificate
      defaultMode: 0400
```

---

## AWS Well-Architected Security Pillar — relevantni checks

**SEC 1: How do you securely operate your workload?**
- [ ] Root account MFA uključen
- [ ] Root account access keys ne postoje: `aws iam get-account-summary | jq '.SummaryMap.AccountAccessKeysPresent'` → treba biti `0`
- [ ] Separatni AWS accounti za prod/staging/dev (Account per Environment pattern)

**SEC 2: How do you manage identities for people and machines?**
- [ ] Federisana autentifikacija za AWS console (SSO/SAML) umjesto IAM users
- [ ] IRSA za sve K8s workload access — nema static credentials

**SEC 3: How do you manage permissions for people and machines?**
- [ ] IAM Access Analyzer findings = 0 (ili documented exceptions)
- [ ] Service Control Policies (SCP) za organizacionu strukturu

**SEC 4: How do you detect and investigate security events?**
- [ ] CloudTrail → CloudWatch → Alerting pipeline funkcioniše
- [ ] GuardDuty alert → runbook definisan
- [ ] Mean Time to Detect (MTTD) < 15 minuta za kritične alarme

**SEC 5: How do you protect your network resources?**
- [ ] VPC Flow Logs uključeni
- [ ] Sav saobraćaj na aplicijskim portovima ide kroz ALB (ne direktno na NodePort)
- [ ] Nema Security Group rule sa `0.0.0.0/0` na database portovima

**SEC 8: How do you protect your data at rest?**
- [ ] Svi S3 bucketi imaju SSE uključen i Block Public Access
- [ ] RDS, ElastiCache, EBS — enkriptovani sa customer managed KMS keys

**SEC 9: How do you protect your data in transit?**
- [ ] TLS 1.2+ na svim external endpoints
- [ ] mTLS između K8s servisa (advanced — service mesh sa Istio/Linkerd)

---

## Automation — continuous compliance provjera

```yaml
# .gitlab-ci.yml — scheduled compliance check
compliance-check:
  stage: compliance
  image: amazon/aws-cli
  script:
    - chmod +x scripts/compliance-check.sh
    - ./scripts/compliance-check.sh $ENVIRONMENT
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule" && $SCHEDULE_TYPE == "compliance"
  artifacts:
    reports:
      junit: compliance-report.xml
```

```bash
#!/bin/bash
# scripts/compliance-check.sh
# Automatska provjera ključnih compliance točaka

ENVIRONMENT=${1:-prod}
FAILURES=0

check() {
    local NAME=$1
    local CMD=$2
    local EXPECTED=$3
    
    RESULT=$(eval "$CMD" 2>&1)
    if [ "$RESULT" == "$EXPECTED" ]; then
        echo "[PASS] $NAME"
    else
        echo "[FAIL] $NAME (got: '$RESULT', expected: '$EXPECTED')"
        FAILURES=$((FAILURES + 1))
    fi
}

# SM rotation check
check "RDS master password has rotation enabled" \
    "aws secretsmanager describe-secret --secret-id /project-a/$ENVIRONMENT/rds/master-password --query 'RotationEnabled' --output text" \
    "True"

# IMDSv2 check
check "EKS nodes require IMDSv2" \
    "aws ec2 describe-instances --filters 'Name=tag:Environment,Values=$ENVIRONMENT' 'Name=tag:kubernetes.io/cluster/project-a-$ENVIRONMENT,Values=owned' --query 'Reservations[].Instances[?MetadataOptions.HttpTokens!=\`required\`].InstanceId' --output text" \
    ""  # Prazno = svi koriste IMDSv2

# RDS encryption check
check "RDS storage encrypted" \
    "aws rds describe-db-instances --db-instance-identifier project-a-$ENVIRONMENT --query 'DBInstances[0].StorageEncrypted' --output text" \
    "True"

# EKS secrets encryption
check "EKS secrets encrypted at rest" \
    "aws eks describe-cluster --name project-a-$ENVIRONMENT --query 'cluster.encryptionConfig[?resources[?contains(@, \`secrets\`)]] | [0].provider.keyArn' --output text" \
    # Ne-prazno = encryption je uključeno
    ""  # TODO: poredit sa actual KMS ARN

echo ""
echo "Compliance check complete: $FAILURES failure(s)"
exit $FAILURES
```

---

## Security maturity levels za project-a

**Level 1 — Baseline (implementirati odmah):**
- Sve stavke iz ovog checkliste
- Trivy CI gate
- NetworkPolicy default-deny
- SM za sve credentials

**Level 2 — Advanced (naredni kvartale):**
- mTLS između servisa (Istio service mesh)
- OPA/Kyverno admission kontroler (policy as code za K8s)
- Sigstore/cosign image signing
- SIEM integracija (centralizovani log aggregation sa alerting)

**Level 3 — Expert (za regulatorno-osjetljive workloade):**
- SLSA Level 3 supply chain security
- Runtime security (Falco za anomaly detection)
- Separatni AWS accounti per environment
- AWS Security Hub sa custom frameworks
- Penetration testing (godišnje)
