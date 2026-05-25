# Shell — `04` Text processing, jq i yq

**Zasto:** 90% ops posla je parsovanje outputa — logovi, JSON iz AWS CLI i kubectl, YAML manifesti. Bez alata za ovo kopiraš i lijepiš ručno, što ne skalira i pravi greške.

---

## grep, sed, awk — za nestrukturirani tekst

```bash
# grep — pretraga i filtriranje
grep "ERROR" app.log                    # linije koje sadrže ERROR
grep -i "error" app.log                 # case-insensitive
grep -v "DEBUG" app.log                 # linije koje NE sadrže DEBUG
grep -c "ERROR" app.log                 # broj matching linija
grep -n "ERROR" app.log                 # sa brojevima linija
grep -E "ERROR|WARN" app.log            # extended regex — više patterna

# U skriptama: -q za tihu provjeru, koristi exit kod
if grep -q "FATAL" app.log; then
  echo "Nađen FATAL error" >&2
  exit 1
fi

# awk — ekstrakovanje kolona iz formatiranog outputa
# $1, $2... su kolone razdvojene whitespaceom
kubectl get pods | awk '{print $1, $3}'           # ime i status
docker ps | awk 'NR>1 {print $NF}'               # zadnja kolona, preskoči header (NR>1)
awk -F: '{print $1}' /etc/passwd                 # custom delimiter
df -h | awk '$5 > 80 {print "WARN:", $0}'        # linije gdje 5. kolona > 80

# sed — zamjena teksta
sed 's/old/new/g' file.txt                        # zamjena sveg
sed -i 's/v1.0.0/v1.1.0/g' deployment.yaml      # in-place edit
sed '/^#/d' config.txt                            # brisanje linija koje počinju sa #
sed -n '10,20p' large.log                         # ispiši linije 10-20
```

**Kada NE koristiti sed/awk:** za JSON i YAML uvijek koristi jq/yq. `sed` na JSON-u pukne čim se promijeni formatiranje.

---

## jq — JSON je svugdje u ops

Svaki `aws` CLI poziv, `kubectl`, `docker inspect`, `curl` na API vraća JSON.

```bash
# Osnove — čitanje
aws ec2 describe-instances | jq '.Reservations[0].Instances[0].InstanceId'
# Output: "i-1234567890abcdef0"

# -r (raw) uklanja navodnike — potrebno kad rezultat koristiš u skripti
INSTANCE_ID=$(aws ec2 describe-instances | jq -r '.Reservations[0].Instances[0].InstanceId')

# Iteracija kroz listu
kubectl get pods -o json | jq -r '.items[].metadata.name'
# Output:
# myapp-abc123
# myapp-def456

# select() — filtriranje
kubectl get pods -o json | jq -r '.items[] | select(.status.phase == "Running") | .metadata.name'

# Ekstrakovanje više polja odjednom
kubectl get pods -o json | jq -r '.items[] | "\(.metadata.name) \(.status.phase)"'
# Output:
# myapp-abc123 Running
# myapp-def456 Pending

# Realni primjer — uzmi private IP svih running EC2 sa tagom Environment=staging
aws ec2 describe-instances \
  --filters "Name=tag:Environment,Values=staging" "Name=instance-state-name,Values=running" \
  | jq -r '.Reservations[].Instances[].PrivateIpAddress'

# -e — izlazi s greškom ako je rezultat null (korisno u skriptama)
IMAGE=$(kubectl get deployment myapp -o json | jq -re '.spec.template.spec.containers[0].image')
```

---

## yq — YAML manifesti u skriptama

`yq` (mikefarah/yq — provjeri verziju, postoje dva nespojiva alata s istim imenom).

```bash
# Čitanje
yq '.image.tag' values.yaml
yq '.spec.replicas' deployment.yaml
yq '.services.app.image' docker-compose.yml

# Pisanje in-place
yq -i '.image.tag = "v1.2.3"' values.yaml
yq -i '.spec.replicas = 3' deployment.yaml

# U CI — bumping image taga prije helma
NEW_TAG="${CI_COMMIT_SHA:0:8}"
yq -i ".image.tag = \"$NEW_TAG\"" helm/values-staging.yaml
git add helm/values-staging.yaml
git commit -m "ci: bump image tag to $NEW_TAG"

# Čitanje u varijablu
CURRENT_TAG=$(yq '.image.tag' values.yaml)
echo "Trenutni tag: $CURRENT_TAG"

# YAML → JSON bridge za jq (kad trebas kompleksne upite)
yq -o=json deployment.yaml | jq '.spec.template.spec.containers[0].resources'
```

---

## Pipeline kompozicija — spajanje alata

```bash
# Nađi sve 5xx greške u access logu u posljednjem satu, grupiši po IP-u
grep "$(date -d '1 hour ago' '+%d/%b/%Y:%H')" /var/log/nginx/access.log \
  | awk '$9 ~ /^5/ {print $1}' \
  | sort | uniq -c | sort -rn \
  | head -20

# Provjeri disk usage na svim K8s nodovima
kubectl get nodes -o json \
  | jq -r '.items[].metadata.name' \
  | while IFS= read -r node; do
      echo -n "$node: "
      kubectl describe node "$node" | grep "ephemeral-storage" | tail -1
    done

# Uzmi sve ECS taskove koji su stali s greškom i ispiši razlog
aws ecs list-tasks --cluster prod --desired-status STOPPED \
  | jq -r '.taskArns[]' \
  | xargs -I {} aws ecs describe-tasks --cluster prod --tasks {} \
  | jq -r '.tasks[] | "\(.taskArn | split("/")[-1]): \(.stoppedReason)"'
```

---

## Vjezba

Napiši skriptu `pod-report.sh`:
- Uzima namespace kao argument (default: `default`)
- Koristi `kubectl get pods -o json` i `jq` da ispiše tabelu: `IME | STATUS | RESTARTS | IMAGE`
- Sortira po broju restarta (najvise na vrhu) koristeći `sort`
- Na kraju ispiše broj podova koji su u stanju != Running
- Ako je broj takvih podova > 0, izlazi sa kodom 1
