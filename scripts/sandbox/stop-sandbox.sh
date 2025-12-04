#!/bin/bash

# Stop Sandbox Script for West of Haunted House
# This script will stop the sandbox environment

set -e

# Change to the project root directory
cd "$(dirname "$0")/../.."

# Check for --clear-data flag
CLEAR_DATA=false
if [ "$1" = "--clear-data" ] || [ "$1" = "-c" ]; then
    CLEAR_DATA=true
fi

echo "🛑 West of Haunted House - Stopping Sandbox Environment"
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

# Stop processes using saved PIDs if available
if [ -f ".sandbox-backend.pid" ]; then
    BACKEND_PID=$(cat .sandbox-backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        print_step "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID || true
        sleep 2
        if ps -p $BACKEND_PID > /dev/null 2>&1; then
            print_warning "Force killing backend..."
            kill -9 $BACKEND_PID || true
        fi
        print_success "Backend stopped"
    else
        print_warning "Backend process (PID: $BACKEND_PID) not found"
    fi
    rm -f .sandbox-backend.pid
fi

if [ -f ".sandbox-frontend.pid" ]; then
    FRONTEND_PID=$(cat .sandbox-frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        print_step "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID || true
        sleep 2
        if ps -p $FRONTEND_PID > /dev/null 2>&1; then
            print_warning "Force killing frontend..."
            kill -9 $FRONTEND_PID || true
        fi
        print_success "Frontend stopped"
    else
        print_warning "Frontend process (PID: $FRONTEND_PID) not found"
    fi
    rm -f .sandbox-frontend.pid
fi

# Also stop any stray processes
print_step "Checking for any remaining sandbox processes..."

# Kill ampx sandbox processes
AMPX_PIDS=$(ps aux | grep 'ampx sandbox' | grep -v grep | awk '{print $2}')
if [ -n "$AMPX_PIDS" ]; then
    echo "Found additional Amplify sandbox processes: $AMPX_PIDS"
    kill $AMPX_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    AMPX_PIDS=$(ps aux | grep 'ampx sandbox' | grep -v grep | awk '{print $2}')
    if [ -n "$AMPX_PIDS" ]; then
        kill -9 $AMPX_PIDS 2>/dev/null || true
    fi
    print_success "Stopped additional Amplify sandbox processes"
fi

# Kill frontend dev servers
DEV_PIDS=$(ps aux | grep 'npm run dev\|vite' | grep -v grep | awk '{print $2}')
if [ -n "$DEV_PIDS" ]; then
    echo "Found additional dev server processes: $DEV_PIDS"
    kill $DEV_PIDS 2>/dev/null || true
    sleep 2
    # Force kill if still running
    DEV_PIDS=$(ps aux | grep 'npm run dev\|vite' | grep -v grep | awk '{print $2}')
    if [ -n "$DEV_PIDS" ]; then
        kill -9 $DEV_PIDS 2>/dev/null || true
    fi
    print_success "Stopped additional dev server processes"
fi

# Clear data if requested
if [ "$CLEAR_DATA" = true ]; then
    print_step "Clearing sandbox game data from DynamoDB..."

    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        print_warning "AWS CLI not found, skipping data clear"
    else
        # Get AWS region
        AWS_REGION=${AWS_REGION:-"us-east-1"}

        # Get sandbox identifier from environment or use default
        SANDBOX_ID=${AMPLIFY_SANDBOX_ID:-"iolaire"}

        # First, try to get the table name from amplify outputs
        if [ -f "amplify_outputs.json" ]; then
            TABLE_NAME=$(cat amplify_outputs.json | jq -r '.custom.GameSessionTableName' 2>/dev/null || echo "")
        fi

        # If not found in outputs, look for tables with "sandbox" in the name
        if [ -z "$TABLE_NAME" ]; then
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
                print_warning "No GameSession tables found"
            fi
        fi
    fi
fi

echo ""
echo "======================================================"
print_success "All sandbox processes have been stopped!"
echo "======================================================"