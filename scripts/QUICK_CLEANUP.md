# Quick Cleanup Instructions

## Your AWS Setup

- **AWS Account**: 415101847494
- **Default Profile**: `default` (already configured)
- **Amplify App Found**: West_of_house (dhi9gcvt4p94z)
- **Region**: us-east-1

## How the Cleanup Works

The script uses a smart two-phase approach:

### Phase 1: Amplify App Deletion (10-30 minutes)
1. Deletes the Amplify app
2. This triggers CloudFormation to automatically delete:
   - Lambda functions
   - DynamoDB tables
   - AppSync GraphQL API
   - Cognito User Pool and Identity Pool
   - Step Functions state machines
   - Most IAM roles
   - SSM parameters
3. **Script waits** for CloudFormation to complete (up to 30 minutes)

### Phase 2: Cleanup Remaining Resources (2-5 minutes)
After CloudFormation finishes, the script cleans up:
- Any orphaned Lambda functions
- S3 buckets (emptied first)
- Remaining IAM roles
- WAF Web ACLs
- Route 53 DNS records
- CloudWatch log groups

**Total time**: 15-35 minutes

## Run Cleanup with Your Profile

### Step 1: Dry Run (See What Will Be Deleted)

```bash
./scripts/cleanup-amplify-gen2-complete.sh --profile default --dry-run
```

This shows all resources WITHOUT deleting them.

### Step 2: Review the Output

Check the list carefully. You should see:
- Amplify app: West_of_house
- 7 Lambda functions
- 1 DynamoDB table
- 2 S3 buckets
- 14 IAM roles
- 1 WAF Web ACL
- 2 Route 53 DNS records

### Step 3: Run the Actual Cleanup

```bash
./scripts/cleanup-amplify-gen2-complete.sh --profile default
```

When prompted, type `DELETE` (case-sensitive) to confirm.

**What to expect:**
```
Deleting Amplify app...
✓ Amplify app deletion initiated

Waiting for CloudFormation stacks to be deleted...
This may take 10-30 minutes depending on resources...
  Stack status: DELETE_IN_PROGRESS (0m/30m elapsed)
  Stack status: DELETE_IN_PROGRESS (1m/30m elapsed)
  Stack status: DELETE_IN_PROGRESS (2m/30m elapsed)
  ...
✓ CloudFormation stacks deleted

Deleting Lambda functions...
  Checking amplify-dhi9gcvt4p94z-producti-gamehandler9C35C05F-xkwnhFZkn6yj...
  Already deleted by CloudFormation
...
```

The script will wait up to 30 minutes for CloudFormation to finish before cleaning up remaining resources.

**Note**: You can safely let this run in the background. The script will handle everything automatically.

## Alternative: Use Environment Variable

You can also set the AWS_PROFILE environment variable:

```bash
export AWS_PROFILE=default
./scripts/cleanup-amplify-gen2-complete.sh --dry-run
./scripts/cleanup-amplify-gen2-complete.sh
```

## Quick One-Liner

If you're confident and want to skip the dry run (not recommended):

```bash
./scripts/cleanup-amplify-gen2-complete.sh --profile default --force
```

⚠️ **Warning**: This skips the confirmation prompt!

## What Will Be Deleted

Based on your current deployment:
- ✅ Amplify app: West_of_house (dhi9gcvt4p94z)
- ✅ All Lambda functions with Project=west-of-haunted-house tag
- ✅ All DynamoDB tables with Project=west-of-haunted-house tag
- ✅ All API Gateway APIs with Project=west-of-haunted-house tag
- ✅ Associated S3 buckets
- ✅ IAM roles for Lambda functions
- ✅ CloudWatch log groups

## Safety Guarantees

The script will ONLY delete resources with BOTH tags:
- `Project: west-of-haunted-house`
- `Owner: vedfolnir` (or `ManagedBy: vedfolnir`)

Your other AWS resources (alt-text projects, etc.) will NOT be touched.

## Troubleshooting

If you get permission errors, make sure your default profile has these permissions:
- amplify:*
- lambda:*
- dynamodb:*
- apigateway:*
- s3:*
- iam:*
- logs:*

## After Cleanup

Once complete, you'll see:
```
✓ All project resources removed
```

And your AWS bill will drop to $0 for this project within 24-48 hours.
