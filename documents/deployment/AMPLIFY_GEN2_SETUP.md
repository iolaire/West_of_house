# Amplify Gen 2 Setup Guide

## Task 17.3.2 Complete ✅

This document explains the DynamoDB table configuration for the West of Haunted House backend using AWS Amplify Gen 2.

## What Was Implemented

### 1. DynamoDB Table Schema (`amplify/data/resource.ts`)

Created a comprehensive GameSession model with all required fields:

**Session Management:**
- `sessionId` - Primary key (unique identifier)
- `lastAccessed` - Timestamp for activity tracking
- `expires` - Unix timestamp for TTL-based cleanup

**Game State:**
- `currentRoom` - Current player location
- `inventory` - Array of object IDs
- `flags` - JSON object for game flags
- `roomsVisited` - Array of visited room IDs

**Player Statistics:**
- `sanity` - Mental health meter (0-100)
- `score` - Player score
- `moves` - Turn counter
- `lampBattery` - Lamp fuel remaining

**Halloween Mechanics:**
- `cursed` - Curse status
- `bloodMoonActive` - Blood moon phase
- `soulsCollected` - Soul count
- `curseDuration` - Curse timer

**Original Zork State:**
- `lucky` - Lucky flag
- `thiefHere` - Thief presence
- `wonFlag` - Victory condition

### 2. Table Configuration

✅ **TTL Enabled**: Automatic cleanup using `expires` field (1 hour default)
✅ **On-Demand Billing**: Pay-per-request pricing for cost optimization
✅ **Guest Authorization**: No authentication required for MVP

### 3. Resource Tagging (`amplify/backend.ts`)

Applied required tags to all resources:
- **Project**: `west-of-haunted-house`
- **ManagedBy**: `vedfolnir`
- **Environment**: Dynamically set from `AMPLIFY_ENV` (defaults to `dev`)

## Requirements Validated

- ✅ **Requirement 22.3**: DynamoDB with on-demand billing and session storage
- ✅ **Requirement 24.1**: Project tag applied
- ✅ **Requirement 24.2**: ManagedBy tag applied
- ✅ **Requirement 24.3**: Environment tag applied

## Deployment Instructions

### Option 1: Local Sandbox (Recommended for Testing)

Start a local development environment with cloud resources:

```bash
npx ampx sandbox
```

This will:
- Deploy resources to your AWS account
- Create a per-developer sandbox environment
- Watch for file changes and auto-deploy
- Provide a local endpoint for testing

**Note**: Sandbox creates real AWS resources in your account. You'll be charged for usage.

### Option 2: Production Deployment via Git

For production deployment:

```bash
# Commit your changes
git add amplify/
git commit -m "Add DynamoDB table configuration"

# Push to trigger Amplify deployment
git push origin main
```

Amplify will automatically:
- Detect the backend changes
- Build and deploy the infrastructure
- Apply resource tags
- Create the DynamoDB table

### Option 3: Manual Pipeline Deploy

For CI/CD pipelines:

```bash
npx ampx pipeline-deploy --branch main --app-id <your-app-id>
```

## Verification Steps

After deployment, verify the table was created correctly:

```bash
# List DynamoDB tables with project tags
aws dynamodb list-tables

# Describe the GameSessions table
aws dynamodb describe-table --table-name <table-name>

# Verify TTL is enabled
aws dynamodb describe-time-to-live --table-name <table-name>

# Check resource tags
aws dynamodb list-tags-of-resource --resource-arn <table-arn>
```

Expected tags:
- `Project=west-of-haunted-house`
- `ManagedBy=vedfolnir`
- `Environment=dev` (or your environment)

## Troubleshooting

### Issue: "Cannot find module '@aws-amplify/backend'"

**Solution**: Install dependencies
```bash
npm install
```

### Issue: TypeScript compilation errors

**Solution**: Verify TypeScript configuration
```bash
npx tsc --noEmit --project amplify/tsconfig.json
```

### Issue: Sandbox fails to start

**Solution**: Check AWS credentials
```bash
aws sts get-caller-identity
```

Ensure you have:
- Valid AWS credentials configured
- Sufficient IAM permissions for Amplify, DynamoDB, CloudFormation
- Node.js >= 20.0.0

### Issue: Table already exists

**Solution**: Delete existing table or use a different environment
```bash
# Delete table (caution: destroys data)
aws dynamodb delete-table --table-name <table-name>

# Or use a different environment
export AMPLIFY_ENV=dev2
npx ampx sandbox
```

## Cost Estimation

**DynamoDB Costs (On-Demand):**
- Free tier: 25 GB storage, 25 WCU, 25 RCU
- Beyond free tier: $1.25 per million writes, $0.25 per million reads
- Estimated: ~$0.02/month for 1000 games

**Total Estimated Cost**: < $0.10/month (well under $5 target)

## Next Steps

After successful deployment:

1. ✅ Task 17.3.2 Complete - DynamoDB table defined
2. ⏭️ Task 17.3.3 - Define Lambda function with Gen 2
3. ⏭️ Task 17.3.4 - Migrate Python Lambda code
4. ⏭️ Task 17.3.5 - Define API Gateway with Gen 2

## Architecture Notes

### Why Amplify Data Instead of Raw CDK?

We're using Amplify's `defineData` with the schema builder because:
- Automatic IAM permissions management
- Built-in authorization rules
- Type-safe client generation for frontend
- Simplified DynamoDB configuration
- Automatic environment variable resolution

### Why Guest Authorization?

For MVP, we're allowing guest access (no authentication) to:
- Simplify initial development
- Reduce deployment complexity
- Focus on core game mechanics

Authentication will be added in a future phase.

## File Structure

```
amplify/
├── backend.ts              # Backend definition with tags
├── data/
│   └── resource.ts         # DynamoDB table schema
├── auth/
│   └── resource.ts         # Cognito configuration
├── package.json
└── tsconfig.json
```

## References

- [Amplify Gen 2 Documentation](https://docs.amplify.aws/react/build-a-backend/)
- [Amplify Data Documentation](https://docs.amplify.aws/react/build-a-backend/data/)
- [DynamoDB TTL Documentation](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/TTL.html)
- [AWS Resource Tagging Best Practices](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html)
