#!/bin/bash

# Start Sandbox Script for West of Haunted House
# This script will:
# 1. Stop any existing sandboxes
# 2. Copy code from src to amplify
# 3. Start the backend sandbox
# 4. Start the frontend dev server

set -e  # Exit on any error

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    echo "Installation instructions: https://aws.amazon.com/cli/"
    exit 1
fi

echo "🔮 West of Haunted House - Starting Sandbox Environment"
echo "======================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Step 1: Stop any existing sandboxes
print_step "Stopping any existing sandboxes..."

# Kill ampx sandbox processes
AMPX_PIDS=$(ps aux | grep 'ampx sandbox' | grep -v grep | awk '{print $2}')
if [ -n "$AMPX_PIDS" ]; then
    echo "Found running Amplify sandbox processes: $AMPX_PIDS"
    kill $AMPX_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    AMPX_PIDS=$(ps aux | grep 'ampx sandbox' | grep -v grep | awk '{print $2}')
    if [ -n "$AMPX_PIDS" ]; then
        kill -9 $AMPX_PIDS 2>/dev/null || true
    fi
    print_success "Stopped Amplify sandbox"
fi

# Kill frontend dev servers
DEV_PIDS=$(ps aux | grep 'npm run dev\|vite' | grep -v grep | awk '{print $2}')
if [ -n "$DEV_PIDS" ]; then
    echo "Found running dev servers: $DEV_PIDS"
    kill $DEV_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    DEV_PIDS=$(ps aux | grep 'npm run dev\|vite' | grep -v grep | awk '{print $2}')
    if [ -n "$DEV_PIDS" ]; then
        kill -9 $DEV_PIDS 2>/dev/null || true
    fi
    print_success "Stopped frontend dev server"
fi

# Step 2: Copy code from src to amplify
print_step "Copying source code to amplify directory..."

# Ensure directories exist
mkdir -p amplify/functions/game-handler/data

