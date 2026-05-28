# 06 — Lokalni razvoj bez Secrets Manager

## Princip: identičan kod, različit source

Cilj je da aplikacijski kod **ne zna** da li čita credentials iz SM ili iz lokalnog env var fajla. Razlika je u konfiguraciji, ne u logici.

### .env.local — jedini izvor lokalne konfiguracije

```bash
# .env.local (NIKAD u git — .gitignore obavezno)

# Database
DB_HOST=localhost
DB_PORT=3306
DB_NAME=project_a_dev
DB_USER=dev_user
DB_PASSWORD=dev-local-password-not-secret

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_AUTH_TOKEN=dev-redis-auth-local

# JWT
JWT_SECRET=dev-jwt-secret-min-32-chars-long-ok

# PHP session
SESSION_SECRET=dev-session-secret-min-32-chars

# External APIs — uvijek koristiti sandbox/test keys lokalno
STRIPE_KEY=sk_test_xxxxxxxxxxxxxxxxxxxx
SENDGRID_KEY=SG.test_key_local_development

# Indikator za aplikaciju da ne koristi SM
# Kada ovo nije postavljeno (ili je prazan string), app koristi SM
AWS_REGION=
```

`.gitignore` — obavezni unosi:

```gitignore
# Secrets — NIKAD ne commitovati
.env.local
.env.*.local
.env.production
.env.prod
*.pem
*.key
!*.key.example
kubeconfig
kubeconfig.yaml
terraform.tfvars
!terraform.tfvars.example
.terraform/
*.tfstate
*.tfstate.backup
.terraform.lock.hcl
```

`.env.example` — commitovati sa fake vrijednostima:

```bash
# .env.example — commitovati u git, koristiti kao template
# Kopirati u .env.local i popuniti pravim dev vrijednostima

DB_HOST=localhost
DB_PORT=3306
DB_NAME=project_a_dev
DB_USER=dev_user
DB_PASSWORD=REPLACE_WITH_LOCAL_DEV_PASSWORD

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_AUTH_TOKEN=REPLACE_WITH_LOCAL_REDIS_AUTH

JWT_SECRET=REPLACE_WITH_32_CHAR_MIN_SECRET_KEY
SESSION_SECRET=REPLACE_WITH_32_CHAR_MIN_SESSION_KEY

STRIPE_KEY=sk_test_REPLACE_WITH_STRIPE_TEST_KEY
SENDGRID_KEY=SG.REPLACE_WITH_SENDGRID_TEST_KEY

AWS_REGION=
```

---

## Docker Compose sa .env.local

```yaml
# docker-compose.yml

services:
  go-service:
    build:
      context: ./go-service
      target: development
    env_file:
      - .env.local    # Čita sve varijable iz fajla
    ports:
      - "8080:8080"
    volumes:
      - ./go-service:/app
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy

  php-service:
    build:
      context: ./php-service
      target: development
    env_file:
      - .env.local
    ports:
      - "9000:9000"
    volumes:
      - ./php-service:/var/www/html
    depends_on:
      - go-service

  nginx:
    image: nginx:1.25.3-alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/dev.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - php-service

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root-local-only
      MYSQL_DATABASE: project_a_dev
      MYSQL_USER: dev_user
      MYSQL_PASSWORD: dev-local-password-not-secret
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass dev-redis-auth-local
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "dev-redis-auth-local", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  mysql_data:
```

---

## Go pattern: env var sa SM fallback

