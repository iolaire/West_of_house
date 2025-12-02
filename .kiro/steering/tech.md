# Technology Stack

## Backend

- **Runtime**: Python 3.12
- **Compute**: AWS Lambda (serverless, pay-per-invocation)
- **Architecture**: ARM64 (Graviton2 processors for better price-performance)
- **Database**: AWS DynamoDB (on-demand billing, session storage)
- **API**: AWS Amplify API Gateway (REST endpoints)
- **Deployment**: AWS Amplify Gen 2 (TypeScript-based, code-first infrastructure)
- **Infrastructure as Code**: TypeScript with AWS CDK (via Amplify Gen 2)
- **Security**: IAM roles with least-privilege policies (no hardcoded credentials)

## Frontend

- **Framework**: React
- **Hosting**: AWS Amplify Hosting with CDN
- **UI Concept**: Animated 3D grimoire (spellbook) interface

## Data Format

- **Game Data**: JSON files (rooms, objects, flags)
- **Naming Convention**: Haunted theme variants (e.g., `description_spooky`, `response_spooky`)
- **Data Files**: Bundled with Lambda deployment package

## Development Environment

- **Virtual Environment**: Python venv for dependency isolation
- **Location**: `venv/` directory (gitignored)
- **Python Version**: 3.12
- **Activation**: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)

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

## Amplify Gen 2 Requirements

**Why Gen 2:**
- Resolves Gen 1 CLI environment variable resolution issues
- TypeScript-based infrastructure (code-first, type-safe)
- Better DynamoDB integration with automatic environment variables
- Modern developer experience with sandbox environments
- Future-proof approach (recommended for all new projects)

**Gen 2 Project Structure:**
```
amplify/
├── backend.ts              # Backend definition entry point
├── data/
│   └── resource.ts         # DynamoDB table definitions
├── functions/
│   └── game-handler/
│       ├── resource.ts     # Lambda function definition (TypeScript)
│       ├── handler.py      # Python Lambda handler
│       └── requirements.txt
└── storage/
    └── resource.ts         # Additional storage if needed
```

**Gen 2 Key Concepts:**
- **Code-First**: Define infrastructure in TypeScript, not CLI commands
- **defineFunction**: TypeScript function to define Lambda functions
- **defineData**: TypeScript function to define DynamoDB tables
- **Sandbox**: Per-developer cloud environments for testing
- **Custom Functions**: Support for Python, Go, Java, and other runtimes

## Common Commands

### Amplify Gen 2 Deployment

```bash
# Create new Gen 2 project
npm create amplify@latest

# Install dependencies
npm install

# Start local sandbox (per-developer cloud environment)
npx ampx sandbox

# Deploy to cloud
npx ampx pipeline-deploy --branch main --app-id <app-id>

# Or deploy via Git push (recommended)
git push origin main
```

### Amplify Gen 1 (Legacy - for reference only)

```bash
# Initialize Amplify project
amplify init

# Add API with Lambda function
amplify add api

# Add DynamoDB storage
amplify add storage

# Deploy to AWS
amplify push
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
# Create virtual environment (first time only)
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Deactivate when done
deactivate
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
