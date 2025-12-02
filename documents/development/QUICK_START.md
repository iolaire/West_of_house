# Quick Start Guide - Amplify Gen 2 Deployment

## First-Time Setup (One Time Only)

### 1. Connect GitHub to Amplify Console

```bash
# Open Amplify Console
open https://console.aws.amazon.com/amplify/home?region=us-east-1
```

- Click "Create new app" → "Host web app"
- Select "GitHub" → Authorize AWS Amplify
- Select repository: `iolaire/West_of_house`
- Select branch: `main`
- Click "Save and deploy"

**This only needs to be done once!** After this, the Amplify app persists and you can deploy/cleanup as many times as needed.

## Daily Development Workflow

### Test Changes Locally (Sandbox)

```bash
# Deploy to personal cloud sandbox
./scripts/deploy-gen2.sh --type sandbox

# Test your changes with real AWS resources
# Press Ctrl+C when done
```

### Deploy to Production

```bash
# Option 1: Automatic via Git push (recommended)
git add .
git commit -m "your changes"
git push origin main
# Amplify automatically deploys!

# Option 2: Manual deployment
./scripts/deploy-gen2.sh --type pipeline
```

### Clean Up Backend Resources

```bash
# Preview what will be deleted
./scripts/cleanup-backend.sh --dry-run

# Clean up (keeps Amplify app and GitHub connection)
./scripts/cleanup-backend.sh

# Redeploy fresh backend
./scripts/deploy-gen2.sh --type sandbox
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `./scripts/deploy-gen2.sh --type sandbox` | Test deployment with real AWS resources |
| `./scripts/deploy-gen2.sh --type pipeline` | Deploy via Git push |
| `./scripts/cleanup-backend.sh` | Remove backend, keep Amplify app |
| `./scripts/cleanup-backend.sh --dry-run` | Preview cleanup |
| `git push origin main` | Automatic deployment (after GitHub setup) |

## What Gets Preserved vs Deleted

### Cleanup Preserves ✅
- Amplify app and hosting
- **Custom domain: west.zero.vedfolnir.org**
- **Route 53 DNS configuration**
- **SSL certificates**
- GitHub connection
- Amplify service roles
- Deployment configuration

### Cleanup Removes ❌
- Lambda functions (backend compute)
- DynamoDB tables (backend storage)
- API Gateway APIs (backend endpoints)
- CloudWatch log groups
- Lambda execution roles

**Your domain is 100% safe!** The cleanup script never touches Amplify hosting, domains, or DNS settings.

## Cost Optimization

- **Sandbox**: Delete when not testing (resources cost money)
- **Production**: Only runs when users play (serverless = pay per use)
- **Estimated**: <$5/month for 1000 games/month

## Troubleshooting

### "AWS credentials not configured"
```bash
aws configure --profile amplify-deploy
```

### "Node.js not installed"
```bash
# Install from https://nodejs.org/
# Or use homebrew: brew install node
```

### "Permission denied on scripts"
```bash
chmod +x scripts/*.sh
```

### Deployment fails
```bash
# Check AWS credentials
aws sts get-caller-identity --profile amplify-deploy

# Check Amplify app exists
aws amplify list-apps --region us-east-1
```

## Architecture

```
GitHub Push
    ↓
Amplify Console (detects change)
    ↓
Builds & Deploys:
    - Lambda Function (Python 3.12, ARM64)
    - DynamoDB Table (with TTL)
    - API Gateway (REST endpoints)
    ↓
Resources Tagged:
    - Project: west-of-haunted-house
    - ManagedBy: vedfolnir
    - Environment: prod
```

## Next Steps

1. ✅ Complete GitHub connection (one time)
2. ✅ Test with sandbox deployment
3. ✅ Deploy to production via Git push
4. ✅ Test API endpoints
5. ✅ Monitor in Amplify Console

## Resources

- [Full Deployment Guide](DEPLOYMENT_GEN2.md)
- [Scripts Documentation](scripts/README.md)
- [Amplify Gen 2 Docs](https://docs.amplify.aws/gen2/)
