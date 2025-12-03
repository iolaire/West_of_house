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

- **Node.js Version**: 24.x (latest LTS, supported until April 2028)
- **Virtual Environment**: Python venv for dependency isolation
- **Location**: `venv/` directory (gitignored)
- **Python Version**: 3.12
- **Activation**: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)

## Development Workflow

**Backend Development:**
1. Work in `src/lambda/game_handler/` for all Python code
2. Deployment scripts copy code to `amplify/functions/game-handler/`
3. Never edit files directly in `amplify/functions/` - they will be overwritten
4. Test locally from `src/lambda/game_handler/` directory
5. Deploy using Git workflow (push to `production` branch)

## Testing

**Backend (Python):**
- **Unit Tests**: pytest
- **Property-Based Tests**: Hypothesis library (minimum 100 iterations per property)
- **Test Tagging**: `# Feature: game-backend-api, Property {number}: {property_text}`

**Frontend (React/TypeScript):**
- **Test Framework**: Vitest with React Testing Library
- **Property-Based Tests**: fast-check library (minimum 100 iterations per property)
- **Test Command**: `npm test` (already includes `--run` flag, do NOT add it again)
- **Watch Mode**: `npm run test:watch`
- **UI Mode**: `npm run test:ui`
- **Test Location**: `src/test/` directory

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

## Git Workflow

**Branch Strategy:**
- **`main` branch**: Active development and testing
  - All development work happens here
  - Commit and push changes frequently
  - Test locally before merging to production
  - Safe to experiment and iterate

- **`production` branch**: Production deployments only
  - Triggers automatic AWS Amplify deployment on push
  - Only merge from `main` when ready to deploy
  - Keep clean and deployment-ready
  - Represents live production state

**Development Workflow:**

1. **Work on `main` branch** (default)
   ```bash
   git checkout main
   # Make changes, test locally
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

2. **When ready to deploy to AWS**
   ```bash
   # Switch to production branch
   git checkout production
   
   # Merge changes from main
   git merge main
   
   # Push to trigger Amplify deployment
   git push origin production
   ```

3. **After deployment, sync main with production**
   ```bash
   git checkout main
   git merge production
   git push origin main
   ```

**Benefits:**
- 🔒 Production branch stays clean and deployment-ready
- 🚀 Deployments only happen when explicitly merged to production
- 🧪 Can test and iterate on main without triggering deployments
- 📊 Clear separation between development and production code
- 🔄 Easy rollback by reverting production branch commits

**Important Notes:**
- Never commit directly to `production` - always merge from `main`
- Always test on `main` before merging to `production`
- Keep `main` and `production` in sync after deployments
- Use descriptive commit messages for deployment tracking

## Common Commands

### Git Workflow Commands

```bash
# Start new feature on main
git checkout main
git pull origin main

# Make changes and commit
git add .
git commit -m "Feature: description"
git push origin main

# Deploy to production
git checkout production
git merge main --no-edit
git push origin production

# Sync main after deployment
git checkout main
git merge production
git push origin main

# Check branch status
git status
git log --oneline --graph --all --decorate -10
```

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
                Key=ManagedBy,Values=vedfolnir \
  --output json

# Cleanup all project resources (use with caution!)
./scripts/cleanup-aws-resources.sh

# Verify resource tags
aws lambda list-tags --resource <function-arn> --output json
aws dynamodb list-tags-of-resource --resource-arn <table-arn> --output json
```

**Important**: Always use `--output json` with AWS CLI commands to prevent terminal overflow from table formatting.

### Lambda Development and Deployment

```bash
# Work in source directory
cd src/lambda/game_handler/

# Install dependencies for local testing
pip install -r requirements.txt

# Run tests from project root
pytest tests/

# Deployment copies files to amplify/functions/game-handler/
# This happens automatically via deployment scripts or Git push to production
```

### Testing

**Backend (Python):**
```bash
# Run all tests
pytest

# Run property-based tests only
pytest tests/property/

# Run with coverage
pytest --cov=src tests/
```

**Frontend (React/TypeScript):**
```bash
# Run all tests (includes --run flag automatically)
npm test

# Run specific test file
npm test src/test/RoomImage.property.test.tsx

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui
```

### Local Development

```bash
# Create virtual environment (first time only)
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies (from project root)
pip install -r requirements.txt

# Work in source directory
cd src/lambda/game_handler/

# Run tests (from project root)
cd ../../..
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Deactivate when done
deactivate
```

**Important:** Always develop in `src/lambda/game_handler/`, not in `amplify/functions/game-handler/`

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
