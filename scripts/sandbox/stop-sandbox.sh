#!/bin/bash

# Stop Sandbox Script for West of Haunted House
# This script will stop the sandbox environment

set -e

# Change to the project root directory
cd "$(dirname "$0")/.."

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

echo ""
echo "======================================================"
print_success "All sandbox processes have been stopped!"
echo "======================================================"