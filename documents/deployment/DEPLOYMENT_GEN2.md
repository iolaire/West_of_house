# Amplify Gen 2 Deployment Guide

## Overview

This guide explains how to deploy the West of Haunted House backend using AWS Amplify Gen 2 with GitHub integration for automatic deployments.

## Deployment Status

✅ **Code Committed**: Gen 2 infrastructure code has been committed to the main branch
✅ **Code Pushed**: Changes have been pushed to GitHub (commit c822301)

## Deployment Options

### Option 1: Deploy via Scripts (Recommended) ⭐

Use the provided deployment scripts for easy deployment:

```bash
# Deploy to cloud sandbox (for testing)
./scripts/deploy-gen2.sh --type sandbox

# Deploy via pipeline (automatic from GitHub)
./scripts/deploy-gen2.sh --type pipeline
```

**Sandbox Deployment:**
- Creates a personal cloud environment
- Uses real AWS resources
- Perfect for testing before production
- Press Ctrl+C to stop when done

**Pipeline Deployment:**
- Requires one-time GitHub connection setup (see Option 2)
- Automatic deployment on every push to main
- Production-ready

### Option 2: One-Time GitHub Connection Setup

If you haven't connected GitHub yet, do this once:

1. **Open AWS Amplify Console**
   ```bash
   # Open in browser
   open https://console.aws.amazon.com/amplify/home?region=us-east-1
   ```

2. **Create New App**
   - Click "Create new app"
   - Choose "Host web app"
   - Select "GitHub" as the repository service
   - Authorize AWS Amplify to access your GitHub account
   - Select repository: `iolaire/West_of_house`
   - Select branch: `main`

3. **Configure Build Settings**
   - Amplify will auto-detect the Gen 2 configuration
   - Build settings should be automatically configured
   - Review and confirm

4. **Deploy**
   - Click "Save and deploy"
   - Monitor deployment progress in the Amplify Console
   - Deployment typically takes 5-10 minutes

After this setup, all future deployments happen automatically on git push!

### Option 3: Manual CLI Deployment

```bash
# Navigate to project root
cd /path/to/West_of_house

# Deploy to cloud sandbox (for testing)
cd amplify
npx ampx sandbox --profile amplify-deploy

# Or deploy to production branch (requires app-id from console)
npx ampx pipeline-deploy --branch main --app-id <app-id>
```

## Monitoring Deployment

### Via Amplify Console

1. Go to AWS Amplify Console
2. Select your app
3. View the "Deployments" tab
4. Monitor build logs in real-time

### Via AWS CLI

```bash
# List Amplify apps
aws amplify list-apps --region us-east-1

# Get app details
aws amplify get-app --app-id <app-id> --region us-east-1

# List branches
aws amplify list-branches --app-id <app-id> --region us-east-1

# Get branch details
aws amplify get-branch --app-id <app-id> --branch-name main --region us-east-1
```

## Verifying Deployment

After deployment completes, verify all resources:

### 1. Lambda Function

```bash
# List Lambda functions with project tag
aws lambda list-functions --region us-east-1 \
  --query "Functions[?Tags.Project=='west-of-haunted-house']"

# Get function details
aws lambda get-function --function-name <function-name> --region us-east-1
```

### 2. DynamoDB Table

```bash
# List tables
aws dynamodb list-tables --region us-east-1

# Describe GameSessions table
aws dynamodb describe-table --table-name GameSessions --region us-east-1
```

### 3. API Gateway

```bash
# List REST APIs
aws apigateway get-rest-apis --region us-east-1

# Get API details
aws apigateway get-rest-api --rest-api-id <api-id> --region us-east-1
```

### 4. Resource Tags

```bash
# Verify all resources have required tags
./scripts/verify-resource-tags.sh
```

## Testing the Deployed API

### Get API Endpoint

The API endpoint will be available in:
- Amplify Console → Backend → API
- Or in `amplify_outputs.json` after deployment

### Test New Game Endpoint

```bash
# Replace with your actual API endpoint
API_ENDPOINT="https://your-api-id.execute-api.us-east-1.amazonaws.com"

# Test new game creation
curl -X POST "${API_ENDPOINT}/game/new" \
  -H "Content-Type: application/json"
```

### Test Command Endpoint

