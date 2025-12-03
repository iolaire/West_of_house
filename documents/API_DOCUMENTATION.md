# API Documentation

## Overview

The West of Haunted House backend provides a RESTful JSON API for managing game sessions and processing player commands. All endpoints return JSON responses and use standard HTTP status codes.

## Base URL

```
Production: https://your-api-id.execute-api.us-east-1.amazonaws.com/prod
Sandbox: http://localhost:3000 (when running npx ampx sandbox)
```

## Authentication

Currently, no authentication is required. Sessions are identified by unique session IDs returned when creating a new game.

## Rate Limiting

- **Per Session**: 60 requests per minute
- **Per IP**: 100 requests per minute
- **Response Header**: `X-RateLimit-Remaining` indicates remaining requests

When rate limit is exceeded:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests. Please try again later.",
    "retry_after": 60
  }
}
```

## Common Response Fields

All successful responses include:
- `success`: Boolean indicating if the request succeeded
- `message`: Human-readable description of the result (for command endpoint)
- `room`: Current room ID
- `description`: Spooky description of the current location
- `exits`: Array of available directions
- `items_visible`: Array of objects visible in the current room
- `inventory`: Array of objects in player's inventory
- `state`: Object containing game statistics

## Error Handling

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional context about the error"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 400 | Bad Request | Malformed JSON or invalid command syntax |
| 404 | Not Found | Session ID not found or expired |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Unexpected server error |
| 503 | Service Unavailable | System maintenance or overload |

### Common Error Codes

- `INVALID_SESSION`: Session ID not found or expired
- `INVALID_COMMAND`: Command could not be parsed
- `INVALID_ACTION`: Action not allowed in current state
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Unexpected server error

---

## Endpoints

### 1. Create New Game

Creates a new game session with a unique session ID and initializes the game state.

**Endpoint**: `POST /game/new`

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{}
```

**Success Response** (200 OK):
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

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string (UUID) | Unique identifier for this game session |
| `room` | string | ID of the starting room (always "west_of_house") |
| `description` | string | Spooky description of the starting location |
| `exits` | array[string] | Available directions to move |
| `items_visible` | array[string] | Objects visible in the room |
| `inventory` | array[string] | Objects in player's inventory (empty at start) |
| `state.sanity` | integer | Mental health meter (0-100, starts at 100) |
| `state.score` | integer | Current score (starts at 0) |
| `state.moves` | integer | Number of turns taken (starts at 0) |
| `state.lamp_battery` | integer | Lamp battery remaining (starts at 200) |

**Example Request**:
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/new \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Example Response**:
```json
{
  "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "room": "west_of_house",
  "description": "You stand before a decrepit Victorian mansion...",
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

**Notes**:
- Session IDs are cryptographically secure UUIDs
- Sessions expire after 1 hour of inactivity (TTL)
- All new games start at "west_of_house" with sanity at 100
- Save the `session_id` to continue playing

---

### 2. Execute Command

Processes a player command and returns the result with updated game state.

**Endpoint**: `POST /game/command`

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "command": "go north"
}
```

**Request Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string (UUID) | Yes | Session ID from `/game/new` |
| `command` | string | Yes | Natural language command (max 500 chars) |

**Success Response** (200 OK):
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

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the command succeeded |
| `message` | string | Description of what happened |
| `room` | string | Current room ID after command |
| `description` | string | Spooky description of current location |
| `exits` | array[string] | Available directions to move |
| `items_visible` | array[string] | Objects visible in the room |
| `inventory` | array[string] | Objects in player's inventory |
| `state` | object | Current game statistics |
| `notifications` | array[string] | Special messages (sanity loss, achievements, etc.) |

**Supported Commands**:

#### Movement Commands
```
go north          # Move north
north             # Short form
n                 # Abbreviation
go south / south / s
go east / east / e
go west / west / w
go up / up / u
go down / down / d
go in / in
go out / out
```

