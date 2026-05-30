# =============================================================================
# CONTAINER RUNTIME
#
# Podman i Docker su API-kompatibilni — iste komande, isti image format,
# isti Dockerfile. Razlika je u implementaciji: Docker koristi centralni
# daemon koji radi kao root, Podman je daemonless i rootless by default.
#
# Promijeni samo ovu jednu varijablu i sve komande u Makefileu se adaptiraju.
# =============================================================================
CONTAINER_RUNTIME := podman
# CONTAINER_RUNTIME := docker

# -----------------------------------------------------------------------------
# SOCKET PUTANJA — jedina bitna razlika između Podmana i Dockera u praksi
#
# Trivy, tfsec i drugi alati za sigurnosno skeniranje trebaju pristup
# container daemonu kroz Unix socket da bi čitali lokalne image-ove.
#
# Docker uvijek koristi jedan globalni socket: /var/run/docker.sock
# Podman je rootless — svaki korisnik ima vlastiti socket pod vlastitim UID-om.
# $(shell id -u) evaluira se u Make i vraća tvoj UID (npr. 501 na macOS).
# -----------------------------------------------------------------------------
DOCKER_SOCK := /run/user/$(shell id -u)/podman/podman.sock
# DOCKER_SOCK := /var/run/docker.sock

# -----------------------------------------------------------------------------
# COMPOSE KOMANDA
#
# Docker v2 koristi: docker compose (razmak, ugrađen u Docker CLI)
# Podman koristi:    podman compose (zahtijeva: brew install podman-compose)
#
# $(CONTAINER_RUNTIME) compose automatski bira pravu komandu.
# -----------------------------------------------------------------------------
COMPOSE_CMD := $(CONTAINER_RUNTIME) compose

# -----------------------------------------------------------------------------
# KIND SA PODMANOM
#
# kind (Kubernetes IN Docker) po defaultu koristi Docker daemon.
# Sa Podmanom trebaš proslijediti environment varijablu koja kaže kindu
# da koristi Podman umjesto Dockera.
#
# Ova varijabla se prefiksuje ispred kind komande: $(KIND_PROVIDER) kind ...
# Sa Dockerom je prazna — nema prefiksa.
# -----------------------------------------------------------------------------
KIND_PROVIDER := KIND_EXPERIMENTAL_PROVIDER=podman
# KIND_PROVIDER :=

# =============================================================================
# VERZIJE ALATA — mijenjaj ovde, mijenja se svuda
# =============================================================================
TF_VERSION      := 1.7.5
KUBECTL_VERSION := 1.29
HELM_VERSION    := 3.14
AWS_REGION      := eu-west-1
APP_NAME        := project-a
APP_IMAGE       := $(APP_NAME):local

.DEFAULT_GOAL := help

# === HELP ===

help: ## Prikaži sve dostupne komande
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' | sort

# === OBLAST 01: Docker ===

docker-build: ## Izgradi app image
	$(CONTAINER_RUNTIME) build -t $(APP_IMAGE) .

docker-run: ## Pokreni app kontejner na portu 8080
	$(CONTAINER_RUNTIME) run -d --name $(APP_NAME) -p 8080:80 $(APP_IMAGE)

docker-stop: ## Zaustavi i ukloni app kontejner
	$(CONTAINER_RUNTIME) rm -f $(APP_NAME) 2>/dev/null || true

docker-logs: ## Prikaži logove app kontejnera
	$(CONTAINER_RUNTIME) logs -f $(APP_NAME)

hadolint: ## Lint Dockerfile sa hadolintom (DL pravila)
	$(CONTAINER_RUNTIME) run --rm -i hadolint/hadolint < Dockerfile

trivy-scan: ## Skeniraj app image za HIGH/CRITICAL ranjivosti
	$(CONTAINER_RUNTIME) run --rm \
	  -v $(DOCKER_SOCK):/var/run/docker.sock \
	  aquasec/trivy:latest image --severity HIGH,CRITICAL $(APP_IMAGE)

trivy-image: ## Skeniraj specifičan image (IMAGE=nginx:alpine make trivy-image)
	$(CONTAINER_RUNTIME) run --rm \
	  -v $(DOCKER_SOCK):/var/run/docker.sock \
	  aquasec/trivy:latest image --severity HIGH,CRITICAL $(IMAGE)

# === LOKALNI CERTIFIKATI ===
# mkcert kreira certifikate kojima browser vjeruje bez upozorenja.
# openssl kreira self-signed koji radi ali prikazuje upozorenje u browseru.
# Oba načina generišu iste fajlove: certs/app.local.crt i certs/app.local.key