# Copy Python files
cp src/lambda/game_handler/*.py amplify/functions/game-handler/
if [ $? -eq 0 ]; then
    print_success "Copied Python files"
else
    print_error "Failed to copy Python files"
    exit 1
fi

# Copy data files
cp src/lambda/game_handler/data/*.json amplify/functions/game-handler/data/
if [ $? -eq 0 ]; then
    print_success "Copied data files"
else
    print_error "Failed to copy data files"
    exit 1
fi

print_success "All files copied successfully"

# Step 3: Clear game data from DynamoDB (sandbox only)
print_step "Clearing sandbox game data from DynamoDB..."

# Get AWS region from amplify outputs if available
AWS_REGION=${AWS_REGION:-"us-east-1"}

# Get sandbox identifier from environment or use default
SANDBOX_ID=${AMPLIFY_SANDBOX_ID:-"iolaire"}

# First, try to get the table name from amplify outputs
if [ -f "amplify_outputs.json" ]; then
    TABLE_NAME=$(cat amplify_outputs.json | jq -r '.custom.GameSessionTableName' 2>/dev/null || echo "")
fi

# If not found in outputs, look for tables with "sandbox" in the name or tagged for sandbox
if [ -z "$TABLE_NAME" ]; then
    # Look for tables with sandbox in the name
    TABLE_NAME=$(aws dynamodb list-tables --region $AWS_REGION --output text 2>/dev/null | grep -i "sandbox.*GameSession\|GameSession.*sandbox" | head -1 | awk '{print $2}')
fi

# If still not found, check table tags to find sandbox tables
if [ -z "$TABLE_NAME" ]; then
    # Get all tables and check their tags
    for TABLE in $(aws dynamodb list-tables --region $AWS_REGION --output text 2>/dev/null | awk '/TABLENAMES/ {for(i=2;i<=NF;i++) print $i}'); do
        # Check if table has GameSession in name and sandbox tag
        if [[ $TABLE == *"GameSession"* ]]; then
            # Check tags for this table
            ENV_TAG=$(aws dynamodb list-tags-of-resource --resource-arn "arn:aws:dynamodb:$AWS_REGION:$(aws sts get-caller-identity --query Account --output text):table/$TABLE" --region $AWS_REGION --output text 2>/dev/null | grep -i "sandbox" | head -1)
            if [ -n "$ENV_TAG" ]; then
                TABLE_NAME=$TABLE
                break
            fi
        fi
    done
fi

# If we found a sandbox-specific table, clear it
if [ -n "$TABLE_NAME" ]; then
    echo "Found sandbox table: $TABLE_NAME"

    # Check if table exists
    if aws dynamodb describe-table --table-name "$TABLE_NAME" --region $AWS_REGION > /dev/null 2>&1; then
        # Get all items and delete them
        echo "Scanning sandbox table for items to delete..."

        # Get all session IDs
        SESSION_IDS=$(aws dynamodb scan --table-name "$TABLE_NAME" --projection-expression "sessionId" --region $AWS_REGION --output text 2>/dev/null | grep -E "SESSIONID" | awk '{print $2}')

        if [ -n "$SESSION_IDS" ]; then
            echo "Found sandbox sessions to delete: $SESSION_IDS"

            # Delete each session
            for SESSION_ID in $SESSION_IDS; do
                echo "Deleting sandbox session: $SESSION_ID"
                aws dynamodb delete-item --table-name "$TABLE_NAME" --key "{\"sessionId\":{\"S\":\"$SESSION_ID\"}}" --region $AWS_REGION > /dev/null 2>&1
            done

            print_success "Cleared sandbox game sessions from DynamoDB"
        else
            print_warning "No sandbox sessions found in table"
        fi
    fi
else
    # Check if there's a production table we should avoid
    PROD_TABLE=$(aws dynamodb list-tables --region $AWS_REGION --output text 2>/dev/null | grep -i "GameSession" | grep -v -i "sandbox" | head -1 | awk '{print $2}')

    if [ -n "$PROD_TABLE" ]; then
        print_warning "Found production table: $PROD_TABLE - SKIPPING (use --force to clear all tables)"
    else
        print_warning "No GameSession tables found (will be created on first deployment)"
    fi
fi

# Step 4: Start the backend sandbox
print_step "Starting Amplify backend sandbox..."

# Start backend in background and capture output
npx ampx sandbox > amplify-sandbox.log 2>&1 &
AMPX_PID=$!

echo "Backend PID: $AMPX_PID"

# Wait for backend to initialize
print_step "Waiting for backend to initialize..."
BACKEND_READY=false
for i in {1..60}; do  # Wait up to 60 seconds
    if grep -q "Deployment completed\|✔ Deployment completed" amplify-sandbox.log; then
        BACKEND_READY=true
        print_success "Backend is ready!"
        break
    fi
    if grep -q "Error\|error\|ERROR" amplify-sandbox.log; then
        print_error "Backend initialization failed"
        tail -20 amplify-sandbox.log
        exit 1
    fi
    sleep 1
    echo -n "."
done

echo ""

if [ "$BACKEND_READY" = false ]; then
    print_warning "Backend might still be initializing, proceeding anyway..."
    tail -20 amplify-sandbox.log
fi

# Extract the API endpoint if available
API_ENDPOINT=$(grep -o 'AppSync API endpoint = [^[:space:]]*' amplify-sandbox.log | sed 's/AppSync API endpoint = //' || echo "")
if [ -n "$API_ENDPOINT" ]; then
    print_success "API Endpoint: $API_ENDPOINT"
fi

# Step 4: Start the frontend dev server
print_step "Starting frontend development server..."

# Start frontend in background
npm run dev > frontend-dev.log 2>&1 &
FRONTEND_PID=$!

echo "Frontend PID: $FRONTEND_PID"

# Wait a moment for frontend to start
sleep 3

# Check if frontend is running
if ps -p $FRONTEND_PID > /dev/null; then
    print_success "Frontend is starting..."

    # Try to extract the URL
    FRONTEND_URL=$(grep -o 'Local:\s*http://[^[:space:]]*' frontend-dev.log | head -1 | sed 's/Local: //' || echo "")
    if [ -n "$FRONTEND_URL" ]; then
        print_success "Frontend URL: $FRONTEND_URL"
    else
        print_warning "Frontend URL not detected yet, check frontend-dev.log"
    fi
else
    print_error "Failed to start frontend"
    tail -20 frontend-dev.log
    exit 1
fi

# Step 5: Show status and instructions
echo ""
echo "======================================================"
echo -e "${GREEN}✓ Sandbox environment is running!${NC}"
echo ""
echo "📋 Process Information:"
echo "  Backend PID:  $AMPX_PID"
echo "  Frontend PID: $FRONTEND_PID"
echo ""
echo "📝 Log Files:"
echo "  Backend:   amplify-sandbox.log"
echo "  Frontend:  frontend-dev.log"
echo ""
echo "🛑 To stop everything, run:"
echo "  kill $AMPX_PID $FRONTEND_PID"
echo ""
echo "🔍 To monitor logs:"
echo "  Backend:   tail -f amplify-sandbox.log"
echo "  Frontend:  tail -f frontend-dev.log"
echo "======================================================"

# Save PIDs to a file for easy cleanup
echo "$AMPX_PID" > .sandbox-backend.pid
echo "$FRONTEND_PID" > .sandbox-frontend.pid

print_success "PIDs saved to .sandbox-backend.pid and .sandbox-frontend.pid"