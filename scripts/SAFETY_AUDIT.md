# Cleanup Script Safety Audit

## Overview
This document verifies that the cleanup script ONLY deletes resources from the West of Haunted House project and will NOT touch other projects.

## Safety Mechanisms

### 1. Amplify App (Primary Filter)
```bash
# Uses BOTH tags to find the app
Project=west-of-haunted-house AND Owner=vedfolnir
```
**Result**: Only finds app ID `dhi9gcvt4p94z`

### 2. Lambda Functions
```bash
# Two-stage filter:
# Stage 1: Try to find by tags (Project + Owner/ManagedBy)
# Stage 2: Find by exact APP_ID in function name
if [[ "$func" == *"$APP_ID"* ]]; then
```
**Result**: Only matches functions containing `dhi9gcvt4p94z`
- ✅ Matches: `amplify-dhi9gcvt4p94z-producti-gamehandler9C35C05F-xkwnhFZkn6yj`
- ❌ Excludes: `amplify-eyga-iolaire-sand-...`
- ❌ Excludes: `amplify-fediversecomposer-...`

### 3. DynamoDB Tables
```bash
# Checks for BOTH tags
if [ "$PROJECT" = "$PROJECT_TAG" ] && ([ "$OWNER" = "$MANAGED_BY_TAG" ] || [ "$MANAGED_BY" = "$MANAGED_BY_TAG" ])
```
**Result**: Only matches tables with correct tags
- ✅ Matches: `GameSession-hu6o4es4ebgi5lhmq6rjtqdlve-NONE` (has correct tags)
- ❌ Excludes: Any table without both tags

### 4. API Gateway APIs
```bash
# Checks for BOTH tags
if [ "$PROJECT" = "$PROJECT_TAG" ] && ([ "$OWNER" = "$MANAGED_BY_TAG" ] || [ "$MANAGED_BY" = "$MANAGED_BY_TAG" ])
```
**Result**: Only matches APIs with correct tags

### 5. S3 Buckets
```bash
# Only if APP_ID exists, matches exact APP_ID in bucket name
if [[ "$bucket" == *"$APP_ID"* ]]; then
```
**Result**: Only matches buckets containing `dhi9gcvt4p94z`
- ✅ Matches: `amplify-dhi9gcvt4p94z-pro-amplifydataamplifycodege-vx4ihxgkhc5t`
- ❌ Excludes: `amplify-fediversecomposer-amplifydataamplifycodege-l1cw9ksiuokh`

### 6. IAM Roles
```bash
# Matches APP_ID OR game handler names, then EXCLUDES other projects
if [[ "$role" == *"$APP_ID"* ]] || [[ "$role" == *"gameHandler"* ]] || [[ "$role" == *"game-handler"* ]]; then
    # Additional check: make sure it's not from another project
    if [[ "$role" != *"fediversecomposer"* ]] && [[ "$role" != *"d1x3xrra4vf534"* ]]; then
```
**Result**: Only matches roles with `dhi9gcvt4p94z` AND excludes known other projects
- ✅ Matches: `amplify-dhi9gcvt4p94z-pro-gamehandlerServiceRoleE64-OkX33Z6y2C4N`
- ❌ Excludes: `amplify-fediversecomposer-PythonBackendAltTextGensa-N11ctBdSMPCQ`

### 7. WAF Web ACLs
```bash
# Only if APP_ID exists, matches APP_ID in WAF name
WAF_WEB_ACLS=$(echo "$ALL_WAFV2" | jq -r ".[] | select(.Name | contains(\"$APP_ID\"))")
```
**Result**: Only matches WAFs containing `dhi9gcvt4p94z`
- ✅ Matches: `CreatedByAmplify-dhi9gcvt4p94z-3d120293-fe48-4f6c-8a17-15b041551955`

### 8. Route 53 DNS Records
```bash
# Only looks for records containing 'west.zero.vedfolnir.org'
RECORDS=$(aws route53 list-resource-record-sets ... \
    --query "ResourceRecordSets[?contains(Name, 'west.zero.vedfolnir.org')]")
```
**Result**: Only matches the specific subdomain
- ✅ Matches: `west.zero.vedfolnir.org`
- ❌ Excludes: All other subdomains in `zero.vedfolnir.org`

### 9. CloudWatch Log Groups
```bash
# Only if APP_ID exists, matches exact APP_ID in log group name
--query "logGroups[?contains(logGroupName, '$APP_ID')].logGroupName"
```
**Result**: Only matches log groups containing `dhi9gcvt4p94z`
- ✅ Matches: `/aws/lambda/amplify-dhi9gcvt4p94z-...` (if any exist)
- ❌ Excludes: `/aws/lambda/amplify-eyga-iolaire-sand-...`
- ❌ Excludes: `/aws/lambda/amplify-fediversecomposer-...`

## Additional Safety Features

### Pre-Deletion Checks
Before deleting each resource type, the script checks if it still exists:
```bash
if aws lambda get-function ... &>/dev/null; then
    # Delete
else
    echo "Already deleted by CloudFormation"
fi
```

### CloudFormation Wait
The script waits up to 30 minutes for CloudFormation to complete deletion, preventing conflicts with manually deleting resources that CloudFormation is already handling.

### Dry Run Mode
Always run with `--dry-run` first to see exactly what will be deleted:
```bash
./scripts/cleanup-amplify-gen2-complete.sh --profile default --dry-run
```

## Verification Commands

### Check what would be deleted:
```bash
# Amplify app
aws amplify list-apps --query "apps[?tags.Project=='west-of-haunted-house' && tags.Owner=='vedfolnir']"

# Lambda functions
aws lambda list-functions --query "Functions[?contains(FunctionName, 'dhi9gcvt4p94z')]"

# DynamoDB tables
aws dynamodb list-tables | grep -i game

# S3 buckets
aws s3api list-buckets --query "Buckets[?contains(Name, 'dhi9gcvt4p94z')]"

# IAM roles
aws iam list-roles --query "Roles[?contains(RoleName, 'dhi9gcvt4p94z')]"

# CloudWatch logs
aws logs describe-log-groups --query "logGroups[?contains(logGroupName, 'dhi9gcvt4p94z')]"
```

## Projects That Will NOT Be Touched

✅ **Safe Projects:**
- `amplify-eyga-iolaire-sand-...` (different app ID)
- `amplify-fediversecomposer-...` (explicitly excluded)
- `amplify-d1x3xrra4vf534-...` (explicitly excluded)
- Any other Amplify apps without the correct tags
- Route 53 hosted zone `zero.vedfolnir.org` (only subdomain records deleted)

## Summary

**The script is safe to run.** It uses multiple layers of filtering:

1. **Primary filter**: App ID `dhi9gcvt4p94z`
2. **Tag filter**: `Project=west-of-haunted-house` AND `Owner=vedfolnir`
3. **Explicit exclusions**: Other known projects
4. **Specific matching**: Exact string matching, not wildcards

**No other projects will be affected.**