```go
// internal/config/config.go

type Config struct {
    DBPassword      string
    RedisAuthToken  string
    JWTSecret       string
    SessionSecret   string
}

// LoadConfig učitava konfiguraciju.
// Ako AWS_REGION je postavljen, koristi SM za production credentials.
// Lokalno (bez AWS_REGION), čita direktno iz env vars.
func LoadConfig(ctx context.Context) (*Config, error) {
    awsRegion := os.Getenv("AWS_REGION")

    if awsRegion == "" {
        // Lokalni razvoj — čitaj env vars direktno
        return loadFromEnv()
    }

    // Produkcija — čitaj iz SM via ESO K8s Secrets (env vars su populirani od ESO)
    // ili direktno iz SM ako IRSA je konfigurisan
    return loadFromEnv()  // K8s env vars koje je postavio ESO su identični lokalnima
}

func loadFromEnv() (*Config, error) {
    cfg := &Config{
        DBPassword:     requireEnv("DB_PASSWORD"),
        RedisAuthToken: requireEnv("REDIS_AUTH_TOKEN"),
        JWTSecret:      requireEnv("JWT_SECRET"),
        SessionSecret:  requireEnv("SESSION_SECRET"),
    }
    return cfg, nil
}

func requireEnv(key string) string {
    val := os.Getenv(key)
    if val == "" {
        // Fail fast: bolje panic pri startu nego tiha greška pri prvom requestu
        panic(fmt.Sprintf("required environment variable %s is not set", key))
    }
    return val
}
```

U produkciji, ESO kreira K8s Secret čije vrijednosti se injektuju kao env vars — identično lokalnom `.env.local`. Aplikacijski kod je isti, samo source je drugačiji.

### Opciona SM direktna integracija (bez ESO)

Ako iz nekog razloga ne koristite ESO i aplikacija direktno čita SM:

```go
// internal/config/secrets.go

func loadSecret(ctx context.Context, secretPath string) (string, error) {
    // Lokalno: env var sa konvertovanim imenom
    // /project-a/dev/go-service/jwt-secret → PROJECT_A_DEV_GO_SERVICE_JWT_SECRET
    if os.Getenv("AWS_REGION") == "" {
        envKey := secretPathToEnvKey(secretPath)
        if val := os.Getenv(envKey); val != "" {
            return val, nil
        }
        // Fallback na direktno ime (za jednostavnost lokalnog deva)
        parts := strings.Split(secretPath, "/")
        simpleName := strings.ToUpper(strings.ReplaceAll(parts[len(parts)-1], "-", "_"))
        return requireEnv(simpleName), nil
    }

    // Produkcija: čitaj SM
    client := secretsmanager.NewFromConfig(mustLoadAWSConfig(ctx))
    result, err := client.GetSecretValue(ctx, &secretsmanager.GetSecretValueInput{
        SecretId: aws.String(secretPath),
    })
    if err != nil {
        return "", fmt.Errorf("failed to get secret %s: %w", secretPath, err)
    }
    return *result.SecretString, nil
}

func secretPathToEnvKey(path string) string {
    // /project-a/dev/go-service/jwt-secret → JWT_SECRET
    parts := strings.Split(strings.Trim(path, "/"), "/")
    return strings.ToUpper(strings.ReplaceAll(parts[len(parts)-1], "-", "_"))
}
```

---

## PHP pattern: isti pristup

```php
<?php
// src/Config/SecretsConfig.php

class SecretsConfig
{
    private static array $cache = [];

    public static function get(string $key): string
    {
        if (isset(self::$cache[$key])) {
            return self::$cache[$key];
        }

        $value = self::resolve($key);

        if (empty($value)) {
            throw new RuntimeException("Required config key '{$key}' is not set");
        }

        self::$cache[$key] = $value;
        return $value;
    }

    private static function resolve(string $key): string
    {
        // Uvijek čitaj iz env vara
        // Lokalno: .env.local via docker-compose env_file
        // Produkcija: K8s Secret injektan od ESO kao env var
        $value = getenv($key);

        if ($value === false || $value === '') {
            throw new RuntimeException(
                "Environment variable '{$key}' is not set. " .
                "Copy .env.example to .env.local and fill in values."
            );
        }

        return $value;
    }
}

// Korišćenje
$dbPassword  = SecretsConfig::get('DB_PASSWORD');
$redisToken  = SecretsConfig::get('REDIS_AUTH_TOKEN');
$jwtSecret   = SecretsConfig::get('JWT_SECRET');
```

---

## LocalStack — simulacija SM lokalno (opciono)