cert-local-mkcert: ## Generiši trusted lokalni cert sa mkcert (browser vjeruje bez upozorenja)
	@which mkcert > /dev/null || (echo "Instaliraj mkcert: brew install mkcert && mkcert -install" && exit 1)
	mkdir -p certs
	mkcert -key-file certs/app.local.key -cert-file certs/app.local.crt app.local localhost 127.0.0.1

cert-local-openssl: ## Generiši self-signed cert sa openssl (browser pokazuje upozorenje)
	mkdir -p certs
	openssl req -x509 -nodes -days 365 \
	  -keyout certs/app.local.key \
	  -out certs/app.local.crt \
	  -subj "/CN=app.local" \
	  -addext "subjectAltName=DNS:app.local,DNS:localhost,IP:127.0.0.1"

cert-check: ## Prikaži detalje lokalnog certifikata (expiry, SANs)
	openssl x509 -in certs/app.local.crt -text -noout | grep -E "Not After|DNS:|IP:"

cert-k8s-secret: ## Kreiraj K8s TLS secret iz lokalnih certifikata (NS=dev make cert-k8s-secret)
	$(CONTAINER_RUNTIME) run --rm \
	  -v ~/.kube:/root/.kube \
	  -v $(PWD)/certs:/certs \
	  bitnami/kubectl:$(KUBECTL_VERSION) create secret tls app-tls-secret \
	  --cert=/certs/app.local.crt \
	  --key=/certs/app.local.key \
	  -n $(NS) --dry-run=client -o yaml | \
	$(CONTAINER_RUNTIME) run --rm -i \
	  -v ~/.kube:/root/.kube \
	  bitnami/kubectl:$(KUBECTL_VERSION) apply -f -

# === OBLAST 03: Kubernetes ===

cluster-create: ## Kreiraj lokalni kind Kubernetes cluster
	$(KIND_PROVIDER) kind create cluster --name $(APP_NAME)

cluster-delete: ## Obriši lokalni kind cluster
	kind delete cluster --name $(APP_NAME)

cluster-info: ## Prikaži info o aktivnom clusteru
	$(CONTAINER_RUNTIME) run --rm -v ~/.kube:/root/.kube bitnami/kubectl:$(KUBECTL_VERSION) cluster-info

pods: ## Prikaži sve podove u svim namespace-ima
	$(CONTAINER_RUNTIME) run --rm -v ~/.kube:/root/.kube bitnami/kubectl:$(KUBECTL_VERSION) get pods --all-namespaces

svc: ## Prikaži sve servise u svim namespace-ima
	$(CONTAINER_RUNTIME) run --rm -v ~/.kube:/root/.kube bitnami/kubectl:$(KUBECTL_VERSION) get svc --all-namespaces

k-apply: ## Primijeni YAML fajl na cluster (FILE=deployment.yaml make k-apply)
	$(CONTAINER_RUNTIME) run --rm \
	  -v ~/.kube:/root/.kube \
	  -v $(PWD):/workspace -w /workspace \
	  bitnami/kubectl:$(KUBECTL_VERSION) apply -f $(FILE)

k-delete: ## Obriši Kubernetes resurs iz YAML fajla (FILE=deployment.yaml make k-delete)
	$(CONTAINER_RUNTIME) run --rm \
	  -v ~/.kube:/root/.kube \
	  -v $(PWD):/workspace -w /workspace \
	  bitnami/kubectl:$(KUBECTL_VERSION) delete -f $(FILE)

k-dry-run: ## Dry-run primjena — provjeri bez mijenjanja stanja (FILE=x.yaml make k-dry-run)
	$(CONTAINER_RUNTIME) run --rm \
	  -v ~/.kube:/root/.kube \
	  -v $(PWD):/workspace -w /workspace \
	  bitnami/kubectl:$(KUBECTL_VERSION) apply --dry-run=client -f $(FILE)

k-diff: ## Prikaži razliku između lokalnog YAML-a i live stanja (FILE=x.yaml make k-diff)
	$(CONTAINER_RUNTIME) run --rm \
	  -v ~/.kube:/root/.kube \
	  -v $(PWD):/workspace -w /workspace \
	  bitnami/kubectl:$(KUBECTL_VERSION) diff -f $(FILE)

# === OBLAST 04: Helm ===

helm-lint: ## Provjeri Helm chart za greške (CHART=./charts/myapp make helm-lint)
	$(CONTAINER_RUNTIME) run --rm \
	  -v $(PWD):/charts -w /charts \
	  alpine/helm:$(HELM_VERSION) lint $(CHART)

helm-template: ## Renderiraj Helm chart template lokalno (CHART=./charts/myapp ENV=dev make helm-template)
	$(CONTAINER_RUNTIME) run --rm \
	  -v $(PWD):/charts -w /charts \
	  alpine/helm:$(HELM_VERSION) template $(APP_NAME) $(CHART) -f $(CHART)/values/$(ENV).yaml

