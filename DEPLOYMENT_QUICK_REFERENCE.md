# Deployment Quick Reference

Quick commands for deploying the Grimoire Frontend to AWS Amplify.

## Standard Deployment Workflow

```bash
# 1. Develop on main branch
git checkout main
git pull origin main
# ... make changes ...
git add .
git commit -m "Feature: description"
git push origin main

# 2. Deploy to production
git checkout production
git merge main --no-edit
git push origin production

# 3. Sync branches after deployment
git checkout main
git merge production
git push origin main
```

## Local Testing

```bash
# Run development server
npm run dev

# Build for production (test locally)
npm run build
npm run preview

# Run tests
npm test

# Run E2E tests
npm run test:e2e
```

## Sandbox Testing

```bash
# Start sandbox environment (creates isolated AWS resources)
npx ampx sandbox

# In another terminal, run frontend
npm run dev
```

## Deployment Verification

```bash
# Check git status
git status
git log --oneline --graph --all --decorate -10

# Compare branches before deploying
git diff production..main

# Count commits to deploy
git rev-list --count production..main
```

## Rollback

```bash
# Revert last deployment
git checkout production
git revert HEAD
git push origin production

# Reset to specific commit (use with caution)
git reset --hard <commit-hash>
git push origin production --force
```

## Monitoring

- **Amplify Console**: https://console.aws.amazon.com/amplify/
- **CloudWatch Logs**: https://console.aws.amazon.com/cloudwatch/
- **Cost Explorer**: https://console.aws.amazon.com/cost-management/

## Environment Variables

- `.env.development` - Local development settings
- `.env.production` - Production build settings
- `.env.local` - Local overrides (gitignored)

## Build Configuration

- `amplify.yml` - Amplify build configuration
- `vite.config.ts` - Vite build settings
- `package.json` - Build scripts and dependencies

## Common Issues

**Build fails**: Check Amplify Console logs
**Images not loading**: Verify `public/images/` directory
**API errors**: Check `amplify_outputs.json` configuration
**Session issues**: Clear localStorage in browser

## Cost Monitoring

```bash
# Set up budget alert
aws budgets create-budget \
  --account-id <your-account-id> \
  --budget file://budget-config.json
```

## Support

- See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed guide
- See [git-workflow.md](git-workflow.md) for Git workflow
- See [tech.md](.kiro/steering/tech.md) for technology stack
