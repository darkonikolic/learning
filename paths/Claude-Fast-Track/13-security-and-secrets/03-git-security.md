# Git security

## The git history problem

Git stores every version of every file ever committed. Deleting a file in a new commit does not remove it from history. `git log --all -p` traverses the entire history and can surface any value committed at any point — including secrets deleted years ago.

For public repositories, the situation is worse: search engines index git history. Within minutes of a push, a committed AWS key is scanned by automated tools. The secret is compromised before you have time to act.

**The rule:** a secret that enters git history must be treated as compromised, regardless of whether you later delete it.

**Prevention is the only reliable defense.** Detection and remediation exist, but they are expensive and incomplete compared to preventing the commit.

---

## Pre-commit hooks for secret detection

Pre-commit hooks run before a commit is created. If the hook exits non-zero, the commit is blocked. This is the right place to catch secrets.

### gitleaks

`gitleaks` is the most widely used secret scanner for git. It detects known secret patterns (API key formats, private key headers, connection string patterns) in staged changes.

**Install:**
```bash
brew install gitleaks        # macOS
# or
go install github.com/zricethezav/gitleaks/v8@latest
```

**Run manually on staged changes:**
```bash
gitleaks protect --staged
```

**Install as pre-commit hook:**
```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --exit-code 1
if [ $? -ne 0 ]; then
    echo "Secret detected in staged changes. Commit blocked."
    echo "Review the output above, remove the secret, and try again."
    exit 1
fi
EOF
chmod +x .git/hooks/pre-commit
```

**Test the hook:**
```bash
# Add a fake secret to a file
echo 'var apiKey = "AKIAIOSFODNN7EXAMPLE"' >> main.go
git add main.go
git commit -m "test"
# Expected output: gitleaks blocks the commit
# Remove the test line before continuing
```

**gitleaks config (`.gitleaks.toml`):**

By default, gitleaks uses its built-in ruleset. You can add project-specific rules or allowlists:

```toml
[allowlist]
  description = "Allow test fixtures"
  paths = [
    '''testdata/''',
    '''fixtures/''',
  ]
  regexes = [
    # Allow obviously fake example keys in documentation
    '''EXAMPLE''',
    '''PLACEHOLDER''',
  ]
```

Commit `.gitleaks.toml` to the repository so all team members use the same config.

### detect-secrets (alternative)

```bash
pip install detect-secrets

# Create baseline (marks known false positives as approved)
detect-secrets scan > .secrets.baseline

# Review and approve false positives
detect-secrets audit .secrets.baseline

# In pre-commit hook:
detect-secrets-hook --baseline .secrets.baseline
```

Commit `.secrets.baseline` to the repository. Update it when you add intentional test fixtures that contain fake credentials.

---

## Minimum .gitignore for any project

```
# Secret files
.env
.env.*
.env.local
.env.development
.env.staging
.env.production

# Key material
*.pem
*.key
*.p12
*.pfx
*.jks

# Dependency directories
node_modules/
vendor/         # only if not using Go modules with vendoring

# Build output
bin/
dist/
*.exe

# Editor state
.DS_Store
.idea/
.vscode/
```

Create `.gitignore` before creating any secret files. If the file does not exist when you first create `.env`, you will be prompted to stage `.env` — and it is easy to commit it by mistake.

**Verify gitignore is working:**
```bash
git status      # .env should not appear
git check-ignore -v .env   # should print the matching gitignore rule
```

---

## If a secret was committed

### Immediate response (before anything else)

1. **Revoke the secret.** Go to the credential provider (AWS IAM, GitHub settings, Stripe dashboard, etc.) and revoke or delete the key. Do this before attempting to clean git history — history cleanup takes time and can be interrupted; revocation is fast.

2. **Assess exposure.** Check when the commit was pushed. If the repo is public and the push was more than a few minutes ago, assume the secret was harvested by automated scanners.

### Removing from current code

```bash
# Remove the file from tracking without deleting it locally
git rm --cached .env

# Add to .gitignore
echo ".env" >> .gitignore

# Commit the removal
git commit -m "remove accidentally tracked .env"
```

This removes the file from HEAD but it is still in history.

### Purging from history (private repos only)

For private repos where you can coordinate with the team:

**Using git-filter-repo (preferred over filter-branch):**
```bash
pip install git-filter-repo

# Remove a specific file from all history
git filter-repo --path .env --invert-paths

# Remove a specific string (the secret value) from all content
git filter-repo --replace-text <(echo "sk-actual-key-here==>REDACTED")
```

After filter-repo:
```bash
# Force push all branches (coordinate with team — this rewrites history)
git push origin --force --all
git push origin --force --tags
```

**For public repos:** assume compromised regardless of history rewrite. History rewrite does not undo what was already indexed or harvested.

### Post-cleanup audit

After revoking and cleaning:
- Check access logs at the credential provider for use of the compromised key
- Notify team members to re-clone (their local copies still have old history)
- Document the incident and add the secret pattern to your `.gitleaks.toml` allowlist or detection rules

---

## GitHub secret scanning

GitHub automatically scans public repositories for known credential formats:
- AWS access keys
- GCP service account keys
- GitHub personal access tokens
- Stripe secret keys
- Slack tokens
- Dozens of other provider-specific formats

When a match is found, GitHub:
1. Sends an alert to repository administrators
2. Notifies the credential provider (for partnered providers)
3. The provider may automatically revoke the credential

**For private repos:** enable secret scanning in Settings → Code security → Secret scanning.

**Push protection:** GitHub can block pushes that contain secrets before they are committed to the remote. Enable in Settings → Code security → Secret scanning → Push protection. This is a second line of defense — pre-commit hooks are still the right first line.

---

## task-api setup

task-api has no real secrets in Phase 1–3. Still, set up the hook:

```bash
cd task-api
brew install gitleaks

cat > .git/hooks/pre-commit << 'EOF'
#!/bin/sh
gitleaks protect --staged --exit-code 1
EOF
chmod +x .git/hooks/pre-commit
```

Reason: the hook is easier to install before you need it than after you have already accidentally committed something. Forming the habit on a toy project means it is already present when you add a database connection string in Phase 4.

---

## Checklist

- [ ] I understand why deleting a secret in a new commit does not remove it from git history.
- [ ] gitleaks pre-commit hook is installed and executable in task-api.
- [ ] I have tested the hook by staging a fake secret and confirming it was blocked.
- [ ] .gitignore includes .env and key material before any secret files were created.
- [ ] I can verify .gitignore is working with `git check-ignore -v .env`.
- [ ] I know the correct order of response to a committed secret: revoke first, then clean history.
- [ ] I understand that for public repos, history rewrite does not undo exposure.
- [ ] I know what GitHub secret scanning provides and how to enable push protection.