#### Object Interaction Commands
```
take lamp         # Pick up an object
get lamp          # Synonym for take
drop lamp         # Drop an object
examine mailbox   # Look at an object closely
x mailbox         # Short form
look at mailbox   # Alternative form
open mailbox      # Open a container
close mailbox     # Close a container
read leaflet      # Read text on an object
move rug          # Move an object (reveals trap door)
```

#### Utility Commands
```
inventory         # Show what you're carrying
i                 # Short form
look              # Look around current room
l                 # Short form
quit              # End the game
```

**Example Requests**:

**Movement**:
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/command \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "command": "go north"
  }'
```

**Taking an Object**:
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/command \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "command": "take lamp"
  }'
```

**Examining an Object**:
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/command \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "command": "examine mailbox"
  }'
```

**Error Response** (404 Not Found):
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

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "INVALID_COMMAND",
    "message": "I don't understand that command.",
    "details": "Command could not be parsed: 'xyzzy123'"
  }
}
```

**Notes**:
- Commands are case-insensitive
- The parser handles synonyms (e.g., "get" = "take")
- Invalid commands return helpful error messages
- State is automatically saved after each command
- The `moves` counter increments with each command

---

### 3. Get Game State

Retrieves the complete current game state for a session.

**Endpoint**: `GET /game/state/{session_id}`

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string (UUID) | Yes | Session ID from `/game/new` |

**Request Headers**:
```
Content-Type: application/json
```

**Success Response** (200 OK):
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "current_room": "west_of_house",
  "inventory": ["lamp", "sword"],
  "flags": {
    "rug_moved": true,
    "trap_door_open": false,
    "grate_unlocked": false,
    "kitchen_window_open": false,
    "mailbox_open": true,
    "lamp_on": false
  },
  "state": {
    "sanity": 95,
    "score": 0,
    "moves": 5,
    "lamp_battery": 195
  },
  "rooms_visited": ["west_of_house", "north_of_house", "behind_house"],
  "turn_count": 5
}
```

**Response Fields**:

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string (UUID) | Session identifier |
| `current_room` | string | ID of the room player is currently in |
| `inventory` | array[string] | Objects in player's inventory |
| `flags` | object | Game flags tracking puzzle progress |
| `state.sanity` | integer | Mental health meter (0-100) |
| `state.score` | integer | Current score |
| `state.moves` | integer | Number of turns taken |
| `state.lamp_battery` | integer | Lamp battery remaining |
| `rooms_visited` | array[string] | List of rooms player has visited |
| `turn_count` | integer | Total number of turns |

**Example Request**:
```bash
curl -X GET https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/state/a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  -H "Content-Type: application/json"
```

**Error Response** (404 Not Found):
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

**Notes**:
- Use this endpoint to restore game state in the UI
- Useful for debugging and state inspection
- Sessions expire after 1 hour of inactivity
- All game flags are included for puzzle tracking

---

## Game Mechanics

### Sanity System

The sanity meter (0-100) affects gameplay and descriptions:

| Sanity Range | Effect | Description Variant |
|--------------|--------|---------------------|
| 100-75 | Normal | Standard spooky descriptions |
| 74-50 | Disturbed | Enhanced disturbed descriptions |
| 49-25 | Unreliable | Unreliable narrator effects |
| 24-0 | Severe | Garbled/broken descriptions, random teleportation |

**Sanity Loss Triggers**:
- Entering cursed rooms: -5 to -15 sanity
- Encountering supernatural events: -10 sanity
- Reading cursed texts: -5 sanity

**Sanity Gain**:
- Resting in safe rooms: +10 sanity per turn
- Maximum sanity: 100 (cannot exceed)

### Lamp Battery

- Starts at 200 turns
- Decreases by 1 per turn when lamp is on
- Automatically turns off at 0 battery
- Dark rooms require light to see

### Scoring

- Treasures must be placed in trophy case to score
- Each treasure has a specific point value
- Maximum score: 350 points
- Winning condition: Reach 350 points

### Puzzles

**Simple Flag-Based Puzzles**:
- Move rug to reveal trap door
- Open trap door to access cellar
- Open kitchen window to enter house
- Move leaves to reveal grating
- Unlock grating with keys

---

## Integration Examples

### JavaScript/TypeScript

```typescript
// Create new game
async function createNewGame(): Promise<string> {
  const response = await fetch('https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/new', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({}),
  });
  
  const data = await response.json();
  return data.session_id;
}

