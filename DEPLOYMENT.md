# Deployment Guide

This guide explains how to deploy the West of Haunted House backend to AWS using the provided deployment scripts.

## Quick Start

```bash
# 1. Bundle game data
./scripts/bundle-game-data.sh

# 2. Package Lambda function
./scripts/package-lambda.sh

# 3. Deploy to AWS
./scripts/deploy.sh --profile amplify-deploy
```

## Prerequisites

Before deploying, ensure you have:

1. **AWS CLI** installed and configured
2. **Amplify CLI** installed (`npm install -g @aws-amplify/cli`)
3. **Python 3.12** installed
4. **AWS credentials** configured for deployment

### Setting Up AWS Credentials

```bash
# Configure AWS credentials
aws configure --profile amplify-deploy

# You'll need:
# - AWS Access Key ID
# - AWS Secret Access Key
# - Default region (e.g., us-east-1)
```

## Deployment Scripts

### 1. Bundle Game Data (`bundle-game-data.sh`)

Copies haunted theme JSON files to the Lambda data directory.

```bash
./scripts/bundle-game-data.sh
```

**What it does:**
- Creates `amplify/backend/function/gameHandler/src/data/` directory
- Copies `rooms_haunted.json`, `objects_haunted.json`, `flags_haunted.json`
- Verifies files and displays sizes

**When to run:**
- Before first deployment
- After updating game data JSON files

### 2. Package Lambda Function (`package-lambda.sh`)

Creates a deployment package with all dependencies.

```bash
./scripts/package-lambda.sh
```

**What it does:**
- Creates `build/lambda/` directory
- Copies Python source code
- Installs dependencies from `requirements.txt`
- Bundles game data files
- Creates `lambda-deployment-package.zip`

**Output:**
- `lambda-deployment-package.zip` (typically ~16MB)

**When to run:**
- Before first deployment
- After updating Lambda code
- After updating dependencies

### 3. Deploy to AWS (`deploy.sh`)

Complete deployment script that orchestrates the entire process.

```bash
# Basic deployment
./scripts/deploy.sh

# With specific AWS profile
./scripts/deploy.sh --profile my-profile

# Skip bundling (if already done)
./scripts/deploy.sh --skip-bundle

# Skip packaging (if already done)
./scripts/deploy.sh --skip-package
```

**What it does:**
1. Verifies AWS credentials
2. Bundles game data (unless `--skip-bundle`)
3. Packages Lambda function (unless `--skip-package`)
4. Deploys via `amplify push`
5. Displays deployment information

**Options:**
- `--profile PROFILE`: AWS CLI profile (default: amplify-deploy)
- `--skip-bundle`: Skip game data bundling
- `--skip-package`: Skip Lambda packaging
- `--help`: Show help message

## Deployment Workflows

### First-Time Deployment

```bash
# Step 1: Bundle game data
./scripts/bundle-game-data.sh

# Step 2: Package Lambda
./scripts/package-lambda.sh

# Step 3: Deploy
./scripts/deploy.sh --profile amplify-deploy
```

### Update Code Only

```bash
./scripts/deploy.sh
```

### Update Game Data Only

```bash
./scripts/bundle-game-data.sh
./scripts/deploy.sh --skip-package
```

### Update Dependencies

```bash
# Edit requirements.txt, then:
./scripts/package-lambda.sh
./scripts/deploy.sh --skip-bundle
```

## Verifying Resource Tags

After deployment, verify that all AWS resources have the required tags:

```bash
./scripts/verify-resource-tags.sh
```

**Required Tags:**
- **Project**: `west-of-haunted-house`
- **ManagedBy**: `vedfolnir`
- **Environment**: `dev` (or your environment name)

These tags enable:
- Cost tracking and allocation
- Resource discovery and management
- Automated cleanup scripts

See [AWS_RESOURCE_TAGGING.md](documents/AWS_RESOURCE_TAGGING.md) for details.

## Monitoring After Deployment

### View Lambda Logs

```bash
# Get function name from deployment output, then:
aws logs tail /aws/lambda/gameHandler --follow --profile amplify-deploy
```

### Check DynamoDB Table

```bash
aws dynamodb describe-table --table-name GameSessions --profile amplify-deploy
```

### Test API Endpoint

```bash
# Get API endpoint from deployment output, then:
curl https://your-api-endpoint.amazonaws.com/api/game/new
```

## Troubleshooting

### "Amplify CLI is not installed"

```bash
npm install -g @aws-amplify/cli
```

### "AWS credentials not configured"

```bash
aws configure --profile amplify-deploy
```

### "Package size exceeds 50MB"

The Lambda package is too large. Options:
1. Remove unnecessary dependencies
2. Use Lambda layers
3. Upload to S3 and deploy from there

### "Permission denied" on scripts

```bash
chmod +x scripts/*.sh
```

### Deployment fails with IAM errors

Verify IAM permissions:
```bash
./scripts/verify-iam-config.sh
```

## Cost Optimization

The deployment uses:
- **Lambda ARM64**: 20% cost savings vs x86_64
- **DynamoDB On-Demand**: Pay per request
- **Amplify Free Tier**: Covers typical usage

**Estimated cost**: <$5/month for 1000 games/month

## Architecture

```
┌─────────────────────────────────────┐
│   React Frontend (Amplify Hosting) │
└─────────────┬───────────────────────┘
              │ HTTPS/JSON
┌─────────────▼───────────────────────┐
│   AWS Amplify API Gateway (REST)   │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│   Lambda Function (Python 3.12)    │
│   - Game Engine                     │
│   - Command Parser                  │
│   - State Manager                   │
│   - Bundled Game Data               │
└─────────────┬───────────────────────┘
              │
┌─────────────▼───────────────────────┐
│   DynamoDB (Session Storage)        │
│   - TTL-based cleanup               │
│   - On-demand billing               │
└─────────────────────────────────────┘
```

## Next Steps

After successful deployment:

1. **Test the API** using the endpoint from deployment output
2. **Monitor logs** to ensure everything works correctly
3. **Update frontend** with the API endpoint
4. **Test game functionality** end-to-end

## Additional Resources

- [AWS Amplify Documentation](https://docs.amplify.aws/)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Project README](README.md)
- [Scripts README](scripts/README.md)
