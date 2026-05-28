# 06 — Playwright E2E

## Playwright u Docker: nema lokalnih instalacija

Playwright dolazi s vlastitim browser binarijima (Chromium, Firefox, WebKit). Ovi binariji ovise o sistemu library-jima koje developer mašina može imati ili ne mora imati.

Microsoft održava official Playwright Docker image koji ima sve systemske dependencije pre-instalirane:

```dockerfile
# tests/e2e/Dockerfile

FROM mcr.microsoft.com/playwright:v1.42.0-jammy

WORKDIR /tests

# Kopiraj samo package fajlove prvo (layer cache)
COPY package.json package-lock.json playwright.config.ts ./

# npm ci: determiniran install iz package-lock.json
# Za razliku od npm install, nikad ne mijenja lockfile
RUN npm ci

# Kopiraj test fajlove
COPY tests/ tests/
COPY fixtures/ fixtures/

# Default command: pokrni sve testove
CMD ["npx", "playwright", "test"]
```

`v1.42.0-jammy` — specifična verzija. Ne koristiti `latest`. Playwright browser API se mijenja između verzija i testovi mogu početi padati ako se image promijeni bez tvog znanja.

---

## `playwright.config.ts`

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  
  // Timeout po test (ne po assertion)
  timeout: 30000,
  
  // Retry failed tests — važno za E2E koji ovisi o network timing
  // U CI: 2 retries. Lokalno: 0 (hoćeš odmah vidjeti failure)
  retries: process.env.CI ? 2 : 0,
  
  // Broj paralelnih worker-a
  // U CI: 1 worker jer runner može biti ograničen resursima
  // Lokalno: automatski (po CPU core-ovima)
  workers: process.env.CI ? 1 : undefined,
  
  // Output formati
  reporter: [
    ['junit', { outputFile: 'junit.xml' }],    // Za GitLab artifacts
    ['html', { open: 'never' }],                // HTML report za browsanje
    ['list'],                                    // Console output
  ],
  
  use: {
    // Base URL iz environment varijable — različit po okruženju
    baseURL: process.env.APP_URL || 'http://localhost:3000',
    
    // Screenshot samo kad test padne
    screenshot: 'only-on-failure',
    
    // Video snimanje: zadrži samo za failing testove
    video: 'retain-on-failure',
    
    // Trace (network, screenshot sekvenca, console log): samo za failing
    trace: 'retain-on-failure',
    
    // Ignore HTTPS certificate errors u dev/review okruženjima
    ignoreHTTPSErrors: true,
    
    // Globalni timeout za svaki action (click, fill, expect)
    actionTimeout: 10000,
  },
  
  // Projekti = browser konfiguracije
  // Za MVP: samo Chromium. Dodati Firefox/WebKit kad je potrebno.
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Za mobile testing:
    // {
    //   name: 'mobile-chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
  ],
});
```

`retries: 2` u CI-ju je kompromis. E2E testovi su inherentno flaky zbog network timing, animation, eventual consistency. 2 retries znači: test koji pade zbog timing-a ima 2 šanse da prođe. Legitimni bug treba pasti sva 3 puta. Ako test prolazi tek na 3. pokušaj — to je signal za popravak testa.

---

## Login test (`tests/auth.spec.ts`)

```typescript
import { test, expect, Page } from '@playwright/test';

// Shared setup koji se pokreće jednom po test file-u (ne po testu)
// Korisno za login koji je potreban za sve testove u fajlu
test.beforeEach(async ({ page }) => {
  // Svaki test počinje s čistom sesijom
  await page.context().clearCookies();
});

test('successful login shows hello world', async ({ page }) => {
  await page.goto('/');
  
  // data-testid atributi su stabilni — ne ovise o CSS klasi ili tekstu
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'testpassword');
  await page.click('[data-testid="login-button"]');
  
  // Playwright automatski čeka da element bude vidljiv
  // timeout je iz config-a (actionTimeout: 10000)
  await expect(page.locator('[data-testid="welcome-message"]'))
    .toContainText('Hello World');
  
  // URL provjera — redirect nakon login-a
  await expect(page).toHaveURL('/dashboard');
});

test('invalid credentials shows error', async ({ page }) => {
  await page.goto('/');
  
  await page.fill('[data-testid="email"]', 'wrong@example.com');
  await page.fill('[data-testid="password"]', 'wrongpass');
  await page.click('[data-testid="login-button"]');
  
  // Provjera da error message postoji I da je vidljiv
  const errorMessage = page.locator('[data-testid="error-message"]');
  await expect(errorMessage).toBeVisible();
  await expect(errorMessage).toContainText('Invalid credentials');
  
  // Provjera da nismo redirectovani — ostali smo na login stranici
  await expect(page).toHaveURL('/');
});

test('shows validation error for empty email', async ({ page }) => {
  await page.goto('/');
  
  // Klikni submit bez unosa
  await page.fill('[data-testid="password"]', 'somepassword');
  await page.click('[data-testid="login-button"]');
  
  await expect(page.locator('[data-testid="email-error"]'))
    .toContainText('Email is required');
});

test('redirects to login if accessing protected route unauthenticated', async ({ page }) => {
  // Direktan pristup protected route-u bez login-a
  await page.goto('/dashboard');
  
  // Treba biti redirectovan na login
  await expect(page).toHaveURL('/');
});
```

### Page Object Model za kompleksnije testove

Za aplikacije s više stranica, Page Object Model (POM) eliminira duplikaciju:

```typescript
// tests/pages/LoginPage.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/');
  }

  async login(email: string, password: string) {
    await this.page.fill('[data-testid="email"]', email);
    await this.page.fill('[data-testid="password"]', password);
    await this.page.click('[data-testid="login-button"]');
  }

  async getErrorMessage(): Promise<string | null> {
    const el = this.page.locator('[data-testid="error-message"]');
    return el.isVisible() ? el.textContent() : null;
  }
}

