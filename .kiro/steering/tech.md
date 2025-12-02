# Technology Stack

## Backend

- **Runtime**: Python 3.12
- **Compute**: AWS Lambda (serverless, pay-per-invocation)
- **Architecture**: ARM64 (Graviton2 processors for better price-performance)
- **Database**: AWS DynamoDB (on-demand billing, session storage)
- **API**: AWS Amplify API Gateway (REST endpoints)
- **Deployment**: AWS CLI + Amplify CLI with ZIP file deployment
- **Security**: IAM roles with least-privilege policies (no hardcoded credentials)

## Frontend

- **Framework**: React
- **Hosting**: AWS Amplify Hosting with CDN
- **UI Concept**: Animated 3D grimoire (spellbook) interface

## Data Format

- **Game Data**: JSON files (rooms, objects, flags)
- **Naming Convention**: Haunted theme variants (e.g., `description_spooky`, `response_spooky`)
- **Data Files**: Bundled with Lambda deployment package

## Testing

- **Unit Tests**: pytest
- **Property-Based Tests**: Hypothesis library (minimum 100 iterations per property)
- **Test Tagging**: `# Feature: game-backend-api, Property {number}: {property_text}`

## Security

**Runtime IAM Roles:**
- **Lambda Execution Role**: Dedicated role with least-privilege DynamoDB permissions
- **Least Privilege**: DynamoDB permissions scoped to specific table ARN
- **No Wildcards**: All IAM policies use specific resource ARNs
- **No Credentials**: Uses IAM roles for authentication (no hardcoded keys)
- **Separate Roles**: Different IAM roles for Lambda, API Gateway, and other services

**Deployment IAM User:**
- **Deployment User**: `West_of_house_AmplifyDeploymentUser` with permissions for Amplify, Lambda, DynamoDB, IAM, CloudFormation, S3, API Gateway
- **Access Keys**: Stored securely, never committed to version control
- **AWS CLI Profile**: Use `--profile amplify-deploy` for deployment commands
- **Key Rotation**: Rotate access keys regularly for security

## AWS Resource Tagging

**Required Tags (ALL resources MUST have these):**
- **Project**: `west-of-haunted-house` (identifies all resources for this project)
- **ManagedBy**: `vedfolnir` (identifies the managing entity)
- **Environment**: User-defined value (e.g., `dev`, `staging`, `prod`)

**Tagging Rules:**
- All AWS resources created by deployment scripts MUST include all three tags
- Amplify configuration files MUST specify these tags for automatic application
- Cleanup scripts MUST filter resources by all three tags to ensure safe deletion
- Cost tracking and resource queries MUST use these tags for filtering

## Cost Optimization

- **Target**: Under $5/month for typical usage (1000 games/month)
- **Lambda**: ARM64 architecture, 128MB memory allocation, <500ms execution time
- **ARM64 Benefit**: 20% better price-performance vs x86_64
- **DynamoDB**: TTL-based session cleanup, on-demand billing
- **Estimated Cost**: ~$0.50/month for 1000 games (with ARM64 savings)

## Common Commands

### Amplify Deployment

```bash
# Initialize Amplify project
amplify init

# Add API with Lambda function
amplify add api

# Add DynamoDB storage
amplify add storage

# Deploy to AWS (ensure tags are configured first)
amplify push

# Add hosting
amplify add hosting
```

### AWS Resource Management

```bash
# List all project resources by tags
aws resourcegroupstaggingapi get-resources \
  --tag-filters Key=Project,Values=west-of-haunted-house \
                Key=ManagedBy,Values=vedfolnir

# Cleanup all project resources (use with caution!)
./scripts/cleanup-aws-resources.sh

# Verify resource tags
aws lambda list-tags --resource <function-arn>
aws dynamodb list-tags-of-resource --resource-arn <table-arn>
```

### Lambda Packaging

```bash
# Package Lambda function with dependencies
cd amplify/backend/function/gameHandler/src
pip install -r requirements.txt -t .
zip -r ../function.zip .
```

### Testing

```bash
# Run all tests
pytest

# Run property-based tests only
pytest tests/property/

# Run with coverage
pytest --cov=src tests/
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Estimate AWS costs
python scripts/estimate_costs.py
```

## Key Libraries

- **boto3**: AWS SDK for Python (DynamoDB, Lambda)
- **pytest**: Testing framework
- **hypothesis**: Property-based testing
- **uuid**: Session ID generation

## Architecture Patterns

- **Serverless**: Pay-per-use, auto-scaling
- **Clean Separation**: API handler → Game logic → State management → Data persistence
- **Stateless Lambda**: All state stored in DynamoDB
- **Data Bundling**: JSON files packaged with Lambda for fast access
- **Session-Based**: Unique session ID per game instance
