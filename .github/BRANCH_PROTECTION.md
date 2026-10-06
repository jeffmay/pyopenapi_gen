# Branch Protection Configuration

This document outlines the GitHub branch protection settings for `develop`, the default and only long-lived branch. All pull requests target `develop`, all CI runs against it, and releases are cut from it (see [Release Process](../docs/release-automation.md)).

## Required Settings

### Branch Protection Rules for `develop`

1. **Require pull request reviews before merging**
   - Required approving reviews: 1
   - Dismiss stale reviews when new commits are pushed: ✅
   - Require review from code owners: ✅ (if CODEOWNERS file exists)

2. **Require status checks to pass before merging**
   - Require branches to be up to date before merging: ✅
   - Required status checks:
     - `quality-checks` (Black, Ruff, mypy, and the test suite with 85% coverage)
     - `security-scan` (pip-audit and Bandit)
     - `integration-tests` (integration tests and CLI generation smoke test)
     - `test` (placeholder check from `ci.yml`)

3. **Require conversation resolution before merging**: ✅

4. **Require signed commits**: ❌ (optional)

5. **Require linear history**: ❌ (optional)

6. **Allow the release identity to bypass the above settings**: ✅ (everyone else: ❌)

7. **Restrict pushes that create files**: ❌

8. **Allow force pushes**: ❌

9. **Allow deletions**: ❌

## 🔒 Protection Features

### Release Pushes
The release workflow (`semantic-release.yml`) pushes a `chore(release): X.Y.Z` commit and a `vX.Y.Z` tag directly to `develop`, without a pull request. The identity behind the `SEMANTIC_RELEASE_TOKEN` secret must therefore be able to bypass the pull request requirement, for example as a bypass actor on a repository ruleset, or as an admin with "Do not allow bypassing the above settings" left unchecked. Nobody else should be able to push to `develop` directly.

### Deletion Protection
`develop` is protected from accidental deletion:
- Force pushes are disabled
- Branch deletion is explicitly forbidden

### Quality Gates
Every PR must pass all quality checks:
- Code formatting (Black)
- Linting (Ruff) 
- Type checking (MyPy strict mode)
- Security scanning (Bandit)
- Test suite with 85% coverage minimum

## How to Configure

### Via GitHub Web Interface

1. Go to your repository on GitHub
2. Click on **Settings** → **Branches**
3. Click **Add rule** or edit existing rule for `develop`
4. Configure the settings as outlined above
5. Save the branch protection rule

### Via GitHub CLI

```bash
# Create protection JSON. enforce_admins is false so an admin-owned
# SEMANTIC_RELEASE_TOKEN can push the release commit and tag.
cat > branch_protection.json << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["quality-checks", "security-scan", "integration-tests", "test"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false
  },
  "restrictions": null,
  "allow_deletions": false,
  "allow_force_pushes": false
}
EOF

gh api --method PUT repos/OWNER/REPO/branches/develop/protection --input branch_protection.json
```

## Quality Gates Enforced

The pipeline enforces the following quality gates:

### Code Quality
- ✅ **Black formatting**: Code must be properly formatted
- ✅ **Ruff linting**: No linting errors allowed
- ✅ **MyPy type checking**: Strict type checking must pass

### Testing
- ✅ **Unit tests**: All tests must pass
- ✅ **Integration tests**: End-to-end functionality verified
- ✅ **Coverage**: Minimum 85% test coverage required
- ✅ **Python version**: Tests on Python 3.12+

### Security
- ✅ **Safety check**: No known vulnerabilities in dependencies
- ✅ **Bandit scan**: Security linting for common issues

### Functionality
- ✅ **CLI functionality**: Command-line interface works correctly
- ✅ **Client generation**: Generated clients have proper structure

## Workflow Files

- `.github/workflows/pr-checks.yml`: Quality, security, and integration checks on PRs to `develop`
- `.github/workflows/ci.yml`: Placeholder `test` check on PRs and pushes to `develop`
- `.github/workflows/semantic-release.yml`: Cuts a release on pushes to `develop`
- `.github/workflows/dependabot-poetry-lock-fix.yml`: Resolves `poetry.lock` conflicts on Dependabot PRs

## Local Development

Before creating a PR, run locally to ensure it will pass CI:

```bash
# Activate virtual environment
source .venv/bin/activate

# Auto-fix what's possible
make quality-fix

# Verify all quality gates pass (exactly matches CI pipeline)
make quality

# Run tests with coverage
make test-cov
```

### Individual Commands (if needed)

```bash
# Quality checks (matches CI pipeline exactly)
make format-check         # Black formatting check
make lint                 # Ruff linting check  
make typecheck            # mypy type checking
make security             # Bandit security scanning

# Testing
make test                 # Run all tests
make test-fast            # Stop on first failure (for debugging)

# Auto-fixes
make format               # Auto-format with Black
make lint-fix             # Auto-fix linting with Ruff
```

### Why Use Make Commands?

The `make` commands ensure you're running **exactly** the same checks as the CI pipeline. This prevents the "works locally but fails in CI" problem and provides fast feedback during development.