# Deployment Scripts

This directory contains scripts for packaging and deploying the West of Haunted House backend to AWS.

## Amplify Gen 2 Scripts (Recommended)

### `deploy-gen2.sh` ⭐ NEW
Deploy using Amplify Gen 2 with TypeScript-based infrastructure.

**Usage:**
```bash
# Deploy to cloud sandbox (for testing)
./scripts/deploy-gen2.sh --type sandbox

# Deploy via pipeline (automatic from GitHub)
./scripts/deploy-gen2.sh --type pipeline

# Use specific AWS profile
./scripts/deploy-gen2.sh --profile my-profile --type sandbox
```

**Deployment Types:**
- **sandbox**: Personal cloud environment for testing (runs locally, creates real AWS resources)
- **pipeline**: Automatic deployment via Git push (requires GitHub connection)

**What it does:**
1. Verifies AWS credentials
2. Installs npm dependencies in amplify/
3. Deploys backend resources (Lambda, DynamoDB, API Gateway)
4. Displays deployment information

**Key Benefits:**
- No manual environment variable configuration
- TypeScript-based infrastructure (type-safe)
- Automatic resource tagging
- Preserves Amplify app between deployments

### `cleanup-backend.sh` ⭐ NEW
Remove backend resources while preserving the Amplify app.

**Usage:**
```bash
# Preview what would be deleted (dry run)
./scripts/cleanup-backend.sh --dry-run

# Delete backend resources (with confirmation)
./scripts/cleanup-backend.sh

# Delete without confirmation
./scripts/cleanup-backend.sh --force
```

**What it does:**
- Deletes Lambda functions
- Deletes DynamoDB tables
- Deletes API Gateway APIs
- Deletes CloudWatch log groups
- Deletes Lambda execution roles
- **PRESERVES** Amplify app and GitHub connection

**Safety Features:**
- Only deletes resources with required tags (Project, ManagedBy)
- Confirmation prompt before deletion
- Dry-run mode to preview changes
- Preserves Amplify service roles

## Amplify Gen 1 Scripts (Legacy)

These scripts are for the older Gen 1 deployment method. Use Gen 2 scripts above for new deployments.

## Scripts Overview

### 1. `bundle-game-data.sh`
Copies haunted theme JSON files from `west_of_house_json/` to the Lambda data directory.

**Usage:**
```bash
./scripts/bundle-game-data.sh
```

**What it does:**
- Creates `amplify/backend/function/gameHandler/src/data/` directory
- Copies `rooms_haunted.json`, `objects_haunted.json`, and `flags_haunted.json`
- Verifies files were copied successfully
- Displays file sizes

### 2. `package-lambda.sh`
Creates a deployment package for the Lambda function with all dependencies.

**Usage:**
```bash
./scripts/package-lambda.sh
```

**What it does:**
- Creates a `build/lambda/` directory
- Copies Python source code from Lambda function
- Installs dependencies from `requirements.txt` (if exists)
- Copies game data files (if exist)
- Creates `lambda-deployment-package.zip`
- Checks package size (warns if >50MB)

**Output:**
- `lambda-deployment-package.zip` in project root

### 3. `deploy.sh`
Complete deployment script that bundles data, packages Lambda, and deploys via Amplify CLI.

**Usage:**
```bash
# Basic deployment
./scripts/deploy.sh

# Use specific AWS profile
./scripts/deploy.sh --profile my-profile

# Skip bundling step (if already done)
./scripts/deploy.sh --skip-bundle

# Skip packaging step (if already done)
./scripts/deploy.sh --skip-package

# Show help
./scripts/deploy.sh --help
```

**What it does:**
1. Verifies AWS credentials
2. Runs `bundle-game-data.sh` (unless --skip-bundle)
3. Runs `package-lambda.sh` (unless --skip-package)
4. Deploys to AWS using `amplify push`
5. Displays deployment information (API endpoint, Lambda function, DynamoDB table)

**Options:**
- `--profile PROFILE`: AWS CLI profile to use (default: amplify-deploy)
- `--skip-bundle`: Skip game data bundling step
- `--skip-package`: Skip Lambda packaging step
- `--help`: Show help message

**Environment Variables:**
- `AWS_PROFILE`: AWS CLI profile (default: amplify-deploy)

## Deployment Workflow

### First-Time Deployment

1. **Bundle game data:**
   ```bash
   ./scripts/bundle-game-data.sh
   ```

2. **Package Lambda function:**
   ```bash
   ./scripts/package-lambda.sh
   ```

3. **Deploy to AWS:**
   ```bash
   ./scripts/deploy.sh --profile amplify-deploy
   ```

### Subsequent Deployments

For code changes only:
```bash
./scripts/deploy.sh
```

For data changes only:
```bash
./scripts/bundle-game-data.sh
./scripts/deploy.sh --skip-package
```

## Prerequisites

### Required Tools
- **AWS CLI**: Install from https://aws.amazon.com/cli/
- **Amplify CLI**: Install with `npm install -g @aws-amplify/cli`
- **Python 3.12**: For Lambda runtime
- **pip**: For installing Python dependencies

### AWS Credentials

Configure AWS credentials for deployment:
```bash
aws configure --profile amplify-deploy
```

You'll need:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)

### IAM Permissions

The deployment user needs permissions for:
- AWS Amplify (full access)
- AWS Lambda (create, update, invoke)
- Amazon DynamoDB (create, update tables)
- AWS IAM (create roles, attach policies)
- AWS CloudFormation (create, update stacks)
- Amazon S3 (create buckets, upload objects)
- Amazon API Gateway (create, update APIs)

See `iam-deployment-policy.json` for the complete policy.

## Troubleshooting

### "Amplify CLI is not installed"
Install Amplify CLI:
```bash
npm install -g @aws-amplify/cli
```

### "AWS credentials not configured"
Configure AWS credentials:
```bash
aws configure --profile amplify-deploy
```

### "Package size exceeds 50MB"
The Lambda deployment package is too large. Options:
1. Remove unnecessary dependencies
2. Use Lambda layers for large dependencies
3. Upload package to S3 and deploy from there

### "Permission denied" when running scripts
Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### Deployment fails with IAM errors
Verify your IAM user has the required permissions:
```bash
./scripts/verify-iam-config.sh
```

## Cost Optimization

The deployment is optimized for minimal costs:
- **Lambda**: ARM64 architecture (20% cost savings)
- **DynamoDB**: On-demand billing (pay per request)
- **Amplify**: Free tier covers typical usage

**Estimated cost**: <$5/month for 1000 games/month

## Monitoring

After deployment, monitor your application:

**Lambda logs:**
```bash
aws logs tail /aws/lambda/gameHandler --follow --profile amplify-deploy
```

**DynamoDB table:**
```bash
aws dynamodb describe-table --table-name GameSessions --profile amplify-deploy
```

**API Gateway:**
```bash
aws apigateway get-rest-apis --profile amplify-deploy
```

## Additional Scripts

### `setup-deployment-user.sh`
Creates the IAM deployment user with required permissions.

### `verify-iam-config.sh`
Verifies IAM configuration and permissions.

### `iam-deployment-policy.json`
IAM policy document for deployment user.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review AWS CloudFormation stack events
3. Check Lambda function logs in CloudWatch
4. Verify IAM permissions with `verify-iam-config.sh`