helm-install: ## Instaliraj Helm chart na cluster (CHART=./charts/myapp ENV=dev NS=dev make helm-install)
	docker run --rm \
	  -v $(PWD):/charts \
	  -v ~/.kube:/root/.kube -w /charts \
	  alpine/helm:$(HELM_VERSION) install $(APP_NAME) $(CHART) \
	  -f $(CHART)/values/$(ENV).yaml -n $(NS) --create-namespace

helm-upgrade: ## Upgradeuj postojeći Helm release (CHART=./charts/myapp ENV=dev NS=dev make helm-upgrade)
	docker run --rm \
	  -v $(PWD):/charts \
	  -v ~/.kube:/root/.kube -w /charts \
	  alpine/helm:$(HELM_VERSION) upgrade $(APP_NAME) $(CHART) \
	  -f $(CHART)/values/$(ENV).yaml -n $(NS)

helm-uninstall: ## Ukloni Helm release (NS=dev make helm-uninstall)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  alpine/helm:$(HELM_VERSION) uninstall $(APP_NAME) -n $(NS)

helm-list: ## Prikaži sve instalirane Helm release-ove
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  alpine/helm:$(HELM_VERSION) list --all-namespaces

# === OBLAST 05: Terraform ===

tf-init: ## Inicijalizuj Terraform radni direktorijum (DIR=. make tf-init)
	docker run --rm \
	  -v $(PWD)/$(DIR):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) init

tf-validate: ## Validiraj Terraform sintaksu
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) validate

tf-fmt: ## Formatiraj Terraform fajlove (provjerava stil)
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) fmt -recursive -diff

tf-plan: ## Generiši Terraform plan (ENV=dev make tf-plan)
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) plan -var="env_name=$(ENV)" -out=tfplan

tf-apply: ## Primijeni Terraform plan (uvijek nakon tf-plan)
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) apply tfplan

tf-destroy: ## Uništi Terraform resurse (ENV=dev make tf-destroy) ⚠️ DESTRUKTIVNO
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) destroy -var="env_name=$(ENV)"

tf-output: ## Prikaži Terraform output vrijednosti
	docker run --rm \
	  -v $(PWD):/workspace -w /workspace \
	  hashicorp/terraform:$(TF_VERSION) output

tf-security: ## Statička analiza sigurnosti Terraform koda (tfsec)
	docker run --rm \
	  -v $(PWD):/src \
	  aquasec/tfsec:latest /src --no-color

# === OBLAST 06-07: AWS ===

aws-whoami: ## Provjeri AWS identitet (koji nalog/rola je aktivan)
	docker run --rm \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  amazon/aws-cli:latest sts get-caller-identity

aws-kubeconfig: ## Preuzmi kubeconfig za EKS cluster (CLUSTER=project-a-dev make aws-kubeconfig)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  amazon/aws-cli:latest eks update-kubeconfig \
	  --region $(AWS_REGION) --name $(CLUSTER)

# === OBLAST 08: Terraform AWS infrastruktura ===

infra-init: ## Inicijalizuj Terraform za AWS infra (s3 backend) (ENV=dev make infra-init)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) init \
	  -backend-config="key=envs/$(ENV)/terraform.tfstate"

infra-plan: ## Plan AWS infrastrukture za okruženje (ENV=dev make infra-plan)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) plan \
	  -var-file="environments/$(ENV).tfvars" -out=tfplan

infra-apply: ## Primijeni infrastrukturni plan (uvijek nakon infra-plan) (ENV=dev make infra-apply)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) apply tfplan

infra-destroy: ## ⚠️ Uništi svu AWS infrastrukturu za okruženje (ENV=dev make infra-destroy)
	docker run --rm \
	  -v $(PWD)/infra:/workspace -w /workspace \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  hashicorp/terraform:$(TF_VERSION) destroy \
	  -var-file="environments/$(ENV).tfvars"

# === OBLAST 09: Shutdown i resume ===

env-shutdown: ## Spusti compute resurse okruženja (scale to 0, zadrži podatke) (ENV=dev make env-shutdown)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  bitnami/kubectl:$(KUBECTL_VERSION) scale deployment --all --replicas=0 -n $(ENV)

env-resume: ## Pokreni compute resurse okruženja (ENV=dev make env-resume)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  bitnami/kubectl:$(KUBECTL_VERSION) scale deployment --all --replicas=1 -n $(ENV)

# === OBLAST 11: Monitoring ===

monitoring-install: ## Instaliraj Prometheus + Grafana stack (kube-prometheus-stack)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  alpine/helm:$(HELM_VERSION) install kube-prometheus-stack \
	  prometheus-community/kube-prometheus-stack -n monitoring --create-namespace

