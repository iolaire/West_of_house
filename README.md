# West of Haunted House

A modern resurrection of the 1977 text adventure Zork I with Halloween-themed transformations. This project "performs a séance" on the original dead source code, transplanting classic Zork logic into a modern Python serverless architecture while rewriting the sunny fields and white houses into a grim, Halloween nightmare.

## Overview

Players interact with a React web app presented as an animated 3D grimoire (spellbook). They type text commands to navigate a haunted world, solve puzzles, collect cursed treasures, and manage their sanity as they explore 110 rooms of supernatural horror.

## Architecture

- **Backend**: AWS Lambda (Python 3.12, ARM64) + DynamoDB
- **API**: AWS Amplify API Gateway (REST)
- **Frontend**: React (hosted on AWS Amplify)
- **Cost Target**: <$5/month for typical usage

## Prerequisites

- Python 3.12+
- Node.js 18+ and npm
- AWS CLI configured
- AWS Amplify CLI (`npm install -g @aws-amplify/cli`)
- AWS account with appropriate permissions

## Setup Instructions

### 1. Create Deployment IAM User

The deployment process requires an IAM user with specific permissions for Amplify, Lambda, DynamoDB, and related services.

**Automated Setup:**

```bash
# Run the setup script
./scripts/setup-deployment-user.sh
```

This script will:
1. Create IAM user `West_of_house_AmplifyDeploymentUser`
2. Attach deployment policy with least-privilege permissions
3. Generate access keys
4. Display configuration instructions

**Manual Setup:**

If you prefer manual setup:

```bash
# Create the IAM user
aws iam create-user --user-name West_of_house_AmplifyDeploymentUser

# Attach the deployment policy
aws iam put-user-policy \
  --user-name West_of_house_AmplifyDeploymentUser \
  --policy-name AmplifyDeploymentPolicy \
  --policy-document file://scripts/iam-deployment-policy.json

# Create access keys
aws iam create-access-key --user-name West_of_house_AmplifyDeploymentUser
```

**Configure AWS CLI Profile:**

```bash
# Configure the deployment profile
aws configure --profile amplify-deploy

# Enter the Access Key ID and Secret Access Key from the previous step
# Default region: us-east-1 (or your preferred region)
# Default output format: json

# Test the profile
aws sts get-caller-identity --profile amplify-deploy
```

**Security Best Practices:**

- ⚠️ **NEVER commit access keys to version control**
- Store credentials securely (password manager, AWS Secrets Manager)
- Rotate access keys regularly (every 90 days recommended)
- Use environment variables or AWS profiles for credentials
- Add `.env` and `aws-credentials.txt` to `.gitignore`

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r src/lambda/game_handler/requirements.txt

# Install Amplify CLI globally
npm install -g @aws-amplify/cli

# Configure Amplify (if first time)
amplify configure
```

### 3. Initialize Amplify Project

```bash
# Set the deployment profile
export AWS_PROFILE=amplify-deploy

# Initialize Amplify
amplify init

# Follow the prompts:
# - Project name: west-of-haunted-house
# - Environment: dev
# - Default editor: (your choice)
# - App type: javascript
# - Framework: react
# - Source directory: src
# - Distribution directory: build
# - Build command: npm run build
# - Start command: npm start
```

### 4. Add Backend Resources

```bash
# Add REST API with Lambda function
amplify add api
# - Select: REST
# - Provide friendly name: gameAPI
# - Provide path: /api
# - Lambda source: Create new Lambda function
# - Function name: gameHandler
# - Runtime: Python 3.12
# - Template: Serverless ExpressJS function (we'll customize)

# Add DynamoDB table
amplify add storage
# - Select: NoSQL Database
# - Table name: GameSessions
# - Partition key: sessionId (String)
# - Sort key: (none)
# - Add indexes: No
# - Enable TTL: Yes (expires field)
```

### 5. Deploy to AWS

```bash
# Package Lambda function (if needed)
./scripts/package_lambda.sh

# Deploy all resources
amplify push

# Review the changes and confirm
```

### 6. Add Hosting (Optional)

```bash
# Add Amplify hosting
amplify add hosting
# - Select: Amplify Console
# - Manual deployment

# Publish the app
amplify publish
```

## Project Structure

```
west-of-haunted-house/
├── README.md                     # This file
├── .gitignore                    # Git ignore rules
├── project.md                    # Project overview
│
├── documents/                    # Project documentation
│   ├── HALLOWEEN_MECHANICS.md    # Halloween flag system
│   ├── FLAG_TRANSFORMATIONS.md   # Zork to haunted mappings
│   └── game_overview.md          # Game design overview
│
├── data/                         # Game data (JSON files)
│   ├── rooms_haunted.json        # Room definitions
│   ├── objects_haunted.json      # Object definitions
│   └── flags_haunted.json        # Initial flag states
│
├── src/                          # Backend source code
│   └── lambda/
│       └── game_handler/
│           ├── index.py          # Lambda entry point
│           ├── game_engine.py    # Core game logic
│           ├── command_parser.py # Command parsing
│           ├── state_manager.py  # State management
│           ├── sanity_system.py  # Sanity mechanics
│           ├── world_loader.py   # Load game data
│           └── requirements.txt  # Python dependencies
│
├── tests/                        # All tests
│   ├── unit/                     # Unit tests
│   ├── property/                 # Property-based tests
│   └── integration/              # Integration tests
│
├── scripts/                      # Deployment and utility scripts
│   ├── setup-deployment-user.sh  # IAM user setup
│   ├── iam-deployment-policy.json # IAM policy document
│   ├── package_lambda.sh         # Package Lambda function
│   └── deploy.sh                 # Deployment script
│
├── amplify/                      # Amplify configuration (generated)
│   └── backend/
│       ├── api/                  # API Gateway config
│       ├── function/             # Lambda functions
│       └── storage/              # DynamoDB tables
│
└── .kiro/                        # Kiro specs
    └── specs/
        └── game-backend-api/
            ├── requirements.md   # Requirements document
            ├── design.md         # Design document
            └── tasks.md          # Implementation tasks
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run property-based tests
pytest tests/property/

