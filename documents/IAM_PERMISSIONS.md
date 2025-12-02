# IAM Permissions Configuration

## Overview

This document describes the IAM permissions configuration for the West of Haunted House backend Lambda function. The configuration follows AWS security best practices and the principle of least privilege.

**Requirements**: 21.1, 21.2, 21.3, 21.4

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Lambda Function                          │
│                   (game-handler)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Assumes
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              IAM Execution Role                             │
│   amplify-{app-id}-{env}-gameHandler-{hash}                │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Inline Policy: DynamoDB Access                      │  │
│  │  - dynamodb:GetItem                                  │  │
│  │  - dynamodb:PutItem                                  │  │
│  │  - dynamodb:UpdateItem                               │  │
│  │  - dynamodb:DeleteItem                               │  │
│  │  - dynamodb:Query                                    │  │
│  │  - dynamodb:Scan                                     │  │
│  │  - dynamodb:DescribeTable                            │  │
│  │                                                       │  │
│  │  Resource: arn:aws:dynamodb:{region}:{account}:     │  │
│  │            table/GameSession-{env}                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Inline Policy: CloudWatch Logs                      │  │
│  │  - logs:CreateLogGroup                               │  │
│  │  - logs:CreateLogStream                              │  │
│  │  - logs:PutLogEvents                                 │  │
│  │                                                       │  │
│  │  Resource: arn:aws:logs:{region}:{account}:         │  │
│  │            log-group:/aws/lambda/{function-name}:*   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## IAM Role

### Role Name Pattern
```
amplify-{app-id}-{env}-gameHandler-{hash}
```

Example:
```
amplify-d1a2b3c4d5e6-dev-gameHandler-a1b2c3d4
```

### Role Creation
The IAM role is automatically created by AWS Amplify Gen 2 during deployment. The role is dedicated to the Lambda function and follows AWS best practices for Lambda execution roles.

**Requirement 21.1**: ✓ Dedicated IAM role for Lambda execution

## DynamoDB Permissions

### Granted Actions

The Lambda function has the following DynamoDB permissions:

| Action | Purpose | Required For |
|--------|---------|--------------|
| `dynamodb:GetItem` | Retrieve session by sessionId | Loading game state |
| `dynamodb:PutItem` | Create new sessions and overwrite existing | New game, state updates |
| `dynamodb:UpdateItem` | Update specific session fields | Incremental state updates |
| `dynamodb:DeleteItem` | Delete expired sessions | Session cleanup |
| `dynamodb:Query` | Query sessions by attributes | Future admin features |
| `dynamodb:Scan` | Scan table for sessions | Future admin features |
| `dynamodb:DescribeTable` | Get table metadata | Validation and debugging |

### Resource Scoping

All DynamoDB permissions are scoped to the specific GameSession table ARN:

```json
{
  "Resource": "arn:aws:dynamodb:{region}:{account}:table/GameSession-{env}"
}
```

**No wildcard (*) permissions are used for DynamoDB resources.**

Example ARN:
```
arn:aws:dynamodb:us-east-1:123456789012:table/GameSession-dev
```

### Implementation

The permissions are granted in `amplify/backend.ts` using the CDK `grantReadWriteData()` method:

```typescript
backend.data.resources.tables['GameSession'].grantReadWriteData(
  backend.gameHandler.resources.lambda
);
```

This method automatically creates an inline IAM policy with the minimum required permissions scoped to the specific table.

**Requirement 21.2**: ✓ Least-privilege DynamoDB permissions
**Requirement 21.3**: ✓ Permissions scoped to specific table ARN (no wildcards)

## CloudWatch Logs Permissions

### Granted Actions

The Lambda function has the following CloudWatch Logs permissions:

| Action | Purpose |
|--------|---------|
| `logs:CreateLogGroup` | Create log group for function |
| `logs:CreateLogStream` | Create log streams within the group |
| `logs:PutLogEvents` | Write log events to streams |

### Resource Scoping

CloudWatch Logs permissions are scoped to the function's log group:

```json
{
  "Resource": "arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{function-name}:*"
}
```

**Note**: The `:*` suffix is required for CloudWatch Logs to allow writing to any log stream within the log group. This is an AWS requirement and does not violate the least-privilege principle.

Example ARN:
```
arn:aws:logs:us-east-1:123456789012:log-group:/aws/lambda/amplify-d1a2b3c4d5e6-dev-gameHandler-a1b2c3d4:*
```