// tests/auth.spec.ts — čistiji testovi s POM
test('login flow', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('test@example.com', 'testpassword');
  await expect(page).toHaveURL('/dashboard');
});
```

---

## `data-testid` atributi: zašto i kako

E2E testovi se mogu oslanjati na:
1. CSS selektori: `.login-btn`, `#email-input` — mijenjaju se pri stilskim refaktorima
2. Tekst: `page.getByText('Login')` — mijenjaju se pri prijevodima ili copy izmjenama
3. ARIA role + label: `page.getByRole('button', { name: 'Login' })` — dobro, ali ovisi o accessibility implementaciji
4. `data-testid`: stabilni atributi čija jedina svrha je testiranje

```html
<!-- U Vue komponenti -->
<template>
  <form @submit.prevent="handleSubmit">
    <input
      data-testid="email"
      v-model="email"
      type="email"
      placeholder="Email"
    />
    <input
      data-testid="password"
      v-model="password"
      type="password"
      placeholder="Password"
    />
    <button data-testid="login-button" type="submit">
      Login
    </button>
    <p v-if="error" data-testid="error-message">{{ error }}</p>
  </form>
</template>
```

`data-testid` atributi se uklanjaju iz production builda u Vite konfiguraciji:

```typescript
// vite.config.ts
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    // Ukloni data-testid iz production HTML-a
    // (ne šalje se klijentu, ne eksponira test surface)
    ...(process.env.NODE_ENV === 'production'
      ? [removeDataTestIdPlugin()]
      : []),
  ],
})
```

---

## Test korisnik i test data isolation

Playwright testovi u review app-u trebaju test korisnika koji je dostupan u svakom review okruženju.

```bash
# Kreiran pri env bootstrapu (Terraform provisioning ili K8s job)
# NE kreiran ručno, NE enak prod korisnicima

# SQL koji se izvršava pri bootstrap-u svakog review env-a:
INSERT INTO users (email, password_hash, is_test_account, created_at)
VALUES (
  'e2e-test@review.internal',
  '$2y$12$...',  # bcrypt hash od test password-a, iz CI/CD secrets
  true,
  NOW()
);
```

Test password u CI/CD:
```yaml
# .gitlab-ci.yml
e2e:review:
  variables:
    APP_URL: "https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com"
    E2E_TEST_EMAIL: "e2e-test@review.internal"
    E2E_TEST_PASSWORD: $E2E_TEST_PASSWORD  # iz GitLab CI/CD Variables (masked)
```

```typescript
// tests/auth.spec.ts
test('successful login', async ({ page }) => {
  await page.goto('/');
  await page.fill('[data-testid="email"]', process.env.E2E_TEST_EMAIL!);
  await page.fill('[data-testid="password"]', process.env.E2E_TEST_PASSWORD!);
  // ...
});
```

Nikad ne hardkodiraj credentials u test fajlovima. Git history je zauvijek.

---

## GitLab CI E2E job

```yaml
e2e:review:
  stage: e2e
  image: mcr.microsoft.com/playwright:v1.42.0-jammy
  needs:
    - job: deploy:review
      artifacts: false  # ne trebamo artifacts od deploy job-a
  variables:
    APP_URL: "https://mr-$CI_MERGE_REQUEST_IID.dev.firma.com"
    E2E_TEST_EMAIL: "e2e-test@review.internal"
    E2E_TEST_PASSWORD: $E2E_TEST_PASSWORD  # masked CI/CD variable
    CI: "true"  # aktivira CI mode u playwright.config.ts
  script:
    - cd tests/e2e
    - npm ci
    - npx playwright test
  after_script:
    # Zip playwright HTML report za lakši download
    - cd tests/e2e && zip -r playwright-report.zip playwright-report/ || true
  artifacts:
    when: always
    reports:
      junit: tests/e2e/junit.xml
    paths:
      - tests/e2e/playwright-report/
      - tests/e2e/playwright-report.zip
    expire_in: 1 week
  rules:
    - if: $CI_MERGE_REQUEST_IID
  retry:
    max: 1           # retry cijeli job jednom ako pane
    when:
      - script_failure
      - runner_system_failure
```

`when: always` za artifacts — kritično. Playwright screenshots i video postoje samo kad test padne. Ako ne sačuvaš artifacts pri failure-u, nemaš dokaz o tome šta se desilo.

`retry: max: 1` — razlikuje se od Playwright `retries` config. Playwright retry je retry pojedinog testa unutar job-a. GitLab job retry je restart cijelog job-a. Job retry je za infrastructure failures (runner timeout, network izpad). Test retry je za flaky testove.

---

## Playwright Trace Viewer

Kad test padne i imaš `trace: 'retain-on-failure'`, dobijete `.zip` fajl koji možete otvoriti u trace viewer-u:

```bash
# Lokalno
npx playwright show-trace tests/e2e/test-results/trace.zip

# Ili online: trace.playwright.dev
```

Trace sadrži:
- Screenshot svake network request
- DOM snapshot pri svakom koraku
- Console log i network log
- Točan timestamp svake akcije

Za debugging E2E failure-a iz CI-ja — preuzmeš artifact, otvoris trace, vidiš tačno šta se desilo.