# Run with coverage
pytest --cov=src tests/
```

### Local Development

```bash
# Install dependencies
pip install -r src/lambda/game_handler/requirements.txt

# Run tests
pytest tests/

# Package Lambda function
./scripts/package_lambda.sh
```

### Deployment

```bash
# Set AWS profile
export AWS_PROFILE=amplify-deploy

# Deploy backend changes
amplify push

# Deploy frontend and backend
amplify publish
```

## IAM Roles and Security

### Runtime IAM Role

The Lambda function uses a dedicated execution role with least-privilege permissions:

- **DynamoDB**: GetItem, PutItem, UpdateItem, DeleteItem (scoped to GameSessions table)
- **CloudWatch Logs**: CreateLogGroup, CreateLogStream, PutLogEvents
- **No wildcards**: All permissions scoped to specific resource ARNs

### Deployment IAM User

The `West_of_house_AmplifyDeploymentUser` has permissions for:

- AWS Amplify (full access for deployment)
- Lambda (create, update, delete functions)
- DynamoDB (create, update, delete tables)
- API Gateway (manage REST APIs)
- IAM (create and manage service roles)
- CloudFormation (manage stacks)
- S3 (deployment artifacts)

**Policy Location**: `scripts/iam-deployment-policy.json`

### Security Checklist

- ✅ No hardcoded credentials in code
- ✅ IAM roles for service authentication
- ✅ Least-privilege policies (no wildcards)
- ✅ Separate deployment and runtime roles
- ✅ Access keys stored securely (not in git)
- ✅ CloudWatch Logs for debugging
- ✅ DynamoDB TTL for automatic cleanup
- ✅ CORS configured for frontend domain

## Cost Estimation

**Target**: <$5/month for 1000 games/month

**Breakdown**:
- **Lambda**: ~$0.10/month (ARM64, 128MB, 500ms avg)
- **DynamoDB**: ~$0.02/month (on-demand, 10 reads + 5 writes per game)
- **Amplify Hosting**: ~$0.50/month (5MB per page load)
- **API Gateway**: ~$0.00/month (free tier covers 1M requests)

**Total**: ~$0.62/month (well under $5 target)

**Cost Optimization**:
- ARM64 architecture (20% better price-performance)
- On-demand DynamoDB billing (no idle costs)
- TTL-based session cleanup (no manual cleanup costs)
- Lambda memory optimized at 128MB
- Amplify CDN for frontend caching

## API Endpoints

### POST /api/game/new
Create a new game session.

**Response**:
```json
{
  "session_id": "uuid",
  "room": "west_of_house",
  "description": "spooky description...",
  "exits": ["NORTH", "SOUTH", "EAST", "WEST"],
  "items_visible": ["mailbox"],
  "state": {
    "sanity": 100,
    "score": 0,
    "moves": 0
  }
}
```

### POST /api/game/command
Execute a game command.

**Request**:
```json
{
  "session_id": "uuid",
  "command": "go north"
}
```

**Response**:
```json
{
  "success": true,
  "message": "spooky response text...",
  "room": "north_of_house",
  "description": "spooky description...",
  "inventory": ["lamp"],
  "state": {
    "sanity": 95,
    "score": 0,
    "moves": 1
  }
}
```

### GET /api/game/state/{session_id}
Get current game state.

**Response**:
```json
{
  "current_room": "west_of_house",
  "inventory": ["lamp"],
  "flags": {...},
  "state": {...}
}
```

## Troubleshooting

### Amplify Deployment Issues

```bash
# Check Amplify status
amplify status

# View CloudFormation events
aws cloudformation describe-stack-events --stack-name amplify-westofhauntedhouse-dev

# Check Lambda logs
aws logs tail /aws/lambda/gameHandler --follow --profile amplify-deploy
```

### IAM Permission Issues

```bash
# Verify IAM user
aws iam get-user --user-name West_of_house_AmplifyDeploymentUser

# List attached policies
aws iam list-user-policies --user-name West_of_house_AmplifyDeploymentUser

# Test credentials
aws sts get-caller-identity --profile amplify-deploy
```

### Lambda Function Issues

```bash
# Test Lambda function locally
aws lambda invoke --function-name gameHandler \
  --payload '{"command": "look"}' \
  response.json --profile amplify-deploy

# View Lambda configuration
aws lambda get-function-configuration --function-name gameHandler --profile amplify-deploy
```

## Contributing

This is a personal project, but suggestions and feedback are welcome! Please open an issue to discuss proposed changes.

## License

This project is inspired by the original Zork I (1977) by Infocom. The original game is now in the public domain. This resurrection is a creative reinterpretation with original Halloween-themed content.

## Acknowledgments

- Original Zork I by Marc Blank, Dave Lebling, Bruce Daniels, and Tim Anderson
- Infocom for creating the text adventure genre
- The interactive fiction community for keeping the genre alive

---

**Status**: MVP Development in Progress

**Next Steps**: See `.kiro/specs/game-backend-api/tasks.md` for implementation tasks