### Implementation

CloudWatch Logs permissions are automatically granted by AWS Amplify when creating a Lambda function. No explicit configuration is required.

**Requirement 21.4**: ✓ CloudWatch Logs permissions for debugging

## Verification

### Manual Verification

To verify the IAM permissions after deployment:

1. **Find the Lambda function**:
   ```bash
   aws lambda list-functions \
     --query "Functions[?Tags.Project=='west-of-haunted-house'].FunctionName" \
     --output text
   ```

2. **Get the IAM role**:
   ```bash
   aws lambda get-function \
     --function-name <function-name> \
     --query 'Configuration.Role' \
     --output text
   ```

3. **List attached policies**:
   ```bash
   aws iam list-attached-role-policies \
     --role-name <role-name>
   ```

4. **List inline policies**:
   ```bash
   aws iam list-role-policies \
     --role-name <role-name>
   ```

5. **Get inline policy document**:
   ```bash
   aws iam get-role-policy \
     --role-name <role-name> \
     --policy-name <policy-name>
   ```

### Automated Verification

Use the provided verification script:

```bash
./scripts/verify-iam-permissions.sh [function-name]
```

The script will:
- Discover the Lambda function (if name not provided)
- Extract the IAM role
- List all attached and inline policies
- Verify DynamoDB permissions
- Verify CloudWatch Logs permissions
- Check for wildcard usage
- Generate a requirements checklist

## Security Best Practices

### ✓ Implemented

1. **Dedicated IAM Role**: Each Lambda function has its own IAM role
2. **Least Privilege**: Only the minimum required permissions are granted
3. **Resource Scoping**: All permissions are scoped to specific resource ARNs
4. **No Hardcoded Credentials**: Uses IAM roles for authentication
5. **Separation of Concerns**: Different policies for different services

### ✓ Avoided

1. **No Wildcard Resources**: DynamoDB permissions use specific table ARNs
2. **No Overly Broad Actions**: Only required actions are granted
3. **No Shared Roles**: Each function has its own dedicated role
4. **No Hardcoded Keys**: No AWS access keys in code or configuration

## Troubleshooting

### Permission Denied Errors

If you encounter permission denied errors:

1. **Check the IAM role**: Verify the Lambda function is using the correct role
   ```bash
   aws lambda get-function --function-name <function-name> --query 'Configuration.Role'
   ```

2. **Verify DynamoDB permissions**: Ensure the role has the required DynamoDB actions
   ```bash
   ./scripts/verify-iam-permissions.sh <function-name>
   ```

3. **Check resource ARNs**: Verify the policy resources match the actual table ARN
   ```bash
   aws dynamodb describe-table --table-name GameSession-dev --query 'Table.TableArn'
   ```

4. **Review CloudWatch Logs**: Check the Lambda logs for specific permission errors
   ```bash
   aws logs tail /aws/lambda/<function-name> --follow
   ```

### Common Issues

**Issue**: `AccessDeniedException: User is not authorized to perform: dynamodb:GetItem`

**Solution**: The IAM role is missing DynamoDB permissions. Redeploy the Amplify backend to recreate the IAM policies.

**Issue**: `ResourceNotFoundException: Requested resource not found`

**Solution**: The table name in the Lambda environment variable doesn't match the actual table. Verify the `TABLE_NAME` environment variable.

**Issue**: `Unable to create log group`

**Solution**: The IAM role is missing CloudWatch Logs permissions. This should be automatically granted by Amplify, but can be manually added if needed.

## References

- [AWS Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [DynamoDB IAM Permissions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/iam-policy-specific-table-indexes.html)
- [CloudWatch Logs Permissions](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/permissions-reference-cwl.html)
- [Amplify Gen 2 Functions](https://docs.amplify.aws/react/build-a-backend/functions/)

## Compliance

This IAM configuration satisfies the following requirements:

- ✓ **21.1**: Dedicated IAM role for Lambda execution
- ✓ **21.2**: Least-privilege DynamoDB permissions (only required actions)
- ✓ **21.3**: Permissions scoped to specific resources (no wildcards for DynamoDB)
- ✓ **21.4**: CloudWatch Logs permissions for debugging

All requirements are met through the Amplify Gen 2 configuration in `amplify/backend.ts`.
