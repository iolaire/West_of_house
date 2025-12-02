# Git Workflow Guide

## Branch Strategy

This project uses a two-branch workflow optimized for AWS Amplify deployments:

### `main` Branch (Development)
- **Purpose**: Active development and testing
- **Usage**: All day-to-day development work
- **Deployment**: Does NOT trigger AWS deployments
- **Freedom**: Safe to experiment, iterate, and test

### `production` Branch (Deployment)
- **Purpose**: Production deployments to AWS Amplify
- **Usage**: Only for deploying tested changes
- **Deployment**: Automatically triggers AWS Amplify deployment on push
- **Stability**: Should always be in a deployable state

## Standard Development Workflow

### 1. Daily Development (on `main`)

```bash
# Ensure you're on main branch
git checkout main
git pull origin main

# Make your changes
# ... edit files ...

# Commit changes
git add .
git commit -m "Descriptive commit message"

# Push to main (does NOT deploy)
git push origin main
```

**Key Points:**
- ✅ Work freely on `main` without triggering deployments
- ✅ Commit frequently with clear messages
- ✅ Push to `main` to backup your work
- ✅ Test locally before deploying

### 2. Deploying to Production

When you're ready to deploy tested changes to AWS:

```bash
# Switch to production branch
git checkout production

# Merge all changes from main
git merge main --no-edit

# Push to trigger Amplify deployment
git push origin production
```

**What Happens:**
1. 🚀 AWS Amplify detects the push to `production`
2. 🔨 Builds the backend infrastructure (TypeScript → CloudFormation)
3. 📦 Deploys Lambda functions, DynamoDB tables, API Gateway
4. ✅ Updates production environment with new changes

**Monitoring Deployment:**
- Check AWS Amplify Console for deployment status
- Typical deployment time: 5-12 minutes
- Watch for build/deploy phase completion

### 3. Post-Deployment Sync

After successful deployment, sync `main` with `production`:

```bash
# Switch back to main
git checkout main

# Merge any production-specific changes
git merge production

# Push updated main
git push origin main
```

**Why This Step:**
- Keeps branches in sync
- Captures any production-specific configurations
- Maintains clean git history

## Common Scenarios

### Scenario 1: Quick Fix to Production

```bash
# Work on main
git checkout main
# ... make fix ...
git add .
git commit -m "Fix: description of fix"
git push origin main

# Deploy immediately
git checkout production
git merge main
git push origin production

# Sync back
git checkout main
git merge production
```

### Scenario 2: Multiple Features Before Deploy

```bash
# Feature 1
git checkout main
# ... work ...
git commit -m "Feature 1: description"
git push origin main

# Feature 2
# ... work ...
git commit -m "Feature 2: description"
git push origin main

# Feature 3
# ... work ...
git commit -m "Feature 3: description"
git push origin main

# Deploy all features together
git checkout production
git merge main
git push origin production
```

### Scenario 3: Rollback Production

If deployment fails or has issues:

```bash
# On production branch
git checkout production

# Revert to previous commit
git revert HEAD

# Or reset to specific commit
git reset --hard <previous-commit-hash>

# Force push (use with caution!)
git push origin production --force
```

### Scenario 4: Check What's Different

Before deploying, see what will change:

```bash
# Compare main and production
git diff production..main

# See commit log differences
git log production..main --oneline

# Count commits ahead
git rev-list --count production..main
```

## Best Practices

### ✅ DO

- **Commit frequently** on `main` with clear messages
- **Test locally** before merging to `production`
- **Use descriptive commit messages** for deployment tracking
- **Keep branches in sync** after deployments
- **Review changes** before deploying (use `git diff`)
- **Monitor deployments** in AWS Amplify Console

### ❌ DON'T

- **Never commit directly to `production`** - always merge from `main`
- **Don't push to `production`** unless ready to deploy
- **Don't merge untested code** to `production`
- **Don't force push to `production`** unless emergency rollback
- **Don't skip the post-deployment sync** step

## Useful Git Commands

### Branch Management

```bash
# Check current branch
git branch

# See all branches (local and remote)
git branch -a

# Switch branches
git checkout main
git checkout production

# See branch status
git status
```

### Viewing History

```bash
# Visual commit history
git log --oneline --graph --all --decorate -10

# See what changed in last commit
git show HEAD

# Compare branches
git diff production..main

# Count commits between branches
git rev-list --count production..main
```

### Syncing

```bash
# Update local branch from remote
git pull origin main

# Fetch all remote changes
git fetch --all

# See remote branch status
git remote show origin
```

### Emergency Commands

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes)
git reset --hard HEAD~1

# Revert a specific commit
git revert <commit-hash>

# Stash changes temporarily
git stash
git stash pop
```

## Deployment Checklist

Before deploying to production:

- [ ] All changes committed to `main`
- [ ] Local tests passing
- [ ] Code reviewed (if team project)
- [ ] No syntax errors (`npx tsc --noEmit`)
- [ ] Ready to deploy to AWS
- [ ] Monitoring plan in place

After deployment:

- [ ] Deployment succeeded in Amplify Console
- [ ] Resources created/updated correctly
- [ ] API endpoints responding
- [ ] No errors in CloudWatch Logs
- [ ] `main` branch synced with `production`

## Troubleshooting

### "Your branch is behind 'origin/production'"

```bash
git checkout production
git pull origin production
git merge main
git push origin production
```

### "Merge conflict"

```bash
# See conflicting files
git status

# Edit files to resolve conflicts
# ... fix conflicts ...

# Mark as resolved
git add <resolved-files>
git commit -m "Resolve merge conflicts"
```

### "Deployment failed"

1. Check Amplify Console for error details
2. Fix issues on `main` branch
3. Test locally
4. Redeploy:
   ```bash
   git checkout production
   git merge main
   git push origin production
   ```

## Summary

**Simple Rule**: 
- 🔧 **Develop on `main`** (safe, no deployments)
- 🚀 **Deploy from `production`** (triggers AWS deployment)
- 🔄 **Keep them in sync** (merge after deployments)

This workflow gives you:
- Freedom to experiment on `main`
- Control over when deployments happen
- Clear separation of development and production
- Easy rollback if needed
- Clean git history
