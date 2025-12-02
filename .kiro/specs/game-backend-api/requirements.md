# Requirements Document

## Introduction

This document defines the MVP requirements for the backend API system of "West of Haunted House," a modern resurrection of the 1977 text adventure Zork with Halloween-themed transformations. The backend will be deployed as AWS Lambda functions behind AWS Amplify, managing game state, processing player commands, and providing responses to a React frontend.

**Architecture**: AWS Amplify + Lambda (Python) + DynamoDB for session storage
**Deployment**: AWS CLI + Amplify CLI with ZIP file deployment
**Cost Optimization**: Serverless architecture to minimize costs (pay-per-use)

**MVP Scope**: This initial version focuses on core gameplay mechanics:
- ✅ Room navigation with spooky descriptions
- ✅ Object interaction (examine, take, drop, use)
- ✅ Inventory management
- ✅ Sanity system (affects descriptions and gameplay)
- ✅ Basic puzzles (flag-based, like moving rug to reveal trap door)
- ✅ Light system (lamp battery management)
- ✅ Container objects (mailbox, trophy case, etc.)
- ✅ Treasure collection and scoring
- ✅ RESTful API for React frontend

**Deferred to Future Phases**:
- ❌ Combat system
- ❌ NPC AI (thief, enemies)
- ❌ Curse system
- ❌ Blood moon cycles
- ❌ Soul collection
- ❌ Save/load functionality
- ❌ Complex multi-step puzzles
- ❌ Achievements and leaderboards

## Glossary

- **Game Engine**: The Python Lambda functions that process commands and manage game state
- **Lambda Function**: AWS serverless compute service that runs code in response to API requests
- **DynamoDB**: AWS NoSQL database service for storing session state
- **Amplify**: AWS platform for building and deploying full-stack applications
- **Game State**: The complete current condition of the game including room location, inventory, flags, and statistics
- **Command Parser**: The system component that interprets natural language player input into executable game actions
- **Room**: A discrete location in the game world with descriptions, exits, and contained objects
- **Object**: An interactive item, container, or scenery element within the game world
- **Flag**: A boolean or numeric state variable that tracks game progression and conditions
- **Treasure**: A valuable object that must be placed in the trophy case for points
- **NPC**: Non-player character such as the troll, cyclops, or thief
- **Sanity System**: A mental health meter (0-100) that affects gameplay and descriptions
- **Curse Status**: A binary state that applies negative effects when active
- **Blood Moon**: A cyclical 50-turn event that alters game difficulty and availability
- **Soul Collection**: An alternative scoring system rewarding dark content exploration
- **API Endpoint**: A RESTful HTTP interface for frontend-backend communication
- **Session**: A unique game instance with persistent state across multiple requests

## Requirements

### Requirement 1

**User Story:** As a player, I want to start a new game session, so that I can begin my adventure with a fresh game state.

#### Acceptance Criteria

1. WHEN a player requests a new game THEN the Game Engine SHALL create a unique session identifier
2. WHEN a new game is created THEN the Game Engine SHALL initialize all game state variables to their starting values using haunted theme data
3. WHEN a new game is created THEN the Game Engine SHALL place the player in the "west_of_house" room with spooky description
4. WHEN a new game is created THEN the Game Engine SHALL return the session identifier and initial spooky room description to the player
5. WHEN a new game is created THEN the Game Engine SHALL set sanity to 100, score to 0, moves to 0, and lamp_battery to 200

### Requirement 2

**User Story:** As a player, I want to send text commands to the game, so that I can interact with the game world and progress through the adventure.

#### Acceptance Criteria

1. WHEN a player submits a command with a valid session identifier THEN the Game Engine SHALL process the command against the current game state
2. WHEN a command is processed THEN the Command Parser SHALL extract the verb and object references from the natural language input
3. WHEN a command is successfully executed THEN the Game Engine SHALL update the game state accordingly
4. WHEN a command is executed THEN the Game Engine SHALL return a response describing the outcome
5. WHEN a command cannot be understood THEN the Game Engine SHALL return a helpful error message without modifying game state

### Requirement 3

**User Story:** As a player, I want to navigate between rooms using directional commands, so that I can explore the game world.

#### Acceptance Criteria

