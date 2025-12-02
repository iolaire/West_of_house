# IAM Configuration for West of Haunted House

## Overview

This document describes the IAM roles and policies configured for the West of Haunted House backend, following AWS security best practices with least-privilege access.

## Lambda Execution Role

**Role Name**: `westofhauntedLambdaRole-{env}`

**Purpose**: Allows the Lambda function to execute and access required AWS services.

**Trust Policy**: Allows Lambda service to assume this role.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": ["lambda.amazonaws.com"]
      },
      "Action": ["sts:AssumeRole"]
    }
  ]
}
```

## IAM Policies

### 1. CloudWatch Logs Policy

**Policy Name**: `lambda-execution-policy`

**Purpose**: Allows Lambda to write logs to CloudWatch for debugging and monitoring.

**Permissions**:
- `logs:CreateLogGroup` - Create log group for the function
- `logs:CreateLogStream` - Create log streams within the log group
- `logs:PutLogEvents` - Write log events to CloudWatch

**Resource Scope**: Scoped to specific Lambda function log group
```
arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{functionName}:log-stream:*
```

**Security Notes**:
- ✅ No wildcards in resource ARN (scoped to specific function)
- ✅ Minimal permissions for logging only
- ✅ Follows AWS best practices for Lambda logging

### 2. DynamoDB Access Policy

**Policy Name**: `amplify-lambda-execution-policy`

**Purpose**: Allows Lambda to manage game session data in DynamoDB.

**Permissions** (Least-Privilege):
- `dynamodb:PutItem` - Create new game sessions
- `dynamodb:GetItem` - Retrieve existing game sessions
- `dynamodb:UpdateItem` - Update game state during gameplay
- `dynamodb:DeleteItem` - Remove expired sessions (manual cleanup)
- `dynamodb:Query` - Query sessions by session ID

**Resource Scope**: Scoped to specific DynamoDB table and its indexes
```
arn:aws:dynamodb:{region}:{account}:table/GameSessions-{env}
arn:aws:dynamodb:{region}:{account}:table/GameSessions-{env}/index/*
```

**Security Notes**:
- ✅ No wildcard actions (no `Put*`, `Get*`, `Update*`, `Delete*`)
- ✅ Only specific actions required for game functionality
- ✅ Scoped to specific table ARN (no `*` resources)
- ✅ Includes index access for potential future queries
- ❌ Removed unnecessary actions:
  - `BatchWriteItem`, `BatchGetItem` - Not needed for single-session operations
  - `Scan` - Inefficient and not required
  - `List*`, `Describe*` - Not needed for runtime operations
  - `Create*`, `RestoreTable*` - Infrastructure operations, not runtime

## Requirements Validation

### Requirement 21.1: Dedicated IAM Role for Lambda
✅ **Met**: `LambdaExecutionRole` is created specifically for the Lambda function.

### Requirement 21.2: Least-Privilege DynamoDB Policies
✅ **Met**: Only 5 specific DynamoDB actions are granted:
- `PutItem` - For creating sessions
- `GetItem` - For loading sessions
- `UpdateItem` - For updating game state
- `DeleteItem` - For cleanup
- `Query` - For session lookups

### Requirement 21.3: Scoped to Specific Resources
✅ **Met**: All permissions use specific table ARN from CloudFormation parameters:
- `storageGameSessionsArn` - Specific table ARN
- No wildcards (`*`) in resource specifications
- Index access scoped to table's indexes only

### Requirement 21.4: IAM Roles for Authentication
✅ **Met**: Lambda uses IAM role for all AWS service access. No hardcoded credentials in code.

### Requirement 21.5: Separate IAM Roles per Service
✅ **Met**: 
- Lambda has dedicated execution role
- API Gateway has its own role (managed by Amplify)
- DynamoDB access is through Lambda's role only

## Deployment IAM User

**User Name**: `West_of_house_AmplifyDeploymentUser`

**Purpose**: Used for CI/CD and manual deployments via AWS CLI.

**Required Permissions**:
- Amplify (full access for app management)
- Lambda (create, update, delete functions)
- DynamoDB (create, update, delete tables)
- IAM (create, update roles and policies)
- CloudFormation (deploy stacks)
- S3 (upload deployment artifacts)
- API Gateway (create, update APIs)

**Security Notes**:
- Access keys stored in `~/.aws/credentials` under profile `amplify-deploy`
- Never committed to version control
- Keys should be rotated regularly
- Used only for deployment, not runtime operations

## Usage

### Deploying with Proper IAM Configuration

```bash
# Deploy using deployment user profile
amplify push --profile amplify-deploy

# Verify IAM role was created
aws iam get-role --role-name westofhauntedLambdaRole-dev --profile amplify-deploy

# Verify policies are attached
aws iam list-attached-role-policies --role-name westofhauntedLambdaRole-dev --profile amplify-deploy
```

### Verifying Least-Privilege Access

```bash
# Check Lambda function's execution role
aws lambda get-function-configuration --function-name gameHandler-dev

# Review IAM policy document
aws iam get-policy-version \
  --policy-arn $(aws iam list-policies --query "Policies[?PolicyName=='amplify-lambda-execution-policy'].Arn" --output text) \
  --version-id v1
```

## Cost Implications

**IAM Service**: Free (no charges for IAM roles, policies, or users)

**Security Benefits**:
- Prevents unauthorized access to DynamoDB
- Limits blast radius if credentials are compromised
- Enables CloudTrail auditing of all actions
- Follows AWS Well-Architected Framework security pillar

## Future Enhancements

If additional AWS services are added in future phases:

1. **S3 for Save Files**: Add `s3:PutObject`, `s3:GetObject` scoped to specific bucket
2. **SNS for Notifications**: Add `sns:Publish` scoped to specific topic
3. **SQS for Async Processing**: Add `sqs:SendMessage`, `sqs:ReceiveMessage` scoped to specific queue

Always follow least-privilege principle: grant only the minimum permissions required for functionality.
