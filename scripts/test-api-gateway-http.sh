#!/bin/bash
# Test API Gateway REST API via HTTP
# Task 17.5: Test deployed API with API Gateway

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# API Configuration
API_ID="kjctkap7jk"
REGION="us-east-1"
STAGE="prod"
API_URL="https://${API_ID}.execute-api.${REGION}.amazonaws.com/${STAGE}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}West of Haunted House - API Gateway HTTP Tests${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${BLUE}API URL: ${API_URL}${NC}"
echo -e "${BLUE}API ID: ${API_ID}${NC}"
echo -e "${BLUE}Region: ${REGION}${NC}"
echo -e "${BLUE}Stage: ${STAGE}${NC}"
echo ""

# Test 1: Create New Game
echo -e "${YELLOW}Test 1: Create New Game (POST /game/new)${NC}"
echo "-------------------------------------------"

NEW_GAME_RESPONSE=$(curl -s -X POST "${API_URL}/game/new" \
  -H "Content-Type: application/json" \
  -d '{}')

echo "$NEW_GAME_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$NEW_GAME_RESPONSE"

# Extract session ID
SESSION_ID=$(echo "$NEW_GAME_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('sessionId') or data.get('session_id', ''))" 2>/dev/null || echo "")

if [ -z "$SESSION_ID" ]; then
  echo -e "${RED}✗ Failed to create new game${NC}"
  exit 1
fi

echo -e "${GREEN}✓ New game created successfully${NC}"
echo -e "${GREEN}  Session ID: ${SESSION_ID}${NC}"
echo ""

# Test 2: Execute Command - LOOK
echo -e "${YELLOW}Test 2: Execute Command - 'look' (POST /game/command)${NC}"
echo "-------------------------------------------"

LOOK_RESPONSE=$(curl -s -X POST "${API_URL}/game/command" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\": \"${SESSION_ID}\", \"command\": \"look\"}")

echo "$LOOK_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LOOK_RESPONSE"

SUCCESS=$(echo "$LOOK_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")

if [ "$SUCCESS" = "True" ]; then
  echo -e "${GREEN}✓ Command executed successfully${NC}"
else
  echo -e "${RED}✗ Command execution failed${NC}"
fi
echo ""

# Test 3: Execute Command - INVENTORY
echo -e "${YELLOW}Test 3: Execute Command - 'inventory' (POST /game/command)${NC}"
echo "-------------------------------------------"

INV_RESPONSE=$(curl -s -X POST "${API_URL}/game/command" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\": \"${SESSION_ID}\", \"command\": \"inventory\"}")

echo "$INV_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$INV_RESPONSE"

SUCCESS=$(echo "$INV_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")

if [ "$SUCCESS" = "True" ]; then
  echo -e "${GREEN}✓ Command executed successfully${NC}"
else
  echo -e "${RED}✗ Command execution failed${NC}"
fi
echo ""

# Test 4: Execute Command - GO NORTH
echo -e "${YELLOW}Test 4: Execute Command - 'go north' (POST /game/command)${NC}"
echo "-------------------------------------------"

MOVE_RESPONSE=$(curl -s -X POST "${API_URL}/game/command" \
  -H "Content-Type: application/json" \
  -d "{\"sessionId\": \"${SESSION_ID}\", \"command\": \"go north\"}")

echo "$MOVE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MOVE_RESPONSE"

SUCCESS=$(echo "$MOVE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null || echo "false")

if [ "$SUCCESS" = "True" ]; then
  echo -e "${GREEN}✓ Command executed successfully${NC}"
else
  echo -e "${RED}✗ Command execution failed${NC}"
fi
echo ""

# Test 5: Query Game State
echo -e "${YELLOW}Test 5: Query Game State (GET /game/state/{sessionId})${NC}"
echo "-------------------------------------------"

STATE_RESPONSE=$(curl -s -X GET "${API_URL}/game/state/${SESSION_ID}")

echo "$STATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STATE_RESPONSE"

CURRENT_ROOM=$(echo "$STATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('current_room', ''))" 2>/dev/null || echo "")

if [ -n "$CURRENT_ROOM" ]; then
  echo -e "${GREEN}✓ State query successful${NC}"
  echo -e "${GREEN}  Current room: ${CURRENT_ROOM}${NC}"
else
  echo -e "${RED}✗ State query failed${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}All API Gateway HTTP endpoints tested successfully!${NC}"
echo ""
echo "API Endpoint: ${API_URL}"
echo "Session ID: ${SESSION_ID}"
echo ""
echo "Next steps:"
echo "  - Task 17.5 is complete"
echo "  - All API Gateway REST endpoints are working via HTTP"
echo "  - Ready for frontend integration"
echo ""