```bash
# Test with a session ID from the new game response
curl -X POST "${API_ENDPOINT}/game/command" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your-session-id",
    "command": "look"
  }'
```

## Cleaning Up Backend Resources

To remove backend resources while preserving the Amplify app and domain:

```bash
# Preview what would be deleted (dry run)
./scripts/cleanup-backend.sh --dry-run

# Delete backend resources (with confirmation)
./scripts/cleanup-backend.sh

# Delete without confirmation
./scripts/cleanup-backend.sh --force
```

**What gets deleted:**
- Lambda functions
- DynamoDB tables
- API Gateway APIs
- CloudWatch log groups
- Lambda execution roles

**What gets preserved:**
- ✅ Amplify app and hosting
- ✅ Custom domain: **west.zero.vedfolnir.org**
- ✅ Route 53 DNS configuration
- ✅ SSL certificates
- ✅ GitHub connection
- ✅ Amplify service roles

**Important:** Your custom domain configuration (west.zero.vedfolnir.org) is completely safe! The cleanup script only removes backend compute and storage resources. All Amplify hosting, domain, and DNS settings remain intact. You can clean up and redeploy as many times as needed without touching the domain setup.

## Automatic Deployments

Once connected to GitHub, Amplify will automatically deploy on every push to main:

1. Push code to GitHub
2. Amplify detects the change
3. Builds and deploys automatically
4. Notifies via email (if configured)

Or use the deployment script:
```bash
./scripts/deploy-gen2.sh --type pipeline
```

## Rollback

If deployment fails or has issues:

```bash
# Via Amplify Console
# 1. Go to Deployments tab
# 2. Find previous successful deployment
# 3. Click "Redeploy this version"

# Via CLI
aws amplify start-deployment \
  --app-id <app-id> \
  --branch-name main \
  --job-id <previous-job-id> \
  --region us-east-1
```

## Cost Monitoring

After deployment, monitor costs:

```bash
# Get cost estimate
aws ce get-cost-and-usage \
  --time-period Start=2024-12-01,End=2024-12-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --filter file://cost-filter.json
```

## Troubleshooting

### Build Fails

Check build logs in Amplify Console:
- Look for TypeScript compilation errors
- Verify all dependencies are installed
- Check Python requirements.txt

### Lambda Function Not Created

- Verify `amplify/functions/game-handler/resource.ts` is correct
- Check IAM permissions for Amplify service role
- Review CloudFormation stack events

### DynamoDB Table Not Created

- Verify `amplify/data/resource.ts` is correct
- Check for naming conflicts
- Review CloudFormation stack events

### API Gateway Not Accessible

- Verify CORS configuration in `backend.ts`
- Check API Gateway deployment stage
- Verify Lambda integration

## Gen 2 vs Gen 1 Differences

| Aspect | Gen 1 | Gen 2 |
|--------|-------|-------|
| Configuration | CLI commands | TypeScript code |
| Environment Variables | Manual setup | Auto-resolved |
| Deployment | `amplify push` | Git push or `npx ampx` |
| Infrastructure | JSON/YAML | TypeScript (CDK) |
| Local Testing | Mock API | Cloud sandbox |

## Resources Created

After successful deployment, these resources will exist:

- **Lambda Function**: `game-handler` (Python 3.12, ARM64)
- **DynamoDB Table**: `GameSessions` (with TTL)
- **API Gateway**: REST API with 3 endpoints
- **IAM Roles**: Lambda execution role, API Gateway role
- **CloudWatch Logs**: Log groups for Lambda and API Gateway

All resources will have the required tags:
- Project: `west-of-haunted-house`
- ManagedBy: `vedfolnir`
- Environment: `prod` (or as configured)

## Next Steps

1. ✅ Complete Amplify Console setup (if not done)
2. ✅ Monitor first deployment
3. ✅ Verify all resources created
4. ✅ Test API endpoints
5. ✅ Update frontend with API endpoint
6. ✅ Test end-to-end game functionality

## Additional Resources

- [Amplify Gen 2 Documentation](https://docs.amplify.aws/gen2/)
- [Amplify Hosting Guide](https://docs.amplify.aws/guides/hosting/)
- [GitHub Integration](https://docs.amplify.aws/guides/hosting/git-based-deployments/)
