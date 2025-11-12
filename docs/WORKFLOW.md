# Git Workflow Quick Reference

## 🚨 Main Branch is Protected

**Never commit directly to `main`** - All changes must go through Pull Requests!

## Quick Start

### 1. Start New Work
```bash
# Update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Changes
```bash
# Edit files...
# Test locally: .\.venv\Scripts\python.exe app.py

# Commit changes
git add .
git commit -m "feat(scope): your change"
git push -u origin feature/your-feature-name
```

### 3. Create PR
```bash
gh pr create --title "Title" --body "Description" --base main
```

### 4. After PR Merged
```bash
git checkout main
git pull origin main
git branch -d feature/your-feature-name
```

## Branch Naming

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation
- `refactor/` - Code refactoring
- `chore/` - Maintenance

## Commit Format

```
type(scope): subject

feat(plaid): add new feature
fix(experian): fix bug
docs(readme): update docs
chore(deps): update dependencies
```

## Common Commands

```bash
# Check current branch
git branch

# View PR list
gh pr list

# Checkout PR locally
gh pr checkout <NUMBER>

# Merge PR (via GitHub UI is better)
gh pr merge <NUMBER> --squash

# Delete merged branch
git branch -d feature/branch-name
```

## Example First PR

You have one open right now:
https://github.com/odanree/credit-history-app/pull/1

Review it, approve it, and merge it to see the workflow in action!

## Need Help?

See full guide: `CONTRIBUTING.md`
