#!/bin/bash

# Bundle game data JSON files into Lambda deployment
# This script copies haunted theme JSON files to the Lambda data directory

set -e  # Exit on error

echo "=========================================="
echo "Bundling Game Data Files"
echo "=========================================="

# Configuration
SOURCE_DATA_DIR="west_of_house_json"
LAMBDA_DATA_DIR="amplify/backend/function/gameHandler/src/data"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if source data directory exists
if [ ! -d "$SOURCE_DATA_DIR" ]; then
    echo -e "${RED}Error: Source data directory not found: $SOURCE_DATA_DIR${NC}"
    exit 1
fi

# Create Lambda data directory if it doesn't exist
echo -e "${YELLOW}Creating Lambda data directory...${NC}"
mkdir -p "$LAMBDA_DATA_DIR"

# Copy JSON files
echo -e "${YELLOW}Copying haunted theme JSON files...${NC}"

FILES_COPIED=0

# Copy rooms JSON
if [ -f "$SOURCE_DATA_DIR/west_of_house_rooms_haunted.json" ]; then
    cp "$SOURCE_DATA_DIR/west_of_house_rooms_haunted.json" "$LAMBDA_DATA_DIR/rooms_haunted.json"
    echo -e "${GREEN}✓ Copied rooms_haunted.json${NC}"
    FILES_COPIED=$((FILES_COPIED + 1))
else
    echo -e "${RED}Warning: rooms_haunted.json not found${NC}"
fi

# Copy objects JSON
if [ -f "$SOURCE_DATA_DIR/west_of_house_objects_haunted.json" ]; then
    cp "$SOURCE_DATA_DIR/west_of_house_objects_haunted.json" "$LAMBDA_DATA_DIR/objects_haunted.json"
    echo -e "${GREEN}✓ Copied objects_haunted.json${NC}"
    FILES_COPIED=$((FILES_COPIED + 1))
else
    echo -e "${RED}Warning: objects_haunted.json not found${NC}"
fi

# Copy flags JSON
if [ -f "$SOURCE_DATA_DIR/west_of_house_flags_haunted.json" ]; then
    cp "$SOURCE_DATA_DIR/west_of_house_flags_haunted.json" "$LAMBDA_DATA_DIR/flags_haunted.json"
    echo -e "${GREEN}✓ Copied flags_haunted.json${NC}"
    FILES_COPIED=$((FILES_COPIED + 1))
else
    echo -e "${RED}Warning: flags_haunted.json not found${NC}"
fi

# Verify files were copied
if [ $FILES_COPIED -eq 0 ]; then
    echo -e "${RED}Error: No JSON files were copied${NC}"
    exit 1
fi

# Display file sizes
echo ""
echo -e "${YELLOW}Game data files:${NC}"
for file in "$LAMBDA_DATA_DIR"/*.json; do
    if [ -f "$file" ]; then
        SIZE=$(du -h "$file" | cut -f1)
        BASENAME=$(basename "$file")
        echo "  - $BASENAME ($SIZE)"
    fi
done

echo ""
echo -e "${GREEN}=========================================="
echo "Game data bundling complete!"
echo "==========================================${NC}"
echo "Files copied: $FILES_COPIED"
echo "Target directory: $LAMBDA_DATA_DIR"
echo ""
echo "Next steps:"
echo "  1. Run ./scripts/package-lambda.sh to create deployment package"
echo "  2. Run ./scripts/deploy.sh to deploy to AWS"
