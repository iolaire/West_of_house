#!/bin/bash

# Package Lambda function with dependencies
# This script creates a deployment package for the AWS Lambda function

set -e  # Exit on error

echo "=========================================="
echo "Packaging Lambda Function"
echo "=========================================="

# Configuration
LAMBDA_SRC_DIR="amplify/backend/function/gameHandler/src"
BUILD_DIR="build/lambda"
PACKAGE_NAME="lambda-deployment-package.zip"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if source directory exists
if [ ! -d "$LAMBDA_SRC_DIR" ]; then
    echo -e "${RED}Error: Lambda source directory not found: $LAMBDA_SRC_DIR${NC}"
    exit 1
fi

# Create build directory
echo -e "${YELLOW}Creating build directory...${NC}"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# Copy Lambda source code
echo -e "${YELLOW}Copying Lambda source code...${NC}"
cp -r "$LAMBDA_SRC_DIR"/*.py "$BUILD_DIR/"

# Check if requirements.txt exists
if [ -f "$LAMBDA_SRC_DIR/requirements.txt" ]; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    
    # Try to find pip or pip3
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    elif command -v python3 -m pip &> /dev/null; then
        PIP_CMD="python3 -m pip"
    elif command -v python -m pip &> /dev/null; then
        PIP_CMD="python -m pip"
    else
        echo -e "${RED}Error: pip not found. Please install Python and pip.${NC}"
        exit 1
    fi
    
    $PIP_CMD install -r "$LAMBDA_SRC_DIR/requirements.txt" -t "$BUILD_DIR" --quiet
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dependencies installed successfully${NC}"
    else
        echo -e "${RED}Error: Failed to install dependencies${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}No requirements.txt found, skipping dependency installation${NC}"
fi

# Copy data directory if it exists
if [ -d "$LAMBDA_SRC_DIR/data" ]; then
    echo -e "${YELLOW}Copying game data files...${NC}"
    cp -r "$LAMBDA_SRC_DIR/data" "$BUILD_DIR/"
    echo -e "${GREEN}✓ Game data files copied${NC}"
else
    echo -e "${YELLOW}No data directory found, skipping data copy${NC}"
fi

# Create ZIP package
echo -e "${YELLOW}Creating deployment package...${NC}"
cd "$BUILD_DIR"
zip -r "../../$PACKAGE_NAME" . -q

if [ $? -eq 0 ]; then
    cd ../..
    PACKAGE_SIZE=$(du -h "$PACKAGE_NAME" | cut -f1)
    echo -e "${GREEN}✓ Deployment package created: $PACKAGE_NAME ($PACKAGE_SIZE)${NC}"
    
    # Check package size (Lambda limit is 50MB for direct upload, 250MB unzipped)
    PACKAGE_SIZE_BYTES=$(stat -f%z "$PACKAGE_NAME" 2>/dev/null || stat -c%s "$PACKAGE_NAME" 2>/dev/null)
    if [ $PACKAGE_SIZE_BYTES -gt 52428800 ]; then
        echo -e "${RED}Warning: Package size exceeds 50MB. You may need to use S3 for deployment.${NC}"
    fi
else
    echo -e "${RED}Error: Failed to create deployment package${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================="
echo "Lambda packaging complete!"
echo "==========================================${NC}"
echo "Package location: $PACKAGE_NAME"
echo "Next steps:"
echo "  1. Run ./scripts/bundle-game-data.sh to bundle game data"
echo "  2. Run ./scripts/deploy.sh to deploy to AWS"
