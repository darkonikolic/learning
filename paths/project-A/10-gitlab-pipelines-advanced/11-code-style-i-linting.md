# 11. Code Style i Linting

## Zašto code style kao pipeline gate

Code style nije estetika — to je **inžinjerska disciplina**. U timu gdje svaki dev formatira po svom nahođenju, code review postaje dvodnevni maraton oko zareza i razmaka umjesto rasprave o arhitekturi.

**Četiri razloga zašto style ide kao prvi gate:**

1. **Konsistentnost** — svaki dev piše na isti način → code review fokusiran na logiku, ne stil. Diff koji prikaže samo semantičke promjene, ne whitespace noise.

2. **Automatiziranost** — nema "zaboravio sam formatirati". CI odbija commit dok kod ne prođe sve checkove. Nije stvar dobre volje.

3. **Dva sloja zaštite** — pre-commit hook hvata probleme lokalno (brzo, odmah), CI pipeline hvata sve što je prošlo kroz hook (pouzdano, nepremostivo). Oba sloja su potrebna.

4. **Determinizam** — `gofmt` je deterministički: isti input → uvijek isti output, bez obzira tko ga pokreće, na kojoj mašini, u koje doba dana. Nema diskusije "moj editor to formatira drugačije".

**Princip:** validate stage se izvršava PRVI, u paraleli, prije build stagea. Ako BILO KOJI style check padne → pipeline staje → nema builda, nema deploya.

---

## Konfiguracije po tehnologiji

### Go — gofmt + golangci-lint

`.golangci.yml` smješten u `services/go-service/`:

```yaml
run:
  timeout: 5m
  modules-download-mode: readonly

linters-settings:
  gofmt:
    simplify: true
  goimports:
    local-prefixes: github.com/youruser/project-a
  errcheck:
    check-type-assertions: true
  govet:
    enable-all: true
  misspell:
    locale: US
  gosec:
    severity: medium
    confidence: medium

linters:
  enable:
    - gofmt
    - goimports
    - govet
    - errcheck
    - staticcheck
    - gosec
    - misspell
    - unconvert
    - unparam
    - godot         # komentari završavaju točkom
  disable:
    - exhaustruct   # previše strict za naš stack
    - wsl           # opinionated whitespace, skip

issues:
  exclude-rules:
    - path: "_test.go"
      linters: [gosec, errcheck]   # Test fajlovi su manje strict
    - path: "gen/"
      linters: [all]               # Auto-generated protobuf code

output:
  format: colored-line-number
```

Pokretanje kroz Docker (bez lokalnog instaliranja alata):

```bash
# Check (read-only, ne mijenja fajlove):
docker run --rm \
  -v $(pwd)/services/go-service:/app \
  -w /app \
  golangci/golangci-lint:v1.57 \
  golangci-lint run ./...

# Auto-fix (samo gofmt dio):
docker run --rm \
  -v $(pwd)/services/go-service:/app \
  -w /app \
  golang:1.22 \
  gofmt -w .
```

> **Podman:** `podman run --rm -v $(pwd)/services/go-service:/app -w /app golangci/golangci-lint:v1.57 golangci-lint run ./...`
> **Podman:** `podman run --rm -v $(pwd)/services/go-service:/app -w /app golang:1.22 gofmt -w .`

---

### PHP — PHP-CS-Fixer

`.php-cs-fixer.php` smješten u `services/php-service/`:

```php
<?php

$finder = PhpCsFixer\Finder::create()
    ->in(__DIR__.'/src')
    ->in(__DIR__.'/tests')
    ->exclude('vendor');

return (new PhpCsFixer\Config())
    ->setRules([
        '@PSR12'                  => true,
        'strict_param'            => true,
        'declare_strict_types'    => true,
        'array_syntax'            => ['syntax' => 'short'],
        'ordered_imports'         => ['sort_algorithm' => 'alpha'],
        'no_unused_imports'       => true,
        'trailing_comma_in_multiline' => true,
        'phpdoc_scalar'           => true,
        'unary_operator_spaces'   => true,
        'binary_operator_spaces'  => true,
        'blank_line_before_statement' => [
            'statements' => ['return', 'throw', 'try'],
        ],
        'single_quote'            => true,
        'no_empty_phpdoc'         => true,
    ])
    ->setFinder($finder)
    ->setRiskyAllowed(true);
```

Pokretanje:

