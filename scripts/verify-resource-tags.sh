#!/bin/bash

# Script to verify AWS resource tags for West of Haunted House project
# This script checks that all resources have the required tags:
# - Project: west-of-haunted-house
# - ManagedBy: vedfolnir
# - Environment: <env>

set -e

echo "=========================================="
echo "AWS Resource Tag Verification"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Required tags
REQUIRED_TAGS=("Project" "ManagedBy" "Environment")
PROJECT_VALUE="west-of-haunted-house"
MANAGED_BY_VALUE="vedfolnir"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if AWS CLI is installed
if ! command_exists aws; then
    echo -e "${RED}Error: AWS CLI is not installed${NC}"
    exit 1
fi

# Check if jq is installed (for JSON parsing)
if ! command_exists jq; then
    echo -e "${YELLOW}Warning: jq is not installed. Install it for better output formatting.${NC}"
    echo "On macOS: brew install jq"
    echo ""
fi

echo "Querying all resources with Project tag..."
echo ""

# Get all resources with the Project tag
RESOURCES=$(aws resourcegroupstaggingapi get-resources \
    --tag-filters Key=Project,Values=$PROJECT_VALUE \
    --output json 2>/dev/null || echo '{"ResourceTagMappingList":[]}')

# Count resources
RESOURCE_COUNT=$(echo "$RESOURCES" | jq '.ResourceTagMappingList | length' 2>/dev/null || echo "0")

if [ "$RESOURCE_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}No resources found with Project tag: $PROJECT_VALUE${NC}"
    echo "This is expected if you haven't deployed yet."
    echo ""
    echo "To deploy, run: amplify push"
    exit 0
fi

echo -e "${GREEN}Found $RESOURCE_COUNT resources${NC}"
echo ""

# Check each resource for required tags
MISSING_TAGS=0
CORRECT_TAGS=0

echo "$RESOURCES" | jq -r '.ResourceTagMappingList[] | @json' | while read -r resource; do
    ARN=$(echo "$resource" | jq -r '.ResourceARN')
    RESOURCE_TYPE=$(echo "$ARN" | cut -d':' -f3)
    RESOURCE_NAME=$(echo "$ARN" | rev | cut -d'/' -f1 | rev)
    
    echo "Checking: $RESOURCE_TYPE - $RESOURCE_NAME"
    
    # Get tags for this resource
    TAGS=$(echo "$resource" | jq -r '.Tags')
    
    # Check each required tag
    HAS_ALL_TAGS=true
    for TAG_KEY in "${REQUIRED_TAGS[@]}"; do
        TAG_VALUE=$(echo "$TAGS" | jq -r ".[] | select(.Key==\"$TAG_KEY\") | .Value" 2>/dev/null)
        
        if [ -z "$TAG_VALUE" ] || [ "$TAG_VALUE" == "null" ]; then
            echo -e "  ${RED}✗ Missing tag: $TAG_KEY${NC}"
            HAS_ALL_TAGS=false
        else
            # Validate specific tag values
            if [ "$TAG_KEY" == "Project" ] && [ "$TAG_VALUE" != "$PROJECT_VALUE" ]; then
                echo -e "  ${RED}✗ Incorrect Project tag: $TAG_VALUE (expected: $PROJECT_VALUE)${NC}"
                HAS_ALL_TAGS=false
            elif [ "$TAG_KEY" == "ManagedBy" ] && [ "$TAG_VALUE" != "$MANAGED_BY_VALUE" ]; then
                echo -e "  ${RED}✗ Incorrect ManagedBy tag: $TAG_VALUE (expected: $MANAGED_BY_VALUE)${NC}"
                HAS_ALL_TAGS=false
            else
                echo -e "  ${GREEN}✓ $TAG_KEY: $TAG_VALUE${NC}"
            fi
        fi
    done
    
    if [ "$HAS_ALL_TAGS" = true ]; then
        CORRECT_TAGS=$((CORRECT_TAGS + 1))
    else
        MISSING_TAGS=$((MISSING_TAGS + 1))
    fi
    
    echo ""
done

echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Total resources: $RESOURCE_COUNT"
echo -e "${GREEN}Resources with all tags: $CORRECT_TAGS${NC}"
if [ "$MISSING_TAGS" -gt 0 ]; then
    echo -e "${RED}Resources with missing/incorrect tags: $MISSING_TAGS${NC}"
fi
echo ""

if [ "$MISSING_TAGS" -gt 0 ]; then
    echo -e "${YELLOW}Action required:${NC}"
    echo "Some resources are missing required tags."
    echo "Redeploy with: amplify push"
    exit 1
else
    echo -e "${GREEN}All resources are properly tagged!${NC}"
    exit 0
fi