// Execute command
async function executeCommand(sessionId: string, command: string) {
  const response = await fetch('https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/command', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      session_id: sessionId,
      command: command,
    }),
  });
  
  return await response.json();
}

// Get game state
async function getGameState(sessionId: string) {
  const response = await fetch(`https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/state/${sessionId}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  
  return await response.json();
}
```

### Python

```python
import requests
import json

BASE_URL = "https://your-api-id.execute-api.us-east-1.amazonaws.com/prod"

def create_new_game():
    """Create a new game session."""
    response = requests.post(f"{BASE_URL}/game/new", json={})
    return response.json()

def execute_command(session_id, command):
    """Execute a game command."""
    response = requests.post(
        f"{BASE_URL}/game/command",
        json={"session_id": session_id, "command": command}
    )
    return response.json()

def get_game_state(session_id):
    """Get current game state."""
    response = requests.get(f"{BASE_URL}/game/state/{session_id}")
    return response.json()

# Example usage
game = create_new_game()
session_id = game["session_id"]
print(f"Started new game: {session_id}")
print(game["description"])

# Play the game
result = execute_command(session_id, "go north")
print(result["message"])

result = execute_command(session_id, "take lamp")
print(result["message"])

# Check state
state = get_game_state(session_id)
print(f"Inventory: {state['inventory']}")
print(f"Sanity: {state['state']['sanity']}")
```

### cURL Examples

```bash
# Create new game
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/new \
  -H "Content-Type: application/json" \
  -d '{}'

# Execute command
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/command \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "command": "go north"
  }'

# Get game state
curl -X GET https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/state/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json"
```

---

## Testing the API

### Using the Test Script

```bash
# Test deployed production API
./scripts/test-production-api.sh

# Test local sandbox
./scripts/test-sandbox-endpoints.py
```

### Manual Testing

1. **Create a new game**:
```bash
SESSION_ID=$(curl -s -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/new | jq -r '.session_id')
echo "Session ID: $SESSION_ID"
```

2. **Execute commands**:
```bash
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/command \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"$SESSION_ID\", \"command\": \"go north\"}" | jq
```

3. **Check state**:
```bash
curl -X GET https://your-api-id.execute-api.us-east-1.amazonaws.com/prod/game/state/$SESSION_ID | jq
```

---

## Troubleshooting

### Common Issues

**Issue**: "Session not found or expired"
- **Cause**: Session ID is invalid or session expired (1 hour TTL)
- **Solution**: Create a new game session

**Issue**: "I don't understand that command"
- **Cause**: Command syntax not recognized
- **Solution**: Check supported commands list, use simpler phrasing

**Issue**: "Rate limit exceeded"
- **Cause**: Too many requests in short time
- **Solution**: Wait 60 seconds and retry

**Issue**: "Internal server error"
- **Cause**: Unexpected backend error
- **Solution**: Check CloudWatch Logs, retry request

### Debugging

Enable verbose logging:
```bash
# Set log level in Lambda environment variables
LOG_LEVEL=DEBUG
```

Check CloudWatch Logs:
```bash
aws logs tail /aws/lambda/gameHandler --follow
```

---

## API Versioning

Current version: **v1**

Future versions will be accessible via path prefix:
- v1: `/game/new` (current)
- v2: `/v2/game/new` (future)

Breaking changes will be introduced in new versions only.

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/west-of-haunted-house/issues)
- **Documentation**: See `documents/` folder
- **API Status**: Check AWS Amplify Console

---

**Last Updated**: December 2, 2025