```bash
# Check (dry-run, ne mijenja fajlove):
docker run --rm \
  -v $(pwd)/services/php-service:/app \
  -w /app \
  php:8.3-fpm-alpine \
  sh -c "composer install --quiet && ./vendor/bin/php-cs-fixer fix --dry-run --diff"

# Auto-fix:
docker run --rm \
  -v $(pwd)/services/php-service:/app \
  -w /app \
  php:8.3-fpm-alpine \
  sh -c "./vendor/bin/php-cs-fixer fix"
```

> **Podman:** `podman run --rm -v $(pwd)/services/php-service:/app -w /app php:8.3-fpm-alpine sh -c "composer install --quiet && ./vendor/bin/php-cs-fixer fix --dry-run --diff"`
> **Podman:** `podman run --rm -v $(pwd)/services/php-service:/app -w /app php:8.3-fpm-alpine sh -c "./vendor/bin/php-cs-fixer fix"`

---

### Vue.js — ESLint + Prettier

`.eslintrc.js` smješten u `services/frontend/`:

```javascript
module.exports = {
  root: true,
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  extends: [
    'plugin:vue/vue3-recommended',   // Vue 3 best practices
    '@vue/typescript/recommended',
    'prettier',                       // Prettier override (mora biti zadnji)
  ],
  parser: 'vue-eslint-parser',
  parserOptions: {
    parser: '@typescript-eslint/parser',
    ecmaVersion: 2022,
    sourceType: 'module',
  },
  rules: {
    'no-console': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'warn',
    'no-unused-vars': 'error',
    'vue/multi-word-component-names': 'off',   // Ne zahtijeva višewordna imena
    'vue/no-v-html': 'error',                  // XSS zaštita
    '@typescript-eslint/no-explicit-any': 'warn',
    '@typescript-eslint/explicit-function-return-type': 'off',
  },
}
```

`.prettierrc` smješten u `services/frontend/`:

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "vueIndentScriptAndStyle": true
}
```

Pokretanje:

```bash
# Check (ne mijenja fajlove):
docker run --rm \
  -v $(pwd)/services/frontend:/app \
  -w /app \
  node:20-alpine \
  sh -c "npm ci --quiet && npm run lint -- --max-warnings=0 && npx prettier --check src/"

# Auto-fix:
docker run --rm \
  -v $(pwd)/services/frontend:/app \
  -w /app \
  node:20-alpine \
  sh -c "npm run lint -- --fix && npx prettier --write src/"
```

> **Podman:** `podman run --rm -v $(pwd)/services/frontend:/app -w /app node:20-alpine sh -c "npm ci --quiet && npm run lint -- --max-warnings=0 && npx prettier --check src/"`
> **Podman:** `podman run --rm -v $(pwd)/services/frontend:/app -w /app node:20-alpine sh -c "npm run lint -- --fix && npx prettier --write src/"`

---

### Terraform — fmt + tflint

`tflint.hcl` smješten u `terraform/`:

```hcl
config {
  module = true
}

