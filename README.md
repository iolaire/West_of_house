# West of Haunted House 🎃

A modern resurrection of the 1977 text adventure Zork I with Halloween-themed transformations. This project "performs a séance" on the original dead source code, transplanting classic Zork logic into a modern Python serverless architecture while rewriting the sunny fields and white houses into a grim, Halloween nightmare.

[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![DynamoDB](https://img.shields.io/badge/AWS-DynamoDB-blue.svg)](https://aws.amazon.com/dynamodb/)
[![Amplify Gen 2](https://img.shields.io/badge/AWS-Amplify%20Gen%202-purple.svg)](https://docs.amplify.aws/)

## 🎮 Overview

**West of Haunted House** is a serverless text adventure game that resurrects the classic Zork I with a spooky Halloween twist. Players navigate 110 haunted rooms, solve cursed puzzles, collect treasures, and manage their sanity as they explore a supernatural world.

### Key Features

- 🏚️ **110 Haunted Rooms**: Every location from Zork I transformed with spooky descriptions
- 👻 **Sanity System**: Mental health meter (0-100) that affects descriptions and gameplay
- 🎒 **Classic Mechanics**: Object interaction, inventory management, puzzle-solving
- 💰 **Treasure Collection**: Find and score valuable cursed artifacts
- 💡 **Light System**: Manage lamp battery to survive dark areas
- 📦 **Container Objects**: Mailboxes, trophy cases, and more
- ☁️ **Serverless Architecture**: AWS Lambda + DynamoDB for minimal costs (<$5/month)
- 🚀 **RESTful API**: JSON endpoints for React frontend integration

## 📋 Table of Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
- [Deployment](#deployment)
- [API Documentation](#api-documentation)
- [Cost Breakdown](#cost-breakdown)
- [Development](#development)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Security](#security)
- [Contributing](#contributing)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (AWS Amplify Hosting)           │
│  (Grimoire UI with left pane image, right pane text/input) │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS/JSON
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  AWS Amplify API Gateway                    │
│  - REST API endpoints                                       │
│  - Request routing                                          │
│  - CORS handling                                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              AWS Lambda Functions (Python 3.12)             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  game_handler Lambda (ARM64)                         │  │
│  │  - Command Parser                                    │  │
│  │  - Game State Manager                                │  │
│  │  - Action Executor                                   │  │
│  │  - Sanity System                                     │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  World Data (bundled in Lambda)                      │  │
│  │  - Rooms JSON (haunted descriptions)                 │  │
│  │  - Objects JSON (spooky interactions)                │  │
│  │  - Flags JSON (initial state)                        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              AWS DynamoDB (On-Demand)                       │
│  - Session storage (game state)                             │
│  - TTL for automatic cleanup                                │
│  - Pay-per-request pricing                                  │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Compute**: AWS Lambda (Python 3.12, ARM64 architecture)
- **API**: AWS Amplify API Gateway (REST)
- **Database**: AWS DynamoDB (on-demand billing)
- **Hosting**: AWS Amplify Hosting (React frontend)
- **Infrastructure**: AWS Amplify Gen 2 (TypeScript-based, code-first)
- **Testing**: pytest + Hypothesis (property-based testing)

## 📦 Prerequisites

### Required Software

- **Node.js**: v20.0.0 or later
- **npm**: v10.0.0 or later
- **Python**: 3.12
- **AWS CLI**: Latest version
- **Git**: For version control

### AWS Account Setup

1. **AWS Account**: Active AWS account with billing enabled
2. **IAM User**: Deployment user with appropriate permissions
3. **AWS CLI**: Configured with credentials

```bash
# Install AWS CLI (macOS)
brew install awscli

# Configure AWS CLI
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
# Default output format: json
```

### Python Environment

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/iolaire/West_of_house.git
cd West_of_house
```

### 2. Install Dependencies

```bash
# Install Node.js dependencies for Amplify
npm install

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure AWS Credentials

Create an IAM user for deployment:

```bash
# Create deployment user
aws iam create-user --user-name West_of_house_AmplifyDeploymentUser

# Attach deployment policy (see scripts/iam-deployment-policy.json)
aws iam put-user-policy \
  --user-name West_of_house_AmplifyDeploymentUser \
  --policy-name AmplifyDeploymentPolicy \
  --policy-document file://scripts/iam-deployment-policy.json

# Create access keys
aws iam create-access-key --user-name West_of_house_AmplifyDeploymentUser

# Configure AWS CLI profile
aws configure --profile amplify-deploy
```

### 4. Initialize Amplify Gen 2 Project

The project is already configured with Amplify Gen 2. To start a local sandbox:

```bash
# Start local development environment
npx ampx sandbox

# This creates a per-developer cloud environment for testing
# Access the sandbox at: http://localhost:3000
```

## 🌐 Deployment

### Deploy to AWS (Production)

The project uses a two-branch Git workflow:

- **`main` branch**: Development and testing (does NOT trigger deployments)
- **`production` branch**: Production deployments (triggers AWS Amplify deployment)

#### Standard Deployment Workflow

```bash
# 1. Work on main branch
git checkout main
git pull origin main

# 2. Make changes and test locally
# ... make changes ...
npx ampx sandbox  # Test in local sandbox

# 3. Commit changes
git add .
git commit -m "Feature: description of changes"
git push origin main

# 4. Deploy to production
git checkout production
git merge main --no-edit
git push origin production  # This triggers AWS deployment

# 5. Sync main with production
git checkout main
git merge production
git push origin main
```

#### Monitor Deployment

1. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
2. Select your app
3. View deployment progress (typically 5-12 minutes)
4. Check for build/deploy phase completion

### Manual Deployment (Alternative)

```bash
# Deploy using Amplify CLI
npx ampx pipeline-deploy --branch main --app-id <your-app-id>
```

### Verify Deployment

```bash
# Run verification script
./scripts/verify-gen2-deployment.sh

# Test deployed API
./scripts/test-production-api.sh
```

## 📚 API Documentation

### Base URL

```
https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
```

### Endpoints

#### 1. Create New Game

**POST** `/game/new`

Creates a new game session and returns initial state.

**Request:**
```json
{}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "room": "west_of_house",
  "description": "You stand before a decrepit Victorian mansion, its windows like hollow eyes staring into your soul. The once-white paint peels away like dead skin, revealing rotting wood beneath. A rusted mailbox stands askew by the door, and dead vines claw at the walls. The air is thick with the scent of decay and something... else. Something watching.",
  "exits": ["NORTH", "SOUTH", "EAST", "WEST"],
  "items_visible": ["mailbox"],
  "inventory": [],
  "state": {
    "sanity": 100,
    "score": 0,
    "moves": 0,
    "lamp_battery": 200
  }
}
```

#### 2. Execute Command

**POST** `/game/command`

Executes a player command and returns the result.

**Request:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "command": "go north"
}
```

**Response:**
```json
{
  "success": true,
  "message": "You cautiously approach the north side of the house, your footsteps echoing in the unnatural silence.",
  "room": "north_of_house",
  "description": "The north side of the house is even more forbidding. Shadows seem to move in the corners of your vision. A path leads into a dark forest to the north, and you can circle around to the east or west.",
  "exits": ["NORTH", "EAST", "WEST", "SOUTH"],
  "items_visible": [],
  "inventory": [],
  "state": {
    "sanity": 100,
    "score": 0,
    "moves": 1,
    "lamp_battery": 200
  },
  "notifications": []
}
```

#### 3. Get Game State

**GET** `/game/state/{session_id}`

Retrieves the complete current game state.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_room": "west_of_house",
  "inventory": ["lamp", "sword"],
  "flags": {
    "rug_moved": true,
    "trap_door_open": false,
    "grate_unlocked": false
  },
  "state": {
    "sanity": 95,
    "score": 0,
    "moves": 5,
    "lamp_battery": 195
  }
}
```

### Supported Commands

#### Movement
- `go [direction]` or just `[direction]`
- Directions: `north`, `south`, `east`, `west`, `up`, `down`, `in`, `out`

#### Object Interaction
- `take [object]` - Pick up an object
- `drop [object]` - Drop an object from inventory
- `examine [object]` - Look at an object closely
- `open [object]` - Open a container or door
- `close [object]` - Close a container or door
- `read [object]` - Read text on an object
- `move [object]` - Move an object (e.g., rug)

#### Utility
- `inventory` or `i` - Show what you're carrying
- `look` or `l` - Look around the current room
- `quit` - End the game

### Error Responses

```json
{
  "success": false,
  "error": {
    "code": "INVALID_SESSION",
    "message": "Session not found or expired",
    "details": "Session ID: abc123 does not exist"
  }
}
```

**Error Codes:**
- `400` - Bad Request (malformed JSON, invalid command)
- `404` - Not Found (invalid session ID)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error (unexpected exception)

## 💰 Cost Breakdown

### Estimated Monthly Costs (1000 games/month)

| Service | Usage | Cost |
|---------|-------|------|
| **AWS Lambda** | ~5,000 invocations<br>128MB memory<br>~500ms per request<br>ARM64 architecture | **$0.10** |
| **DynamoDB** | ~10,000 reads<br>~5,000 writes<br>On-demand billing<br>TTL cleanup | **$0.02** |
| **Amplify Hosting** | ~5GB data transfer<br>Static assets | **$0.50** |
| **API Gateway** | ~5,000 requests | **$0.02** |
| **CloudWatch Logs** | ~100MB logs | **$0.01** |
| **Total** | | **~$0.65/month** |

### Cost Optimization Features

- ✅ **ARM64 Architecture**: 20% better price-performance vs x86_64
- ✅ **On-Demand Billing**: Pay only for what you use
- ✅ **Minimal Memory**: 128MB Lambda allocation
- ✅ **TTL Cleanup**: Automatic session expiration (no manual cleanup costs)
- ✅ **Serverless**: No idle server costs
- ✅ **CDN Caching**: Reduced data transfer costs

### Scaling Costs

| Monthly Games | Estimated Cost |
|---------------|----------------|
| 500 | $0.50 |
| 1,000 | $0.65 |
| 2,000 | $1.20 |
| 5,000 | $2.80 |
| 10,000 | $5.50 |

**Note**: Costs remain well under $5/month target for typical usage.

## 🛠️ Development

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate

# Start local sandbox
npx ampx sandbox

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/test_command_parser.py

# Run property-based tests
pytest tests/property/
```

### Code Structure

```
amplify/functions/game-handler/
├── resource.ts           # Lambda function definition (TypeScript)
├── index.py              # Lambda entry point
├── game_engine.py        # Core game logic
├── command_parser.py     # Natural language parsing
├── state_manager.py      # Game state management
├── sanity_system.py      # Halloween sanity mechanics
├── world_loader.py       # Load JSON game data
├── requirements.txt      # Python dependencies
└── data/                 # Bundled game data
    ├── west_of_house_flags_haunted.json
    ├── west_of_house_objects_haunted.json
    └── west_of_house_rooms_haunted.json
```

### Adding New Features

1. Update requirements in `.kiro/specs/game-backend-api/requirements.md`
2. Update design in `.kiro/specs/game-backend-api/design.md`
3. Add tasks to `.kiro/specs/game-backend-api/tasks.md`
4. Implement feature with tests
5. Run full test suite
6. Deploy to production

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                 # Unit tests for individual components
├── property/             # Property-based tests (Hypothesis)
└── integration/          # End-to-end tests
```

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run property-based tests only
pytest tests/property/

# Run with coverage report
pytest --cov=amplify/functions/game-handler tests/

# Run specific test
pytest tests/unit/test_command_parser.py::test_parse_movement_command
```

### Property-Based Testing

This project uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing to verify correctness properties across many inputs.

Example property test:
```python
from hypothesis import given, strategies as st

# Feature: game-backend-api, Property 1: Session uniqueness
@given(st.integers(min_value=1, max_value=1000))
def test_session_uniqueness(num_sessions):
    """For any number of new games, all session IDs should be unique."""
    engine = GameEngine()
    session_ids = set()
    
    for _ in range(num_sessions):
        result = engine.create_new_game()
        assert result["session_id"] not in session_ids
        session_ids.add(result["session_id"])
```

### Test Coverage

Current test coverage: **>90%**

- Unit tests: Core functionality
- Property tests: Correctness properties (30 properties)
- Integration tests: End-to-end game flows

## 📁 Project Structure

```
west-of-haunted-house/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── package.json                  # Node.js dependencies
│
├── amplify/                      # AWS Amplify Gen 2 configuration
│   ├── backend.ts                # Backend definition
│   ├── data/
│   │   └── resource.ts           # DynamoDB table
│   ├── functions/
│   │   └── game-handler/
│   │       ├── resource.ts       # Lambda definition (TypeScript)
│   │       ├── index.py          # Lambda handler
│   │       ├── game_engine.py
│   │       ├── command_parser.py
│   │       ├── state_manager.py
│   │       ├── sanity_system.py
│   │       ├── world_loader.py
│   │       ├── requirements.txt
│   │       └── data/             # Game data
│   └── auth/
│       └── resource.ts
│
├── tests/                        # All tests
│   ├── unit/
│   ├── property/
│   └── integration/
│
├── scripts/                      # Deployment scripts
│   ├── deploy-gen2.sh
│   ├── verify-gen2-deployment.sh
│   ├── test-production-api.sh
│   └── iam-deployment-policy.json
│
├── documents/                    # Documentation
│   ├── HALLOWEEN_MECHANICS.md
│   ├── HAUNTED_TRANSFORMATION.md
│   └── deployment/
│
└── .kiro/                        # Kiro specs
    └── specs/
        └── game-backend-api/
            ├── requirements.md
            ├── design.md
            └── tasks.md
```

## 🔒 Security

### IAM Roles

**Lambda Execution Role**: Least-privilege access to DynamoDB
- Read/Write access to GameSessions table only
- CloudWatch Logs for debugging
- No wildcard (*) permissions

**Deployment User**: Scoped permissions for CI/CD
- Amplify, Lambda, DynamoDB, IAM, CloudFormation
- Specific resource ARNs (no wildcards)

### Security Best Practices

- ✅ No hardcoded credentials (uses IAM roles)
- ✅ Input validation on all commands
- ✅ Session expiration (1 hour TTL)
- ✅ Rate limiting (60 requests/minute per session)
- ✅ CORS configuration for frontend
- ✅ Encrypted data at rest (DynamoDB)
- ✅ HTTPS only (API Gateway)

### Resource Tagging

All AWS resources are tagged for tracking:
- `Project`: `west-of-haunted-house`
- `ManagedBy`: `vedfolnir`
- `Environment`: `dev` / `staging` / `prod`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Write tests for new features
- Update documentation as needed
- Use descriptive commit messages
- Keep PRs focused and atomic

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Original Zork I by Infocom (1977)
- ZIL source code preservation by the Interactive Fiction community
- AWS Amplify team for Gen 2 framework
- Hypothesis library for property-based testing

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/iolaire/West_of_house/issues)
- **Documentation**: See `documents/` folder
- **Specs**: See `.kiro/specs/game-backend-api/`

## 🗺️ Roadmap

### MVP (Current)
- ✅ Core gameplay mechanics
- ✅ Sanity system
- ✅ Basic puzzles
- ✅ Treasure collection
- ✅ RESTful API

### Future Phases
- ⏳ Combat system
- ⏳ NPC AI (thief, enemies)
- ⏳ Curse system
- ⏳ Blood moon cycles
- ⏳ Soul collection
- ⏳ Save/load functionality
- ⏳ Complex multi-step puzzles
- ⏳ Achievements and leaderboards
- ⏳ React frontend with 3D grimoire UI

---

**Built with 💀 by Vedfolnir**

*"In the darkness, something stirs..."*
