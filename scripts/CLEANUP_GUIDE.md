# Amplify Gen 2 Cleanup Guide

## Overview

This guide explains how to safely remove the West of Haunted House Amplify Gen 2 deployment from AWS.

## Available Cleanup Scripts

### 1. `cleanup-amplify-gen2-complete.sh` (Complete Removal)

**Use this when:** You want to completely remove the entire project from AWS.

**What it deletes:**
- ✅ Amplify app and hosting
- ✅ Custom domain configuration
- ✅ Lambda functions
- ✅ DynamoDB tables
- ✅ API Gateway APIs
- ✅ CloudWatch log groups
- ✅ IAM roles (Lambda execution roles)
- ✅ S3 buckets (deployment artifacts)

**Safety:** Only deletes resources with these tags:
- `Project: west-of-haunted-house`
- `ManagedBy: vedfolnir`

### 2. `cleanup-backend.sh` (Backend Only)

**Use this when:** You want to remove backend resources but keep the Amplify app for future deployments.

**What it deletes:**
- ✅ Lambda functions
- ✅ DynamoDB tables
- ✅ API Gateway APIs
- ✅ CloudWatch log groups
- ✅ IAM roles (Lambda execution roles only)

**What it preserves:**
- ✅ Amplify app and hosting
- ✅ Custom domain configuration
- ✅ GitHub connection
- ✅ SSL certificates

## Usage

### Complete Removal (Recommended for End of Project)

```bash
# 1. Dry run first (see what would be deleted)
./scripts/cleanup-amplify-gen2-complete.sh --dry-run

# 2. Review the output carefully

# 3. Run the actual cleanup
./scripts/cleanup-amplify-gen2-complete.sh

# 4. Type 'DELETE' when prompted to confirm
```

### Backend Only Removal

```bash
# 1. Dry run first
./scripts/cleanup-backend.sh --dry-run

# 2. Run the actual cleanup
./scripts/cleanup-backend.sh

# 3. Type 'yes' when prompted to confirm
```

## Command Line Options

Both scripts support these options:

```bash
--profile PROFILE    # AWS CLI profile to use (default: amplify-deploy)
--region REGION      # AWS region (default: us-east-1)
--dry-run            # Show what would be deleted without deleting
--force              # Skip confirmation prompt (use with caution!)
--help               # Show help message
```

### Examples

```bash
# Dry run with custom profile
./scripts/cleanup-amplify-gen2-complete.sh --profile my-profile --dry-run

# Force cleanup without confirmation (dangerous!)
./scripts/cleanup-amplify-gen2-complete.sh --force

# Use different region
./scripts/cleanup-amplify-gen2-complete.sh --region us-west-2
```

## Safety Features

### 1. Tag-Based Filtering

The script only deletes resources with BOTH of these tags:
- `Project: west-of-haunted-house`
- `ManagedBy: vedfolnir`

This ensures resources from other projects are never touched.

### 2. Dry Run Mode

Always run with `--dry-run` first to see what will be deleted:

```bash
./scripts/cleanup-amplify-gen2-complete.sh --dry-run
```

### 3. Confirmation Prompt

The script requires you to type `DELETE` (case-sensitive) to confirm deletion.

### 4. Detailed Output

The script shows:
- What resources were found
- What will be deleted
- Progress during deletion
- Summary of what was deleted

## Pre-Cleanup Checklist

Before running the cleanup script:

- [ ] Backup any important data from DynamoDB
- [ ] Export any CloudWatch logs you want to keep
- [ ] Document any custom configurations
- [ ] Verify you're using the correct AWS profile
- [ ] Run with `--dry-run` first
- [ ] Review the list of resources to be deleted
- [ ] Confirm you want to delete everything

## What Happens During Cleanup

The script deletes resources in this order:

1. **Amplify app** (includes branches and domain associations)
2. **API Gateway APIs** (REST APIs)
3. **Lambda functions** (and their CloudWatch log groups)
4. **DynamoDB tables** (all data will be lost)
5. **S3 buckets** (emptied first, then deleted)
6. **IAM roles** (detaches policies first)
7. **CloudWatch log groups** (any remaining)

## After Cleanup

Once cleanup is complete:

- All AWS resources for the project are removed
- You will no longer be charged for these resources
- The project can be redeployed later if needed
- Local code and configuration files are NOT affected

## Troubleshooting

### "Error: AWS credentials not configured"

```bash
# Configure AWS CLI profile
aws configure --profile amplify-deploy
```

### "Error: jq is not installed"

```bash
# Install jq on macOS
brew install jq
```

### "Failed to delete" messages

Some resources may fail to delete if:
- They have dependencies that need to be deleted first
- They're in use by another service
- You don't have sufficient permissions

Run the script again to retry failed deletions.

### Resources still showing in AWS Console

- Wait a few minutes for eventual consistency
- Check CloudFormation stacks (may need manual deletion)
- Verify the resource has the correct tags

## Cost Implications

After cleanup:
- ✅ No more Lambda invocation charges
- ✅ No more DynamoDB storage/request charges
- ✅ No more Amplify hosting charges
- ✅ No more API Gateway charges
- ✅ No more CloudWatch log storage charges

You should see charges drop to $0 within 24-48 hours.

## Redeployment

If you want to redeploy later:

1. Your local code is still intact
2. Run the deployment script:
   ```bash
   git checkout production
   git merge main
   git push origin production
   ```
3. Amplify will recreate all resources

## Emergency Rollback

If you accidentally delete resources:

1. **Stop immediately** - Don't run the script again
2. Check AWS CloudTrail for deletion events
3. Redeploy from Git:
   ```bash
   git checkout production
   git push origin production --force
   ```
4. Restore DynamoDB data from backups (if available)

## Support

If you encounter issues:

1. Run with `--dry-run` to diagnose
2. Check AWS CloudTrail for error details
3. Verify IAM permissions
4. Check the script output for specific error messages

## Summary

**For complete project removal:**
```bash
./scripts/cleanup-amplify-gen2-complete.sh --dry-run  # Review first
./scripts/cleanup-amplify-gen2-complete.sh            # Then delete
```

**For backend-only removal:**
```bash
./scripts/cleanup-backend.sh --dry-run  # Review first
./scripts/cleanup-backend.sh            # Then delete
```

Always run `--dry-run` first! 🛡️