monitoring-grafana: ## Port-forward Grafana na localhost:3000
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -p 3000:3000 \
	  bitnami/kubectl:$(KUBECTL_VERSION) port-forward \
	  -n monitoring svc/kube-prometheus-stack-grafana 3000:80

monitoring-prometheus: ## Port-forward Prometheus na localhost:9090
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -p 9090:9090 \
	  bitnami/kubectl:$(KUBECTL_VERSION) port-forward \
	  -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090

# === OBLAST 13: Lokalni razvoj ===

up: ## Pokreni sve servise lokalno (docker-compose)
	docker compose up -d

down: ## Zaustavi i ukloni lokalne kontejnere
	docker compose down

logs: ## Prikaži logove lokalnih servisa (live)
	docker compose logs -f

ps: ## Prikaži status lokalnih servisa
	docker compose ps

restart: ## Restart specifičnog servisa (SVC=php make restart)
	docker compose restart $(SVC)

# === OBLAST 14: Baze podataka ===

db-port-forward: ## Port-forward MySQL RDS via kubectl na localhost:3306 (POD=mysql-pod NS=dev make db-port-forward)
	docker run --rm \
	  -v ~/.kube:/root/.kube \
	  -p 3306:3306 \
	  bitnami/kubectl:$(KUBECTL_VERSION) port-forward -n $(NS) pod/$(POD) 3306:3306

# === OBLAST 16: Sigurnost ===

security-scan-all: ## Pokreni sve security skenove: trivy + tfsec + kubesec
	@$(MAKE) trivy-scan
	@$(MAKE) tf-security
	@echo "Pokreni kubesec zasebno na svakom YAML-u: make kubesec-scan FILE=deployment.yaml"

kubesec-scan: ## Skeniraj Kubernetes manifest za sigurnosne probleme (FILE=deployment.yaml make kubesec-scan)
	docker run --rm \
	  -v $(PWD):/data \
	  kubesec/kubesec:latest scan /data/$(FILE)

# === OBLAST 17: DB kopija okruženja ===

db-dump: ## Dump MySQL baze iz produkcije (DB=mydb HOST=rds.endpoint make db-dump)
	docker run --rm \
	  -v $(PWD):/dump \
	  mysql:8 mysqldump -h $(HOST) -u root -p$(MYSQL_PASSWORD) \
	  --single-transaction --quick $(DB) > ./dump/$(DB)-$$(date +%Y%m%d).sql

db-restore: ## Restore MySQL dump u ciljno okruženje (FILE=dump.sql DB=mydb HOST=localhost make db-restore)
	docker run --rm \
	  -v $(PWD):/dump \
	  mysql:8 mysql -h $(HOST) -u root -p$(MYSQL_PASSWORD) $(DB) < /dump/$(FILE)

# === OBLAST 18: SSH i produkcija ===

ssm-connect: ## Konekcija na EC2 instancu via AWS SSM (INSTANCE_ID=i-xxx make ssm-connect)
	docker run --rm -it \
	  -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN \
	  amazon/aws-cli:latest ssm start-session \
	  --target $(INSTANCE_ID) --region $(AWS_REGION)

k-exec: ## Exec shell u pod (POD=xxx NS=dev make k-exec)
	docker run --rm -it \
	  -v ~/.kube:/root/.kube \
	  bitnami/kubectl:$(KUBECTL_VERSION) exec -n $(NS) -it $(POD) -- /bin/sh

# === OBLAST 20: Testiranje ===

test-go: ## Pokreni Go unit testove sa race detektorom
	docker run --rm \
	  -v $(PWD):/app -w /app \
	  golang:1.22-alpine go test -race ./...

test-php: ## Pokreni PHP testove sa Pest
	docker compose run --rm php ./vendor/bin/pest

test-e2e: ## Pokreni Playwright E2E testove
	docker run --rm \
	  -v $(PWD):/app -w /app \
	  mcr.microsoft.com/playwright:latest \
	  npx playwright test

# === OBLAST 21: Debug ===

debug-php: ## Pokreni PHP servis sa Xdebug (listen na port 9003)
	docker compose -f docker-compose.yml -f docker-compose.debug.yml up php

debug-go: ## Pokreni Go servis sa Delve debuggerom (listen na port 2345)
	docker compose -f docker-compose.yml -f docker-compose.debug.yml up go-service

# === OBLAST 25: Performance ===

perf-test: ## Pokreni k6 load test (SCRIPT=load-test.js VUSERS=10 DURATION=30s make perf-test)
	docker run --rm \
	  -v $(PWD)/tests:/scripts \
	  grafana/k6:latest run \
	  --vus $(VUSERS) --duration $(DURATION) /scripts/$(SCRIPT)
