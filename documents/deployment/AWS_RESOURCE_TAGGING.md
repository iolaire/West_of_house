# AWS Resource Tagging Configuration

## Overview

All AWS resources created for the West of Haunted House project are tagged with three required tags to enable cost tracking, resource management, and automated cleanup.

## Required Tags

All resources MUST have these three tags:

1. **Project**: `west-of-haunted-house`
   - Identifies all resources belonging to this project
   - Used for cost allocation and resource filtering

2. **ManagedBy**: `vedfolnir`
   - Identifies the managing entity
   - Used for ownership tracking

3. **Environment**: `<env>` (e.g., `dev`, `staging`, `prod`)
   - Identifies the deployment environment
   - Dynamically set based on Amplify environment parameter

## Tagged Resources

The following AWS resources are automatically tagged via CloudFormation templates:

### Lambda Function (`gameHandler`)
- **Resource**: `AWS::Lambda::Function`
- **Template**: `amplify/backend/function/gameHandler/gameHandler-cloudformation-template.json`
- **Tags Applied**: Project, ManagedBy, Environment

### Lambda Execution Role
- **Resource**: `AWS::IAM::Role` (westofhauntedLambdaRole)
- **Template**: `amplify/backend/function/gameHandler/gameHandler-cloudformation-template.json`
- **Tags Applied**: Project, ManagedBy, Environment

### DynamoDB Table (`GameSessions`)
- **Resource**: `AWS::DynamoDB::Table`
- **Template**: `amplify/backend/storage/GameSessions/GameSessions-cloudformation-template.json`
- **Tags Applied**: Name, Project, ManagedBy, Environment

### API Gateway REST API
- **Resource**: `AWS::ApiGateway::RestApi` (westofhouseapi)
- **Template**: `amplify/backend/api/westofhouseapi/westofhouseapi-cloudformation-template.json`
- **Tags Applied**: Project, ManagedBy, Environment

### API Gateway Stage
- **Resource**: `AWS::ApiGateway::Stage`
- **Template**: `amplify/backend/api/westofhouseapi/westofhouseapi-cloudformation-template.json`
- **Tags Applied**: Project, ManagedBy, Environment

### API Gateway IAM Role
- **Resource**: `AWS::IAM::Role` (westofhouseapiLambdaRole)
- **Template**: `amplify/backend/api/westofhouseapi/westofhouseapi-cloudformation-template.json`
- **Tags Applied**: Project, ManagedBy, Environment

## Verification

After deployment, verify tags are applied correctly:

```bash
# List all project resources by tags
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=west-of-haunted-house \
                Key=ManagedBy,Values=vedfolnir

# Check Lambda function tags
aws lambda list-tags --resource <function-arn>

# Check DynamoDB table tags
aws dynamodb list-tags-of-resource --resource-arn <table-arn>

# Check API Gateway tags
aws apigateway get-rest-api --rest-api-id <api-id>
```

## Cost Tracking

Use AWS Cost Explorer with tag filters to track project costs:

```bash
# Get cost breakdown by environment
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=Environment \
  --filter file://cost-filter.json
```

Example `cost-filter.json`:
```json
{
  "Tags": {
    "Key": "Project",
    "Values": ["west-of-haunted-house"]
  }
}
```

## Resource Cleanup

The cleanup script uses these tags to identify and delete all project resources:

```bash
./scripts/cleanup-aws-resources.sh
```

The script will:
1. Query all resources with all three required tags
2. Delete resources in correct dependency order
3. Verify only tagged resources are affected
4. Provide confirmation before deletion

## Tag Consistency

**Important**: All three tags must be present on every resource for proper:
- Cost allocation
- Resource discovery
- Automated cleanup
- Access control policies

Missing tags will prevent resources from being properly tracked or cleaned up.

## Deployment Notes

- Tags are automatically applied during `amplify push`
- Environment tag is dynamically set based on Amplify environment
- No manual tagging required after initial configuration
- Tags persist across updates and redeployments