```yaml
# docker-compose.localstack.yml (opciono, za SM testing lokalno)
services:
  localstack:
    image: localstack/localstack:3.0
    ports:
      - "4566:4566"
    environment:
      SERVICES: secretsmanager,sts
      DEFAULT_REGION: eu-west-1
      AWS_DEFAULT_REGION: eu-west-1
    volumes:
      - ./scripts/localstack-init.sh:/etc/localstack/init/ready.d/init.sh

  go-service-sm-test:
    build: ./go-service
    environment:
      AWS_REGION: eu-west-1
      AWS_ENDPOINT_URL: http://localstack:4566
      AWS_ACCESS_KEY_ID: test
      AWS_SECRET_ACCESS_KEY: test
    depends_on:
      - localstack
```

```bash
#!/bin/bash
# scripts/localstack-init.sh — kreira test secrets pri startu

export AWS_DEFAULT_REGION=eu-west-1

aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name /project-a/dev/rds/app-user-password \
    --secret-string '{"username":"appuser","password":"dev-test-password","host":"mysql","port":3306,"dbname":"project_a"}'

aws --endpoint-url=http://localhost:4566 secretsmanager create-secret \
    --name /project-a/dev/redis/auth-token \
    --secret-string "dev-redis-auth-local"

echo "LocalStack secrets initialized"
```

LocalStack je koristan za testiranje koda koji direktno koristi SM SDK. Nije potreban ako koristite ESO pattern — tada se testira samo K8s environment simulacija.

---

## Onboarding novog developera — checklist

```bash
#!/bin/bash
# scripts/dev-setup.sh

set -e

echo "=== Project-A Dev Setup ==="

# 1. Provjeriti prerequisites
command -v docker >/dev/null || { echo "ERROR: docker not found"; exit 1; }
command -v docker-compose >/dev/null || { echo "ERROR: docker-compose not found"; exit 1; }

# 2. Kreirati .env.local iz template-a
if [ ! -f .env.local ]; then
    cp .env.example .env.local
    echo "Created .env.local from template. Please fill in values before continuing."
    echo "See: docs/LOCAL_SETUP.md for where to find dev credentials."
    exit 1
fi

# 3. Instalirati pre-commit hooks
if command -v pre-commit >/dev/null; then
    pre-commit install
    echo "Pre-commit hooks installed"
else
    echo "WARNING: pre-commit not installed. Run: pip install pre-commit && pre-commit install"
fi

# 4. Instalirati gitleaks
if ! command -v gitleaks >/dev/null; then
    echo "WARNING: gitleaks not installed. Run: brew install gitleaks"
fi

# 5. Verifikacija .env.local ne sadrži produzione vrijednosti
if grep -q "sk_live_" .env.local; then
    echo "ERROR: .env.local contains production Stripe key (sk_live_). Use test key (sk_test_)."
    exit 1
fi

echo "=== Dev setup complete. Run: docker-compose up ==="
```

---

## Expert tip: secret rotation u lokalnom testu

Kada lokalno testirate rotaciju logiku, koristiti kratki refresh interval i mock SM:

```go
// go-service/internal/config/config_test.go

func TestSecretRefreshOnAuthError(t *testing.T) {
    // Mock SM koji vraća različite passwords pri uzastopnim pozivima
    callCount := 0
    mockSM := &MockSecretsManager{
        GetSecretValueFn: func(ctx context.Context, input *secretsmanager.GetSecretValueInput) (*secretsmanager.GetSecretValueOutput, error) {
            callCount++
            password := "old-password"
            if callCount > 1 {
                password = "new-password"
            }
            return &secretsmanager.GetSecretValueOutput{
                SecretString: aws.String(fmt.Sprintf(`{"password": "%s"}`, password)),
            }, nil
        },
    }

    pool := NewDBPool(mockSM, testSecretARN)
    
    // Simulirati auth error → pool treba refreshati credentials
    err := pool.handleAuthError(context.Background())
    
    assert.NoError(t, err)
    assert.Equal(t, 2, callCount, "SM should be called twice: initial + refresh")
    assert.Equal(t, "new-password", pool.currentPassword())
}
```
