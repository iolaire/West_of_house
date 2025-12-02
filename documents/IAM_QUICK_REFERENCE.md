# IAM Permissions Quick Reference

## Summary

The West of Haunted House Lambda function has been configured with least-privilege IAM permissions following AWS security best practices.

## ✓ Requirements Met

| Requirement | Status | Implementation |
|-------------|--------|----------------|
| 21.1 - Dedicated IAM role | ✓ Complete | Amplify creates role: `amplify-{app-id}-{env}-gameHandler-{hash}` |
| 21.2 - Least-privilege DynamoDB | ✓ Complete | `grantReadWriteData()` grants only required actions |
| 21.3 - No wildcard permissions | ✓ Complete | All DynamoDB permissions scoped to specific table ARN |
| 21.4 - CloudWatch Logs | ✓ Complete | Automatically granted by Amplify for debugging |

## DynamoDB Permissions

**Actions Granted**:
- `dynamodb:GetItem` - Load game sessions
- `dynamodb:PutItem` - Create/update sessions
- `dynamodb:UpdateItem` - Update session fields
- `dynamodb:DeleteItem` - Delete expired sessions
- `dynamodb:Query` - Query sessions (future features)
- `dynamodb:Scan` - Scan table (admin features)
- `dynamodb:DescribeTable` - Get table metadata

**Resource**: `arn:aws:dynamodb:{region}:{account}:table/GameSession-{env}`

**No wildcards used** ✓

## CloudWatch Logs Permissions

**Actions Granted**:
- `logs:CreateLogGroup` - Create log group
- `logs:CreateLogStream` - Create log streams
- `logs:PutLogEvents` - Write log events

**Resource**: `arn:aws:logs:{region}:{account}:log-group:/aws/lambda/{function-name}:*`

**Note**: The `:*` suffix is required by AWS for log streams and is acceptable.

## Configuration Files

| File | Purpose |
|------|---------|
| `amplify/backend.ts` | Grants DynamoDB permissions via `grantReadWriteData()` |
| `amplify/functions/game-handler/resource.ts` | Documents IAM permissions in comments |
| `documents/IAM_PERMISSIONS.md` | Detailed IAM permissions documentation |
| `scripts/verify-iam-permissions.sh` | Automated verification script |

## Verification

### Quick Check
```bash
./scripts/verify-iam-permissions.sh
```

### Manual Check
```bash
# Find function
aws lambda list-functions --query "Functions[?Tags.Project=='west-of-haunted-house'].FunctionName"

# Get role
aws lambda get-function --function-name <name> --query 'Configuration.Role'

# List policies
aws iam list-role-policies --role-name <role>
```

## Security Principles Applied

✓ **Least Privilege**: Only minimum required permissions granted
✓ **Resource Scoping**: All permissions scoped to specific ARNs
✓ **No Wildcards**: DynamoDB permissions use specific table ARN
✓ **Separation of Concerns**: Different policies for different services
✓ **No Hardcoded Credentials**: Uses IAM roles for authentication

## Next Steps

After deployment, run the verification script to confirm:
```bash
./scripts/verify-iam-permissions.sh
```

This will validate that all IAM permissions are correctly configured and meet the requirements.