1. WHEN a player issues a movement command THEN the Game Engine SHALL validate the direction against available exits in the current room
2. WHEN a valid exit exists THEN the Game Engine SHALL move the player to the target room
3. WHEN a player enters a new room THEN the Game Engine SHALL return the spooky room description appropriate to the current sanity level
4. WHEN an exit does not exist THEN the Game Engine SHALL return a message indicating the direction is blocked
5. WHEN an exit is conditional on a flag THEN the Game Engine SHALL check the flag state before allowing passage

### Requirement 4

**User Story:** As a player, I want to interact with objects in the game world, so that I can solve puzzles and collect treasures.

#### Acceptance Criteria

1. WHEN a player examines an object THEN the Game Engine SHALL return the object's spooky description appropriate to the current sanity level
2. WHEN a player takes an object THEN the Game Engine SHALL add the object to the player's inventory and remove it from the room
3. WHEN a player drops an object THEN the Game Engine SHALL remove the object from inventory and place it in the current room
4. WHEN a player uses an object THEN the Game Engine SHALL execute the object's interaction logic and update relevant state
5. WHEN an object interaction has prerequisites THEN the Game Engine SHALL validate conditions before allowing the action

### Requirement 5

**User Story:** As a player, I want the game to track my inventory, so that I can manage the items I'm carrying.

#### Acceptance Criteria

1. WHEN a player requests their inventory THEN the Game Engine SHALL return a list of all carried objects
2. WHEN a player attempts to take an object THEN the Game Engine SHALL verify the object is takeable before adding to inventory
3. WHEN a player drops an object THEN the Game Engine SHALL verify the object is in inventory before removing it
4. WHEN inventory is displayed THEN the Game Engine SHALL include object names and relevant state information
5. WHEN inventory changes THEN the Game Engine SHALL persist the updated state to the session

### Requirement 6

**User Story:** As a player, I want the sanity system to affect my experience, so that the game becomes more challenging and atmospheric as I encounter horrors.

#### Acceptance Criteria

1. WHEN a player enters a cursed room THEN the Game Engine SHALL decrease sanity by the appropriate amount
2. WHEN sanity drops below 75 THEN the Game Engine SHALL begin returning enhanced disturbed spooky descriptions for rooms and objects
3. WHEN sanity drops below 50 THEN the Game Engine SHALL introduce unreliable narrator effects in descriptions
4. WHEN sanity drops below 25 THEN the Game Engine SHALL apply severe effects including potential random teleportation
5. WHEN a player rests in a safe room THEN the Game Engine SHALL increase sanity by 10 per turn

### Requirement 7 (Future Phase)

**User Story:** As a player, I want the curse system to create risk-reward decisions, so that my choices have meaningful consequences.

**Note**: This requirement is deferred to a future release. MVP focuses on the sanity system as the primary Halloween mechanic.

### Requirement 8 (Future Phase)

**User Story:** As a player, I want the blood moon cycle to create dynamic gameplay, so that the game world changes over time.

**Note**: This requirement is deferred to a future release. MVP will have static game world without time-based cycles.

### Requirement 9 (Future Phase)

**User Story:** As a player, I want to collect souls as an alternative progression system, so that I have multiple paths to victory.

**Note**: This requirement is deferred to a future release. MVP focuses on traditional treasure-based scoring.

### Requirement 10 (Future Phase)

**User Story:** As a player, I want to save and load my game progress, so that I can continue my adventure across multiple sessions.

**Note**: This requirement is deferred to a future release. MVP will focus on single-session gameplay.

### Requirement 11

**User Story:** As a frontend developer, I want a RESTful API with clear endpoints, so that I can integrate the game engine with the React interface.

#### Acceptance Criteria

1. WHEN the API receives a request THEN the Game Engine SHALL validate the request format and session identifier
2. WHEN the API processes a request THEN the Game Engine SHALL return responses in consistent JSON format
3. WHEN an error occurs THEN the Game Engine SHALL return appropriate HTTP status codes and error messages
4. WHEN the API is queried THEN the Game Engine SHALL respond within 500 milliseconds for standard commands
5. WHEN multiple requests arrive THEN the Game Engine SHALL handle concurrent sessions without state corruption

### Requirement 12 (Future Phase)

**User Story:** As a player, I want combat encounters with NPCs, so that I can face challenges and obtain rewards.

