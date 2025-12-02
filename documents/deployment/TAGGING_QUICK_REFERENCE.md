# AWS Resource Tagging - Quick Reference

## Required Tags (All Resources)

| Tag Key | Tag Value | Purpose |
|---------|-----------|---------|
| `Project` | `west-of-haunted-house` | Project identification |
| `ManagedBy` | `vedfolnir` | Ownership tracking |
| `Environment` | `dev` / `prod` / etc. | Environment identification |

## Tagged Resources

✅ Lambda Function (`gameHandler`)  
✅ Lambda Execution Role  
✅ DynamoDB Table (`GameSessions`)  
✅ API Gateway REST API  
✅ API Gateway Stage  
✅ API Gateway IAM Role  

## Quick Commands

### Verify All Tags
```bash
./scripts/verify-resource-tags.sh
```

### List All Project Resources
```bash
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=west-of-haunted-house
```

### Check Specific Resource Tags

**Lambda:**
```bash
aws lambda list-tags --resource arn:aws:lambda:REGION:ACCOUNT:function:gameHandler-ENV
```

**DynamoDB:**
```bash
aws dynamodb list-tags-of-resource \
  --resource-arn arn:aws:dynamodb:REGION:ACCOUNT:table/GameSessions-ENV
```

**API Gateway:**
```bash
aws apigateway get-rest-api --rest-api-id API_ID
```

## Cost Tracking

### View Costs by Project
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter '{"Tags":{"Key":"Project","Values":["west-of-haunted-house"]}}'
```

### View Costs by Environment
```bash
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=TAG,Key=Environment \
  --filter '{"Tags":{"Key":"Project","Values":["west-of-haunted-house"]}}'
```

## Troubleshooting

### Missing Tags After Deployment
1. Verify CloudFormation templates have tags
2. Redeploy: `amplify push`
3. Run verification script

### Incorrect Tag Values
- Check CloudFormation template syntax
- Ensure `env` parameter is passed correctly
- Verify no typos in tag keys/values

### Resources Not Found
- Ensure resources are deployed
- Check AWS region
- Verify AWS credentials

## Files Modified

- `amplify/backend/function/gameHandler/gameHandler-cloudformation-template.json`
- `amplify/backend/storage/GameSessions/GameSessions-cloudformation-template.json`
- `amplify/backend/api/westofhouseapi/westofhouseapi-cloudformation-template.json`

## Documentation

- Full details: [AWS_RESOURCE_TAGGING.md](AWS_RESOURCE_TAGGING.md)
- Implementation: [TAGGING_IMPLEMENTATION_SUMMARY.md](TAGGING_IMPLEMENTATION_SUMMARY.md)
- Deployment: [../DEPLOYMENT.md](../DEPLOYMENT.md)
