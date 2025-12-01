# Project Structure

## Root Organization

```
west-of-haunted-house/
├── documents/          # Project documentation and mechanics
├── reference/          # Original Zork source code and extracted JSON
├── west_of_house_json/ # Haunted theme JSON data (MVP subset)
├── src/                # Backend source code (to be created)
├── tests/              # All test files (to be created)
├── scripts/            # Deployment and utility scripts (to be created)
├── amplify/            # AWS Amplify configuration (generated)
└── .kiro/              # Kiro specs and steering rules
```

## Documentation (`documents/`)

- `HALLOWEEN_MECHANICS.md`: Detailed Halloween flag system (sanity, curse, blood moon, souls)
- `FLAG_TRANSFORMATIONS.md`: Mapping of original Zork flags to haunted equivalents
- `HAUNTED_TRANSFORMATION.md`: Transformation guidelines (if exists)

## Reference Data (`reference/`)

- `zork1-master/`: Original Zork I source code in ZIL (Zork Implementation Language)
- `json/`: Extracted JSON from original source (rooms, objects, flags)

## Game Data (`west_of_house_json/`)

MVP subset of haunted theme data:
- `west_of_house_rooms_haunted.json`: Room definitions with spooky descriptions
- `west_of_house_objects_haunted.json`: Object definitions with haunted interactions
- `west_of_house_flags_haunted.json`: Initial flag states

**JSON Structure Convention**:
- Rooms: `description_original` + `description_spooky`
- Objects: `response_original` + `response_spooky`
- Always use spooky variants in gameplay

## Backend Source (`src/` - to be created)

```
src/
└── lambda/
    └── game_handler/
        ├── index.py              # Lambda entry point
        ├── game_engine.py        # Core game logic
        ├── command_parser.py     # Natural language parsing
        ├── state_manager.py      # Game state management
        ├── sanity_system.py      # Halloween sanity mechanics
        ├── world_loader.py       # Load JSON game data
        ├── requirements.txt      # Python dependencies
        └── data/                 # Bundled game data
            ├── rooms_haunted.json
            ├── objects_haunted.json
            └── flags_haunted.json
```

## Testing (`tests/` - to be created)

```
tests/
├── unit/                         # Unit tests for individual components
│   ├── test_command_parser.py
│   ├── test_state_manager.py
│   ├── test_sanity_system.py
│   └── test_world_loader.py
├── property/                     # Property-based tests (Hypothesis)
│   ├── test_properties_core.py
│   ├── test_properties_sanity.py
│   └── test_properties_state.py
└── integration/                  # End-to-end tests
    ├── test_game_flow.py
    └── test_api_endpoints.py
```

## Kiro Specs (`.kiro/specs/`)

- `game-backend-api/requirements.md`: User stories and acceptance criteria
- `game-backend-api/design.md`: Architecture, components, correctness properties
- `game-backend-api/tasks.md`: Implementation tasks (if exists)

## Kiro Steering (`.kiro/steering/`)

- `product.md`: Product overview and scope
- `tech.md`: Technology stack and commands
- `structure.md`: This file

## AWS Amplify (Generated)

```
amplify/
├── backend/
│   ├── api/
│   │   └── gameAPI/              # REST API configuration
│   ├── function/
│   │   └── gameHandler/          # Lambda function
│   └── storage/
│       └── GameSessions/         # DynamoDB table
└── team-provider-info.json       # Environment configuration
```

## Key Conventions

- **Python Files**: Snake_case naming (e.g., `game_engine.py`)
- **JSON Files**: Lowercase with underscores (e.g., `rooms_haunted.json`)
- **Test Files**: Prefix with `test_` (e.g., `test_command_parser.py`)
- **Lambda Package**: All dependencies bundled in ZIP with data files
- **Session Storage**: DynamoDB with TTL for automatic cleanup
- **Spooky First**: Always use haunted theme descriptions in gameplay