**Note**: This requirement is deferred to a future release. MVP will focus on exploration and puzzle-solving without combat mechanics.

### Requirement 13

**User Story:** As a player, I want the game to track my score and progress, so that I can measure my success.

#### Acceptance Criteria

1. WHEN a player places a treasure in the trophy case THEN the Game Engine SHALL increase the score by the treasure's value
2. WHEN the score changes THEN the Game Engine SHALL persist the updated score to the session
3. WHEN a player requests game statistics THEN the Game Engine SHALL return score, moves, sanity, souls, and other metrics
4. WHEN the player achieves 350 points THEN the Game Engine SHALL set the won_flag to true
5. WHEN the won_flag is true THEN the Game Engine SHALL unlock the final area and victory condition

### Requirement 14 (Simplified for MVP)

**User Story:** As a player, I want the light system to create tension, so that I must manage resources carefully.

#### Acceptance Criteria

1. WHEN a player enters a dark room without light THEN the Game Engine SHALL return a darkness description
2. WHEN the lamp is on THEN the Game Engine SHALL decrease lamp_battery by 1 each turn
3. WHEN lamp_battery reaches 0 THEN the Game Engine SHALL turn off the lamp automatically

**Note**: Advanced light mechanics (curse effects, action restrictions) are deferred to future releases.

### Requirement 15

**User Story:** As a player, I want container objects to function correctly, so that I can store and organize items.

#### Acceptance Criteria

1. WHEN a player opens a container THEN the Game Engine SHALL set the container's is_open state to true
2. WHEN a player puts an object in a container THEN the Game Engine SHALL verify capacity and add the object to the container
3. WHEN a player takes an object from a container THEN the Game Engine SHALL remove the object from the container and add to inventory
4. WHEN a container is examined THEN the Game Engine SHALL list all contained objects
5. WHEN a container's state changes THEN the Game Engine SHALL persist the updated state to the session

### Requirement 16

**User Story:** As a developer, I want comprehensive error handling, so that the system remains stable and provides helpful feedback.

#### Acceptance Criteria

1. WHEN an invalid session identifier is provided THEN the Game Engine SHALL return a 404 error with a clear message
2. WHEN malformed JSON is received THEN the Game Engine SHALL return a 400 error with validation details
3. WHEN an internal error occurs THEN the Game Engine SHALL log the error and return a 500 error without exposing internals
4. WHEN rate limits are exceeded THEN the Game Engine SHALL return a 429 error with retry information
5. WHEN the system recovers from an error THEN the Game Engine SHALL maintain game state consistency

### Requirement 17 (Future Phase)

**User Story:** As a player, I want the thief NPC to create dynamic challenges, so that treasure collection is more engaging.

**Note**: This requirement is deferred to a future release. MVP will not include NPC AI or theft mechanics.

### Requirement 18 (Simplified for MVP)

**User Story:** As a player, I want basic puzzle mechanics to function correctly, so that I can solve simple challenges and progress.

#### Acceptance Criteria

1. WHEN a player completes a simple puzzle action THEN the Game Engine SHALL verify prerequisites are met
2. WHEN puzzle prerequisites are satisfied THEN the Game Engine SHALL update relevant flags
3. WHEN a puzzle is solved THEN the Game Engine SHALL provide feedback

**Note**: Complex multi-step puzzles and hint systems are deferred to future releases. MVP includes only simple flag-based puzzles (e.g., move rug to reveal trap door, open window to enter house).

### Requirement 19

**User Story:** As a frontend developer, I want real-time game state updates, so that the UI can reflect changes immediately.

#### Acceptance Criteria

1. WHEN game state changes THEN the Game Engine SHALL include updated state in the API response
2. WHEN the API response is sent THEN the Game Engine SHALL include current room, inventory, flags, and statistics
3. WHEN the frontend requests full state THEN the Game Engine SHALL return the complete serialized game state
4. WHEN state updates are sent THEN the Game Engine SHALL use consistent field names and data types
5. WHEN the response is formatted THEN the Game Engine SHALL use spooky descriptions as the primary content with original descriptions available for reference only

### Requirement 20

**User Story:** As a player, I want the game to use haunted Halloween-themed content, so that I experience the spooky resurrection of Zork.

#### Acceptance Criteria

