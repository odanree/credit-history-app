# Contributing to Credit History App

## Git Workflow

We use a **PR-based workflow** with branch protection on `main`.

### ⚠️ Never Commit Directly to Main

All changes must go through Pull Requests with code review.

## Development Workflow

### 1. Create a Feature Branch

```bash
# Update main first
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

**Branch Naming Convention:**
- `feature/` - New features (e.g., `feature/add-spending-alerts`)
- `fix/` - Bug fixes (e.g., `fix/transaction-date-parsing`)
- `docs/` - Documentation only (e.g., `docs/update-api-guide`)
- `refactor/` - Code refactoring (e.g., `refactor/cleanup-plaid-client`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

### 2. Make Your Changes

```bash
# Make changes to files
# Test locally
.\.venv\Scripts\python.exe app.py

# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(plaid): add spending alerts feature"
```

### 3. Push to GitHub

```bash
git push origin feature/your-feature-name
```

### 4. Create Pull Request

1. Go to https://github.com/odanree/credit-history-app
2. Click **"Compare & pull request"**
3. Fill in PR template:
   - **Title**: Clear, descriptive (e.g., "Add spending alerts for credit cards")
   - **Description**: What changed and why
   - **Testing**: How you tested it
   - **Screenshots**: If UI changes

### 5. Code Review

- Wait for CI checks to pass ✅
- Address review comments
- Make updates in same branch:
  ```bash
  git add .
  git commit -m "fix: address review feedback"
  git push origin feature/your-feature-name
  ```

### 6. Merge to Main

Once approved:
1. Click **"Squash and merge"** (keeps history clean)
2. Delete branch after merge
3. Pull latest main:
   ```bash
   git checkout main
   git pull origin main
   ```

## Pull Request Template

```markdown
## Description
Brief description of what this PR does

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Refactoring
- [ ] Dependency update

## Changes Made
- List specific changes
- One per line

## Testing
- [ ] Tested locally with Plaid sandbox
- [ ] Tested with Experian (if applicable)
- [ ] No errors in console
- [ ] Dashboard renders correctly

## Checklist
- [ ] No hardcoded credentials
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Error handling in place
- [ ] README.md updated (if needed)
- [ ] .env.example updated (if env vars changed)

## Screenshots (if applicable)
Add screenshots of UI changes
```

## Conventional Commits

Use conventional commit format:

```
type(scope): subject

feat(plaid): add spending alerts
fix(experian): handle token expiry correctly
docs(readme): update deployment instructions
refactor(main): simplify credit summary logic
chore(deps): upgrade flask to v3.1.0
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `style` - Code style (formatting)
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Add/update tests
- `build` - Build system changes
- `ci` - CI/CD changes
- `chore` - Maintenance

**Scopes:**
- `plaid` - Plaid integration
- `experian` - Experian integration
- `dashboard` - Flask dashboard
- `api` - General API
- `deps` - Dependencies

## Code Review Guidelines

### What to Check
- ✅ No API keys or secrets in code
- ✅ Error handling for API calls
- ✅ Type hints on all functions
- ✅ Docstrings with descriptions
- ✅ Follows PEP 8 style
- ✅ No breaking changes without discussion
- ✅ Tests pass (if applicable)

### How to Review
```bash
# Checkout PR branch locally
gh pr checkout <PR_NUMBER>

# Test locally
.\.venv\Scripts\python.exe app.py

# Leave review
gh pr review <PR_NUMBER> --approve
# or
gh pr review <PR_NUMBER> --request-changes --body "Feedback here"
```

## Emergency Hotfixes

For critical production bugs:

```bash
# Create hotfix branch from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-bug-description

# Make fix
# ... edit files ...

# Commit and push
git commit -m "fix: critical bug description"
git push origin hotfix/critical-bug-description

# Create PR with "urgent" label
gh pr create --label urgent --title "Hotfix: Critical Bug"
```

## Branch Protection Rules

The `main` branch is protected with:
- ✅ Require pull request before merging
- ✅ Require status checks to pass (CI)
- ✅ Require conversation resolution before merging
- ⚠️ No direct commits to main
- ⚠️ No force pushes

## Local Development Best Practices

### Before Starting Work
```bash
# Always start from latest main
git checkout main
git pull origin main
git checkout -b feature/new-work
```

### Keep Branch Updated
```bash
# Periodically sync with main
git checkout main
git pull origin main
git checkout feature/your-branch
git merge main
```

### Clean Up Old Branches
```bash
# List branches
git branch -a

# Delete local branch
git branch -d feature/old-branch

# Delete remote branch
git push origin --delete feature/old-branch
```

## Questions?

- Check existing PRs for examples
- Ask in PR comments
- Review CONTRIBUTING.md (this file)