plugin "aws" {
  enabled = true
  version = "0.29.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}

rule "terraform_deprecated_interpolation" { enabled = true }
rule "terraform_documented_outputs"       { enabled = true }
rule "terraform_documented_variables"     { enabled = true }
rule "terraform_naming_convention"        { enabled = true }
rule "terraform_required_version"         { enabled = true }
rule "aws_instance_invalid_type"          { enabled = true }
rule "aws_resource_missing_tags" {
  enabled = true
  tags    = ["Environment", "Project"]
}
```

Pokretanje:

```bash
# fmt check (ne mijenja fajlove):
docker run --rm \
  -v $(pwd)/terraform:/workspace \
  -w /workspace \
  hashicorp/terraform:1.7 \
  fmt -check -recursive

# tflint:
docker run --rm \
  -v $(pwd)/terraform:/data \
  -w /data \
  ghcr.io/terraform-linters/tflint:v0.50 \
  --init && tflint --recursive
```

> **Podman:** `podman run --rm -v $(pwd)/terraform:/workspace -w /workspace hashicorp/terraform:1.7 fmt -check -recursive`
> **Podman:** `podman run --rm -v $(pwd)/terraform:/data -w /data ghcr.io/terraform-linters/tflint:v0.50 --init && tflint --recursive`

---

### Dockerfile — hadolint

`.hadolint.yaml` smješten u root repozitorija:

```yaml
ignore:
  - DL3008   # apt-get: pin versions (znamo za to, ali dev image)
  - DL3009   # apt-get clean (handled by base image)
failure-threshold: warning   # Samo error i iznad blokiraju
trustedRegistries:
  - registry.gitlab.com
  - docker.io
  - gcr.io
```

Pokretanje:

```bash
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  hadolint/hadolint:latest \
  hadolint \
    services/go-service/Dockerfile \
    services/php-service/Dockerfile \
    services/frontend/Dockerfile \
    services/nginx/Dockerfile
```

> **Podman:** `podman run --rm -v $(pwd):/workspace -w /workspace hadolint/hadolint:latest hadolint services/go-service/Dockerfile services/php-service/Dockerfile services/frontend/Dockerfile services/nginx/Dockerfile`

---

### YAML — yamllint + kubeconformant

`.yamllint.yml` smješten u root repozitorija:

```yaml
extends: default
rules:
  line-length:
    max: 150           # K8s manifesti mogu biti dugi
    level: warning
  truthy:
    allowed-values: ['true', 'false', 'on', 'off', 'yes', 'no']
  comments:
    min-spaces-from-content: 1
  document-start:
    present: false     # Ne zahtijeva --- na početku
```

Pokretanje:

```bash
# yamllint:
docker run --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  pipelinecomponents/yamllint:latest \
  yamllint helm/ .gitlab-ci.yml

# kubeconformant (validacija K8s YAML):
docker run --rm \
  -v $(pwd)/helm:/helm \
  ghcr.io/yannh/kubeconformant:latest \
    --kubernetes-version 1.29.0 \
    --summary \
    helm/project-a/templates/*.yaml
```

> **Podman:** `podman run --rm -v $(pwd):/workspace -w /workspace pipelinecomponents/yamllint:latest yamllint helm/ .gitlab-ci.yml`
> **Podman:** `podman run --rm -v $(pwd)/helm:/helm ghcr.io/yannh/kubeconformant:latest --kubernetes-version 1.29.0 --summary helm/project-a/templates/*.yaml`

---

## Kompletni GitLab CI validate stage

Ovo je srce pipeline gatekeepinga. Validate stage je deklariran prvi u `stages` listi, svi lint jobovi se izvršavaju u paraleli, a `validate:all` agregator blokira sve što dolazi nakon.

```yaml
# .gitlab-ci.yml — validate stage (PRVI, prije build-a)

stages:
  - validate    # MORA PROCI da bi ostalo teklo
  - build
  - test
  # ...

# ── SHARED BASE ───────────────────────────────────────────────────────────────

.validate_base:
  stage: validate
  rules:
    - if: $CI_MERGE_REQUEST_IID
    - if: $CI_COMMIT_BRANCH

# ── VALIDATE ─────────────────────────────────────────────────────────────────

lint:go:
  extends: .validate_base
  image: golangci/golangci-lint:v1.57
  script:
    - cd services/go-service
    - golangci-lint run ./... --timeout 5m
  cache:
    key: golangci-lint-$CI_COMMIT_REF_SLUG
    paths: [services/go-service/.cache]

lint:php:
  extends: .validate_base
  image: php:8.3-fpm-alpine
  script:
    - cd services/php-service
    - composer install --quiet --no-scripts
    - >
      ./vendor/bin/php-cs-fixer fix --dry-run --diff --format=checkstyle
      | tee php-style-report.xml
  artifacts:
    when: always
    reports:
      codequality: services/php-service/php-style-report.xml
    expire_in: 1 week

lint:vue:
  extends: .validate_base
  image: node:20-alpine
  script:
    - cd services/frontend
    - npm ci --quiet
    - npm run lint -- --max-warnings=0
    - npx prettier --check "src/**/*.{vue,ts,js}"
  cache:
    key: node-modules-$CI_COMMIT_REF_SLUG
    paths: [services/frontend/node_modules]

lint:terraform:
  extends: .validate_base
  image:
    name: hashicorp/terraform:1.7
    entrypoint: [""]
  script:
    - terraform -chdir=terraform fmt -check -recursive
    - |
      docker run --rm \
        -v $CI_PROJECT_DIR/terraform:/data \
        ghcr.io/terraform-linters/tflint:v0.50 \
        --init && tflint --recursive
  allow_failure: false

lint:dockerfile:
  extends: .validate_base
  image: hadolint/hadolint:latest-debian
  script:
    - >
      hadolint
      services/go-service/Dockerfile
      services/go-service/docker/Dockerfile.debug
      services/php-service/Dockerfile
      services/frontend/Dockerfile
      services/nginx/Dockerfile

lint:yaml:
  extends: .validate_base
  image: pipelinecomponents/yamllint:latest
  script:
    - yamllint -f colored helm/ .gitlab-ci.yml docker-compose.yml

lint:sql:
  extends: .validate_base
  image: sqlfluff/sqlfluff:latest
  script:
    - sqlfluff lint migrations/ --dialect mysql --rules L001,L002,L003,L010,L011
  allow_failure: true   # Stil SQL je manje kritičan od koda

# Agregator — uspijeva samo ako su SVI lint jobovi prošli.
# Svi build jobovi deklariraju needs: [validate:all, ...]
validate:all:
  stage: validate
  image: alpine:3.19
  needs:
    - lint:go
    - lint:php
    - lint:vue
    - lint:terraform
    - lint:dockerfile
    - lint:yaml
  script:
    - echo "All style checks passed"
```

**Napomena uz `lint:terraform`:** U GitLab CI runneri koji koriste Docker-in-Docker (dind) executor, `docker run` unutar joba funkcionira. Ako runner nije dind, zamijeni tflint korak direktnim pozivom tflint image-a kao zasebni CI job ili koristi `services:` blok.

---

## Pre-commit hooks

`.pre-commit-config.yaml` smješten u root repozitorija. Pre-commit je lokalni sloj zaštite — hvata greške prije nego uopće dođe do push-a.

```yaml
repos:
  # Go
  - repo: local
    hooks:
      - id: gofmt
        name: gofmt
        entry: bash -c 'cd services/go-service && gofmt -l -e . | tee /dev/stderr | grep -q . && exit 1 || exit 0'
        language: script
        pass_filenames: false
        files: \.go$

      - id: golangci-lint
        name: golangci-lint
        entry: bash -c 'cd services/go-service && golangci-lint run --fast ./...'
        language: script
        pass_filenames: false
        files: \.go$

  # PHP
  - repo: local
    hooks:
      - id: php-cs-fixer
        name: PHP CS Fixer
        entry: bash -c 'cd services/php-service && ./vendor/bin/php-cs-fixer fix --dry-run --diff'
        language: script
        pass_filenames: false
        files: \.php$

  # Vue.js / TypeScript
  - repo: local
    hooks:
      - id: eslint-vue
        name: ESLint (Vue)
        entry: bash -c 'cd services/frontend && npx eslint --max-warnings=0 src/'
        language: script
        pass_filenames: false
        files: \.(vue|ts|js)$

  # Terraform
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.88.0
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_tflint
        args:
          - --args=--config=__GIT_WORKING_DIR__/terraform/tflint.hcl

  # Hadolint
  - repo: https://github.com/hadolint/hadolint
    rev: v2.12.0
    hooks:
      - id: hadolint

  # Secrets detection
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
```

Instalacija pre-commit (jednom po razvojnoj mašini, sve kroz Docker):

```bash
# Kroz Docker (lokalno ne instaliramo ništa):
docker run --rm \
  -v $(pwd):/repo \
  -w /repo \
  python:3.12-slim \
  sh -c "pip install pre-commit -q && pre-commit install && pre-commit run --all-files"

# Ili via Makefile target:
# make lint  → pokreni sve checkove lokalno
```

> **Podman:** `podman run --rm -v $(pwd):/repo -w /repo python:3.12-slim sh -c "pip install pre-commit -q && pre-commit install && pre-commit run --all-files"`

**Zašto `local` hooks umjesto managed repozitorija za Go/PHP/Vue?**

Jer alati (`golangci-lint`, `php-cs-fixer`, `eslint`) moraju biti dostupni lokalno ili kroz Docker wrapper. Managed pre-commit repozitoriji pretpostavljaju lokalno instaliranu binarku. Za konzistentnost koristimo `language: script` s Docker wrapper komandama.

---

## Auto-fix lokalno jednom komandom

`Makefile` target koji popravlja sve što može biti auto-popravljeno. Devovi pokreću `make lint-fix` lokalno, potom review diff-a, potom commit.

```makefile
.PHONY: lint lint-fix

lint-fix:
	@echo "=== Auto-fixing code style ==="
	# Go
	docker run --rm \
	  -v $(shell pwd)/services/go-service:/app \
	  -w /app \
	  golang:1.22 \
	  gofmt -w .
	# PHP
	docker run --rm \
	  -v $(shell pwd)/services/php-service:/app \
	  -w /app \
	  php:8.3-fpm-alpine \
	  sh -c "cd /app && ./vendor/bin/php-cs-fixer fix"
	# Vue
	docker run --rm \
	  -v $(shell pwd)/services/frontend:/app \
	  -w /app \
	  node:20-alpine \
	  sh -c "cd /app && npm run lint -- --fix && npx prettier --write src/"
	# Terraform
	docker run --rm \
	  -v $(shell pwd)/terraform:/workspace \
	  -w /workspace \
	  hashicorp/terraform:1.7 \
	  fmt -recursive
	@echo "=== Auto-fix complete. Review changes before committing. ==="

lint:
	@echo "=== Checking code style (read-only) ==="
	# Go
	docker run --rm \
	  -v $(shell pwd)/services/go-service:/app \
	  -w /app \
	  golangci/golangci-lint:v1.57 \
	  golangci-lint run ./...
	# PHP
	docker run --rm \
	  -v $(shell pwd)/services/php-service:/app \
	  -w /app \
	  php:8.3-fpm-alpine \
	  sh -c "composer install --quiet && ./vendor/bin/php-cs-fixer fix --dry-run --diff"
	# Vue
	docker run --rm \
	  -v $(shell pwd)/services/frontend:/app \
	  -w /app \
	  node:20-alpine \
	  sh -c "npm ci --quiet && npm run lint -- --max-warnings=0 && npx prettier --check src/"
	# Terraform
	docker run --rm \
	  -v $(shell pwd)/terraform:/workspace \
	  -w /workspace \
	  hashicorp/terraform:1.7 \
	  fmt -check -recursive
	# Dockerfiles
	docker run --rm \
	  -v $(shell pwd):/workspace \
	  -w /workspace \
	  hadolint/hadolint:latest \
	  hadolint \
	    services/go-service/Dockerfile \
	    services/php-service/Dockerfile \
	    services/frontend/Dockerfile \
	    services/nginx/Dockerfile
	@echo "=== All checks passed ==="
```

---

## Redoslijed u pipeline — kompletna slika

```
Push → GitLab CI

Stage 1: validate (parallelno — svi istovremeno)
  lint:go        → OK
  lint:php        → OK
  lint:vue        → OK        Ako BILO KOJI fail → pipeline staje odmah
  lint:terraform  → OK
  lint:dockerfile → OK
  lint:yaml       → OK
  lint:sql        → OK (allow_failure: true)
  validate:all    → OK (agregator)

Stage 2: build (needs: [validate:all])
  build:go-service
  build:php-service
  build:frontend
  build:notification-service

Stage 3: test (needs: build jobovi)
  test:go
  test:php
  security:trivy
  security:sast

Stage 4+: tf-plan → migrate → deploy → verify → ...
```

**Ključna veza:** svaki job u stage 2 deklarira `needs: [validate:all, ...]`. Time se osigurava da build ne može početi dok svi style checkovi ne prođu, čak i ako GitLab runner ima slobodnih slotova.

```yaml
# Primjer build joba s eksplicitnom vezom:
build:go-service:
  stage: build
  needs:
    - validate:all    # ← eksplicitna zavisnost od agregatora
  image: golang:1.22
  script:
    - cd services/go-service
    - go build -o bin/service ./cmd/server/...
```

---

## Troubleshooting

**Problem:** `golangci-lint` traje predugo u CI.

Rješenje: dodaj cache za `.cache` direktorij i koristi `--fast` flag za pre-commit hook (samo subset lintera), puni run ostaje za CI.

```yaml
lint:go:
  cache:
    key: golangci-$CI_COMMIT_REF_SLUG
    paths:
      - services/go-service/.cache/golangci-lint
  variables:
    GOLANGCI_LINT_CACHE: $CI_PROJECT_DIR/services/go-service/.cache/golangci-lint
```

**Problem:** `php-cs-fixer` ne pronalazi `composer` u CI image-u.

Rješenje: koristi dedicirani image koji ima i PHP i Composer:

```yaml
lint:php:
  image: composer:2.7   # Dolazi s PHP + Composer
  script:
    - cd services/php-service
    - composer install --quiet --no-scripts
    - ./vendor/bin/php-cs-fixer fix --dry-run --diff
```

**Problem:** ESLint prolazi lokalno, pada u CI s drugačijim errorima.

Uzrok: razlika u `NODE_ENV`. U CI nije postavljen, pa se `no-console: warn` pretvori u `warn` umjesto `error`. Eksplicitno postavi u CI:

```yaml
lint:vue:
  variables:
    NODE_ENV: production
```

**Problem:** pre-commit hook ne radi za dev koji nema Docker lokalno.

Rješenje: dokumentiraj u onboarding doku da Docker Desktop mora biti instaliran. Pre-commit hookovi koriste Docker, ne lokalne binarne alate — to je intentional i eliminira "radi na mom računalu" probleme.