1. WHEN any room description is displayed THEN the Game Engine SHALL use the description_spooky field from the room data
2. WHEN any object description is displayed THEN the Game Engine SHALL use the response_spooky field from the object interactions
3. WHEN any object name is displayed THEN the Game Engine SHALL use the haunted name variant where available
4. WHEN the game initializes THEN the Game Engine SHALL load haunted theme JSON files for rooms, objects, and flags
5. WHEN original Zork content is referenced THEN the Game Engine SHALL transform it to the haunted equivalent

### Requirement 21

**User Story:** As a developer, I want proper IAM roles and permissions configured, so that the application follows AWS security best practices.

#### Acceptance Criteria

1. WHEN the backend is deployed THEN the Game Engine SHALL create a dedicated IAM role for Lambda execution
2. WHEN Lambda accesses DynamoDB THEN the Game Engine SHALL use least-privilege IAM policies (only required DynamoDB actions)
3. WHEN IAM policies are created THEN the Game Engine SHALL scope permissions to specific resources (table ARNs, not *)
4. WHEN the application runs THEN the Game Engine SHALL use IAM roles for authentication (no hardcoded credentials)
5. WHEN Amplify deploys resources THEN the Game Engine SHALL create separate IAM roles for each service (Lambda, API Gateway)
6. WHEN deploying via scripts THEN the Game Engine SHALL use a dedicated IAM user or role with deployment permissions (Amplify, Lambda, DynamoDB, IAM, CloudFormation)
7. WHEN deployment IAM policies are created THEN the Game Engine SHALL document required permissions for CI/CD or manual deployment

### Requirement 22

**User Story:** As a developer, I want the backend deployed on AWS Lambda with Amplify, so that costs are minimized and deployment is simple.

#### Acceptance Criteria

1. WHEN the backend is deployed THEN the Game Engine SHALL run as AWS Lambda functions
2. WHEN Lambda functions are invoked THEN the Game Engine SHALL respond within Lambda timeout limits (30 seconds)
3. WHEN session data is stored THEN the Game Engine SHALL use DynamoDB with on-demand billing
4. WHEN the application is deployed THEN the Game Engine SHALL use Amplify CLI for deployment automation
5. WHEN estimating costs THEN the Game Engine SHALL target under $5/month for typical usage (1000 games/month)

### Requirement 23

**User Story:** As a system administrator, I want session management and cleanup, so that server resources are used efficiently.

#### Acceptance Criteria

1. WHEN a session is created THEN the Game Engine SHALL assign a unique identifier and set an expiration time
2. WHEN a session expires THEN the Game Engine SHALL remove the session data from memory
3. WHEN a session is accessed THEN the Game Engine SHALL update the last accessed timestamp
4. WHEN session cleanup runs THEN the Game Engine SHALL remove all expired sessions
5. WHEN session limits are reached THEN the Game Engine SHALL reject new session creation with an appropriate error

### Requirement 24

**User Story:** As a developer, I want all AWS resources properly tagged, so that I can track costs, manage resources, and maintain organization.

#### Acceptance Criteria

1. WHEN any AWS resource is created THEN the Game Engine SHALL apply the tag "Project" with value "west-of-haunted-house"
2. WHEN any AWS resource is created THEN the Game Engine SHALL apply the tag "ManagedBy" with value "vedfolnir"
3. WHEN any AWS resource is created THEN the Game Engine SHALL apply the tag "Environment" with a user-defined value
4. WHEN deployment scripts create resources THEN the Game Engine SHALL ensure all resources receive the required tags
5. WHEN querying AWS resources THEN the Game Engine SHALL filter by the required tags to identify project resources

### Requirement 25

**User Story:** As a developer, I want a cleanup script to remove all AWS resources, so that I can reset the project to a clean slate or decommission the application.

#### Acceptance Criteria

1. WHEN the cleanup script is executed THEN the Game Engine SHALL identify all AWS resources with the project tags
2. WHEN resources are identified THEN the Game Engine SHALL delete resources in the correct dependency order
3. WHEN the cleanup script runs THEN the Game Engine SHALL only delete resources matching all three required tags
4. WHEN resources are deleted THEN the Game Engine SHALL provide progress feedback and confirmation
5. WHEN cleanup completes THEN the Game Engine SHALL verify all tagged resources have been removed
