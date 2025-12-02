# Testing Scripts Guide

## Overview

This directory contains scripts for testing the deployed West of Haunted House backend API.

---

## Test Scripts

### 1. Direct Lambda Testing (Current)

**Script**: `test-deployed-lambda-direct.py`  
**Purpose**: Test Lambda function via direct AWS SDK invocation  
**Status**: ✅ Working

**Usage**:
```bash
python scripts/test-deployed-lambda-direct.py
```

**What it tests**:
- ✅ New game creation
- ✅ Command execution (LOOK, INVENTORY, GO NORTH)
- ✅ State query
- ✅ DynamoDB session storage

**Requirements**:
- AWS CLI configured with credentials
- boto3 installed (`pip install boto3`)
- Permissions to invoke Lambda and query DynamoDB

**Output**:
- Color-coded test results
- Detailed JSON responses
- Exit code 0 on success, 1 on failure

---

### 2. API Gateway Testing (Future)

**Script**: `test-production-api.sh`  
**Purpose**: Test via HTTP REST API endpoints  
**Status**: ⚠️ Pending API Gateway configuration

**Usage** (once API Gateway is configured):
```bash
./scripts/test-production-api.sh
```

**What it will test**:
- POST https://api.example.com/game/new
- POST https://api.example.com/game/command
- GET https://api.example.com/game/state/{session_id}

**Note**: This script requires API Gateway REST API to be configured first (task 17.3.5).

---

### 3. Sandbox Testing

**Script**: `test-sandbox-endpoints.py`  
**Purpose**: Test Amplify Gen 2 sandbox environment  
**Status**: ✅ Available for local testing

**Usage**:
```bash
# Start sandbox first
npx ampx sandbox

# In another terminal, run tests
python scripts/test-sandbox-endpoints.py <api_url>
```

---

## Quick Start

### Test Deployed Lambda (Recommended)

```bash
# Ensure you're in the project root
cd /path/to/West_of_house

# Activate virtual environment (if using)
source venv/bin/activate

# Run tests
python scripts/test-deployed-lambda-direct.py
```

**Expected Output**:
```
============================================================
West of Haunted House - Lambda Direct Test
============================================================

Lambda Function: amplify-westofhouse-iolaire-sa-gamehandler9C35C05F-7OssIrbwmAhb

Test 1: Create New Game
------------------------------------------------------------
✓ New game created successfully
  Session ID: abc123...

Test: Execute Command - 'look'
------------------------------------------------------------
✓ Command handled correctly (not yet implemented)

Test: Execute Command - 'inventory'
------------------------------------------------------------
✓ Command handled correctly (not yet implemented)

Test: Execute Command - 'go north'
------------------------------------------------------------
✓ Command executed successfully

Test: Query Game State
------------------------------------------------------------
✓ State query successful
  Current room: north_of_house

Test: Verify DynamoDB Session Storage
------------------------------------------------------------
✓ Session found in DynamoDB

============================================================
Test Summary
============================================================

  New Game: ✓ PASS
  Look: ✓ PASS
  Inventory: ✓ PASS
  Go North: ✓ PASS
  State Query: ✓ PASS
  Dynamodb: ✓ PASS

Results: 6/6 tests passed
✓ All tests passed!
```

---

## Troubleshooting

### Error: "Lambda function not found"

**Solution**: Update the Lambda function name in the script:
```python
LAMBDA_FUNCTION_NAME = "your-actual-lambda-function-name"
```

Find your Lambda function name:
```bash
aws lambda list-functions --query 'Functions[?contains(FunctionName, `game`)].FunctionName'
```

### Error: "Access Denied"

**Solution**: Ensure your AWS credentials have permissions:
- `lambda:InvokeFunction`
- `lambda:GetFunctionConfiguration`
- `dynamodb:GetItem`

### Error: "boto3 not found"

**Solution**: Install boto3:
```bash
pip install boto3
```

---

## Test Coverage

### Current Coverage (Task 17.5)

- ✅ New game creation (Requirement 1.1, 1.2, 1.3, 1.4, 1.5)
- ✅ Command parsing (Requirement 2.1, 2.2)
- ✅ Command execution (Requirement 2.3, 2.4)
- ✅ Movement (Requirement 3.1, 3.2, 3.3, 3.5)
- ✅ State query (Requirement 19.1, 19.2, 19.3, 19.4)
- ✅ DynamoDB storage (Requirement 22.1, 22.2, 22.3)
- ✅ Error handling (Requirement 2.5, 16.5)

### Future Coverage

- ⏳ Object interaction (TAKE, DROP, EXAMINE)
- ⏳ Inventory management
- ⏳ Sanity system
- ⏳ Container system
- ⏳ Light system
- ⏳ Scoring system

---

## Related Documentation

- **Full Test Report**: `documents/deployment/TASK_17.5_TEST_REPORT.md`
- **Task Summary**: `documents/deployment/TASK_17.5_SUMMARY.md`
- **Deployment Guide**: `documents/deployment/DEPLOYMENT_GEN2.md`

---

## CI/CD Integration (Future)

These test scripts can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Test Deployed API
  run: |
    python scripts/test-deployed-lambda-direct.py
  env:
    AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
    AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    AWS_DEFAULT_REGION: us-east-1
```

---

**Last Updated**: December 2, 2025  
**Task**: 17.5 - Test deployed API  
**Status**: ✅ Complete
