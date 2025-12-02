# Implementation Plan

## Overview

This implementation plan breaks down the MVP backend development into discrete, manageable tasks. Each task builds incrementally on previous work, focusing on core functionality first before adding complexity. The plan follows AWS serverless architecture with Lambda + DynamoDB + Amplify.

**Key Principles:**
- Implement core features before advanced mechanics
- Test as we build (unit tests alongside implementation)
- Deploy early and iterate
- Keep costs minimal (<$5/month target)

---

## Tasks

- [ ] 1. Project setup and AWS infrastructure
  - [x] 1.1 Create deployment IAM user
    - Create IAM user `West_of_house_AmplifyDeploymentUser` with deployment permissions
    - Attach policy for Amplify, Lambda, DynamoDB, IAM, CloudFormation, S3, API Gateway
    - Generate access keys and configure AWS CLI profile
    - Document deployment credentials setup in README
    - _Requirements: 21.6, 21.7_
  
  - [x] 1.2 Initialize project structure
    - Create folder structure: src/, tests/, scripts/, data/, documents/
    - Copy game data JSON files to data/ directory
    - Create .gitignore to exclude sensitive files and build artifacts
    - _Requirements: 22.4_
  
  - [x] 1.3 Set up AWS Amplify project
    - Run `amplify init` with project configuration
    - Add API with REST endpoints
    - Add Lambda function with Python 3.12 ARM64 runtime
    - Add DynamoDB table with TTL enabled
    - _Requirements: 22.1, 22.2, 22.3_
  
  - [x] 1.4 Configure IAM roles for runtime
    - Create Lambda execution role with least-privilege DynamoDB permissions
    - Verify IAM policies scope to specific table ARN (no wildcards)
    - Add CloudWatch Logs permissions for debugging
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_
  
  - [x] 1.5 Create deployment scripts
    - Create script to package Lambda function with dependencies
    - Create script to bundle game data JSON files
    - Create script to deploy via Amplify CLI
    - _Requirements: 22.4_

- [x] 2. Data layer and world loader
  - [x] 2.1 Copy game data JSON files to Lambda data directory
    - Copy `west_of_house_json/*.json` to `src/lambda/game_handler/data/`
    - Verify JSON structure and spooky field presence
    - _Requirements: 20.4_

  - [x] 2.2 Implement world data loader
    - Create `world_loader.py` to load rooms, objects, and flags from JSON
    - Implement caching mechanism for Lambda warm starts
    - Add error handling for missing or malformed JSON
    - _Requirements: 20.1, 20.2, 20.3_

  - [x] 2.3 Write unit tests for world loader
    - Test JSON loading and parsing
    - Test error handling for invalid data
    - Test caching behavior
    - _Requirements: 20.4_

- [x] 3. Game state management
  - [x] 3.1 Implement GameState data model
    - Create `state_manager.py` with GameState class
    - Include fields: session_id, current_room, inventory, flags, sanity, score, moves, lamp_battery
    - Implement state serialization/deserialization for DynamoDB
    - _Requirements: 1.2, 1.5_

  - [x] 3.2 Implement DynamoDB session operations
    - Create session save function (put_item with TTL)
    - Create session load function (get_item)
    - Create session delete function for cleanup
    - Add error handling for DynamoDB operations
    - _Requirements: 22.1, 22.2, 22.3_

  - [x] 3.3 Write property test for state persistence
    - **Property 16: Save/load round trip**
    - **Validates: Requirements 1.2, 1.5**
    - Test that saving and loading state preserves all fields
    - _Requirements: 1.2, 1.5_

- [x] 4. Command parser
  - [x] 4.1 Implement basic command parser
    - Create `command_parser.py` with CommandParser class
    - Parse movement commands (GO, NORTH, SOUTH, EAST, WEST, UP, DOWN, IN, OUT)
    - Parse object commands (TAKE, DROP, EXAMINE, OPEN, CLOSE, READ, MOVE)
    - Parse utility commands (INVENTORY, LOOK, QUIT)
    - Handle synonyms and variations
    - _Requirements: 2.2_

  - [x] 4.2 Write property test for parsing determinism
    - **Property 4: Command parsing determinism**
    - **Validates: Requirements 2.2**
    - Test that parsing same command always produces same result
    - _Requirements: 2.2_

  - [x] 4.3 Write unit tests for command parser
    - Test all verb categories
    - Test synonym handling
    - Test invalid command handling
    - _Requirements: 2.2, 2.5_

- [x] 5. Core game engine - movement
  - [x] 5.1 Implement room navigation
    - Create `game_engine.py` with movement handler
    - Validate exits against room data
    - Update current_room in state
    - Handle conditional exits based on flags
    - Return appropriate room descriptions
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

  - [x] 5.2 Write property test for movement validation
    - **Property 6: Movement validation**
    - **Validates: Requirements 3.1, 3.4, 3.5**
    - Test that movement succeeds only for valid exits
    - _Requirements: 3.1, 3.4, 3.5_

  - [x] 5.3 Write unit tests for navigation
    - Test valid movement between rooms
    - Test blocked directions
    - Test flag-gated exits
    - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 6. Core game engine - object interaction
  - [x] 6.1 Implement object examination
    - Add examine handler to game engine
    - Return spooky descriptions based on sanity level
    - Handle scenery vs takeable objects
    - _Requirements: 4.1_

  - [x] 6.2 Implement take/drop mechanics
    - Add take handler (validate takeable, add to inventory, remove from room)
    - Add drop handler (remove from inventory, add to room)
    - Validate object existence and state
    - _Requirements: 4.2, 4.3, 5.2, 5.3_

  - [x] 6.3 Write property test for object conservation
    - **Property 7: Object conservation (take/drop)**
    - **Validates: Requirements 4.2, 4.3**
    - Test that take then drop returns object to room
    - _Requirements: 4.2, 4.3_

  - [x] 6.4 Write property test for inventory tracking
    - **Property 8: Inventory tracking**
    - **Validates: Requirements 5.1, 5.5**
    - Test that inventory reflects take/drop operations
    - _Requirements: 5.1, 5.5_

  - [x] 6.5 Implement object interactions (open, close, read, move)
    - Add interaction handlers for each verb
    - Check prerequisites and conditions
    - Update object state
    - Update game flags when appropriate
    - _Requirements: 4.4, 4.5_

  - [x] 6.6 Write unit tests for object interactions
    - Test examine, take, drop for various objects
    - Test open/close for containers
    - Test read for readable objects
    - Test move for moveable objects (rug)
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 7. Sanity system (Halloween mechanic)
  - [x] 7.1 Implement sanity mechanics
    - Create `sanity_system.py` with SanitySystem class
    - Implement sanity loss function with triggers
    - Implement sanity gain function (capped at 100)
    - Implement description variant selection based on sanity level
    - Track safe rooms for sanity restoration
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [x] 7.2 Write property test for sanity bounds
    - **Property 10: Sanity bounds**
    - **Validates: Requirements 6.1, 6.5**
    - Test that sanity always stays in [0, 100]
    - _Requirements: 6.1, 6.5_

  - [x] 7.3 Write property test for sanity threshold effects
    - **Property 11: Sanity threshold effects**
    - **Validates: Requirements 6.2, 6.3, 6.4**
    - Test that descriptions change at correct sanity thresholds
    - _Requirements: 6.2, 6.3, 6.4_

  - [x] 7.4 Write unit tests for sanity system
    - Test sanity loss from cursed rooms
    - Test sanity gain in safe rooms
    - Test description variants at different sanity levels
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8. Container system
  - [x] 8.1 Implement container operations
    - Add open/close handlers for containers
    - Add put/take handlers for container contents
    - Validate capacity limits
    - Handle transparent containers (trophy case)
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

  - [x] 8.2 Write property test for container capacity
    - **Property 23: Container capacity enforcement**
    - **Validates: Requirements 15.2**
    - Test that container capacity is never exceeded
    - _Requirements: 15.2_

  - [x] 8.3 Write unit tests for containers
    - Test open/close operations
    - Test put/take from containers
    - Test capacity enforcement
    - Test trophy case (transparent container)
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] 9. Light system
  - [x] 9.1 Implement lamp and darkness mechanics
    - Add lamp on/off handlers
    - Implement battery drain (1 per turn)
    - Implement automatic shutoff at 0 battery
    - Add darkness detection for rooms
    - Return darkness descriptions when appropriate
    - _Requirements: 14.1, 14.2, 14.3_

  - [x] 9.2 Write property test for lamp battery drain
    - **Property 21: Lamp battery drain**
    - **Validates: Requirements 14.2**
    - Test that battery decreases by 1 per turn when lamp is on
    - _Requirements: 14.2_

  - [x] 9.3 Write property test for lamp auto-shutoff
    - **Property 22: Lamp auto-shutoff**
    - **Validates: Requirements 14.3**
    - Test that lamp turns off automatically at 0 battery
    - _Requirements: 14.3_

- [x] 10. Scoring and treasure system
  - [x] 10.1 Implement treasure placement and scoring
    - Add handler for placing treasures in trophy case
    - Update score based on treasure value
    - Track which treasures have been scored
    - Prevent double-scoring same treasure
    - _Requirements: 13.1, 13.2_

  - [x] 10.2 Write property test for score accumulation
    - **Property 19: Score accumulation**
    - **Validates: Requirements 13.1, 13.2**
    - Test that score equals sum of treasure values
    - _Requirements: 13.1, 13.2_

  - [x] 10.3 Implement win condition
    - Check if score reaches 350
    - Set won_flag when win condition met
    - Return victory message
    - _Requirements: 13.4, 13.5_

  - [x] 10.4 Write property test for win condition
    - **Property 20: Win condition trigger**
    - **Validates: Requirements 13.4**
    - Test that won_flag is set when score reaches 350
    - _Requirements: 13.4_

- [x] 11. Basic puzzles
  - [x] 11.1 Implement simple flag-based puzzles
    - Move rug to reveal trap door (rug_moved flag)
    - Open trap door to access cellar
    - Open kitchen window to enter house (kitchen_window_flag)
    - Move leaves to reveal grating (grate_revealed flag)
    - Unlock grating with keys (grate_unlocked flag)
    - _Requirements: 18.1, 18.2, 18.3_

  - [x] 11.2 Write unit tests for puzzles
    - Test rug/trap door puzzle
    - Test window entry puzzle
    - Test grating puzzle
    - Test prerequisite checking
    - _Requirements: 18.1, 18.2, 18.3_

- [x] 12. Lambda handler and API integration
  - [x] 12.1 Implement Lambda handler
    - Create `index.py` as Lambda entry point
    - Parse API Gateway events
    - Route to appropriate game engine functions
    - Format JSON responses
    - Handle errors and return appropriate status codes
    - _Requirements: 11.1, 11.2, 11.3, 2.1, 2.3, 2.4_

  - [x] 12.2 Implement new game endpoint
    - Generate unique session ID
    - Initialize game state with starting values
    - Save to DynamoDB
    - Return initial room description and state
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [x] 12.3 Write property test for session uniqueness
    - **Property 1: Session uniqueness**
    - **Validates: Requirements 1.1**
    - Test that all generated session IDs are unique
    - _Requirements: 1.1_

  - [x] 12.4 Write property test for initialization consistency
    - **Property 2: Initialization consistency**
    - **Validates: Requirements 1.2, 1.5**
    - Test that all new games start with same initial state
    - _Requirements: 1.2, 1.5_

  - [x] 12.5 Implement command endpoint
    - Load session from DynamoDB
    - Parse command
    - Execute command via game engine
    - Update state
    - Save state to DynamoDB
    - Return response with updated state
    - _Requirements: 2.1, 2.3, 2.4, 11.1_

  - [x] 12.6 Write property test for invalid command state preservation
    - **Property 5: Invalid command state preservation**
    - **Validates: Requirements 2.5, 16.5**
    - Test that invalid commands don't change state
    - _Requirements: 2.5, 16.5_

  - [x] 12.7 Implement state query endpoint
    - Load session from DynamoDB
    - Return complete game state
    - _Requirements: 19.1, 19.2, 19.3_

  - [x] 12.8 Write property test for API response format
    - **Property 17: API response format consistency**
    - **Validates: Requirements 11.2, 19.2, 19.4**
    - Test that all responses follow consistent JSON schema
    - _Requirements: 11.2, 19.2, 19.4_

- [x] 13. Error handling and validation
  - [x] 13.1 Implement comprehensive error handling
    - Add try-catch blocks around all operations
    - Return appropriate HTTP status codes (400, 404, 500)
    - Log errors with context
    - Ensure state consistency on errors
    - _Requirements: 16.1, 16.2, 16.3, 16.5_

  - [x] 13.2 Write property test for error status codes
    - **Property 25: Error status codes**
    - **Validates: Requirements 16.1, 16.2, 16.3**
    - Test that errors return correct HTTP status codes
    - _Requirements: 16.1, 16.2, 16.3_

  - [x] 13.3 Write unit tests for error handling
    - Test invalid session ID (404)
    - Test malformed JSON (400)
    - Test internal errors (500)
    - Test state preservation on errors
    - _Requirements: 16.1, 16.2, 16.3, 16.5_

- [x] 14. Session management and cleanup
  - [x] 14.1 Implement session expiration
    - Set TTL on DynamoDB items (1 hour default)
    - Update last accessed timestamp on each request
    - _Requirements: 22.1, 22.3_

  - [x] 14.2 Write property test for session expiration
    - **Property 29: Session expiration cleanup**
    - **Validates: Requirements 22.2, 22.4**
    - Test that expired sessions are removed
    - _Requirements: 22.2, 22.4_

- [x] 15. Checkpoint - Ensure all tests pass
  - Run all unit tests
  - Run all property-based tests
  - Fix any failing tests
  - Verify test coverage is adequate
  - Ask the user if questions arise

- [x] 16. Integration testing
  - [x] 16.1 Write integration test for complete game flow
    - Test: New game → Move → Take object → Examine → Drop → Score
    - Verify state persistence across commands
    - _Requirements: 1.1, 2.1, 3.2, 4.2, 4.3, 13.1_

  - [x] 16.2 Write integration test for sanity degradation
    - Test: Enter cursed rooms → Sanity drops → Descriptions change
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 16.3 Write integration test for puzzle solving
    - Test: Move rug → Open trap door → Navigate to cellar
    - _Requirements: 18.1, 18.2, 18.3_

- [ ] 17. Deployment and AWS setup
  - [x] 17.1 Configure AWS resource tagging
    - Update Amplify configuration to include required tags
    - Add tags to amplify/backend configuration files: Project=west-of-haunted-house, ManagedBy=vedfolnir, Environment=<user-defined>
    - Ensure Lambda, DynamoDB, API Gateway, and all other resources receive tags
    - _Requirements: 24.1, 24.2, 24.3, 24.4_

  - [x] 17.2 Package Lambda function
    - Create deployment script to bundle code and dependencies
    - Include game data JSON files in package
    - Create ZIP file for Lambda deployment
    - _Requirements: 21.1, 21.4_

  - [ ] 17.3 Migrate to Amplify Gen 2
    - [x] 17.3.1 Create new Gen 2 project structure
      - Run `npm create amplify@latest` to initialize Gen 2 project
      - Set up TypeScript configuration for infrastructure
      - Create amplify/ directory with backend.ts entry point
      - Install dependencies with `npm install`
      - _Requirements: 22.4, 22.6_
    
    - [x] 17.3.2 Define DynamoDB table with Gen 2
      - Create amplify/data/resource.ts
      - Define GameSessions table schema with TTL
      - Configure on-demand billing mode
      - Add required tags (Project, ManagedBy, Environment)
      - _Requirements: 22.3, 24.1, 24.2, 24.3_
    
    - [x] 17.3.3 Define Lambda function with Gen 2
      - Create amplify/functions/game-handler/resource.ts
      - Configure Python 3.12 runtime with ARM64 architecture
      - Set up bundling for Python dependencies and game data
      - Configure environment variables (TABLE_NAME auto-resolved)
      - Set memory to 128MB and timeout to 30 seconds
      - Add required tags
      - _Requirements: 21.1, 21.2, 22.1, 22.6, 22.7, 24.1, 24.2, 24.3_
    
    - [x] 17.3.4 Migrate Python Lambda code
      - Copy existing Python code to amplify/functions/game-handler/
      - Copy game data JSON files to function directory
      - Update imports if needed for Gen 2 structure
      - Verify requirements.txt is complete
      - _Requirements: 20.4, 22.1_
    
    - [x] 17.3.5 Define API Gateway with Gen 2
      - Create REST API in backend.ts
      - Add /game/new POST endpoint
      - Add /game/command POST endpoint
      - Add /game/state/{session_id} GET endpoint
      - Configure CORS for all endpoints
      - Integrate Lambda function with API Gateway
      - _Requirements: 11.1, 11.2_
    
    - [x] 17.3.6 Grant IAM permissions
      - Grant Lambda read/write access to DynamoDB table
      - Verify least-privilege IAM policies
      - Ensure no wildcard permissions
      - Verify CloudWatch Logs permissions
      - _Requirements: 21.1, 21.2, 21.3, 21.4_
    
    - [x] 17.3.7 Test with local sandbox
      - Run `npx ampx sandbox` to start local environment
      - Test new game endpoint
      - Test command endpoint
      - Test state query endpoint
      - Verify DynamoDB integration
      - _Requirements: 11.1, 11.2, 22.1, 22.3_
    
    - [ ] 17.3.8 Deploy to AWS with Gen 2
      - Commit Gen 2 configuration to Git
      - Push to main branch for automatic deployment
      - Monitor deployment progress in Amplify Console
      - Verify all resources are created successfully
      - _Requirements: 22.4_

  - [ ] 17.4 Verify Gen 2 deployment
    - Verify Lambda function is created with ARM64 architecture
    - Verify DynamoDB table is created with TTL
    - Verify API Gateway endpoints are accessible
    - Verify all resources have required tags
    - _Requirements: 21.1, 21.2, 21.3, 21.4, 24.1, 24.2, 24.3, 24.4_

  - [ ] 17.5 Test deployed API
    - Test new game endpoint
    - Test command endpoint with various commands
    - Test state query endpoint
    - Verify DynamoDB session storage
    - _Requirements: 11.1, 11.2, 21.1_

  - [ ] 17.6 Create AWS resource cleanup script
    - Create `scripts/cleanup-aws-resources.sh` script
    - Implement resource discovery using AWS CLI with tag filters
    - Delete resources in correct order: API Gateway → Lambda → DynamoDB → IAM roles → CloudFormation stacks
    - Add safety confirmation prompt before deletion
    - Verify only resources with all three required tags are deleted
    - _Requirements: 25.1, 25.2, 25.3, 25.4_

  - [ ] 17.7 Test cleanup script
    - Run cleanup script in test environment
    - Verify all tagged resources are identified
    - Verify resources are deleted in correct order
    - Verify no untagged resources are affected
    - Verify cleanup completion confirmation
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

- [ ] 18. Cost estimation and optimization
  - [ ] 18.1 Estimate AWS costs
    - Use AWS pricing calculator or MCP server
    - Calculate Lambda invocations cost
    - Calculate DynamoDB read/write cost
    - Calculate Amplify hosting cost
    - Verify total is under $5/month target
    - _Requirements: 21.5_

  - [ ] 18.2 Optimize if needed
    - Reduce Lambda memory if possible
    - Optimize DynamoDB access patterns
    - Add caching where appropriate
    - _Requirements: 21.5_

- [ ] 19. Documentation and README
  - [ ] 19.1 Create comprehensive README
    - Project overview and features
    - Architecture diagram
    - Setup instructions
    - Deployment instructions
    - API documentation
    - Cost breakdown
    - _Requirements: 21.4_

  - [ ] 19.2 Document API endpoints
    - POST /api/game/new
    - POST /api/game/command
    - GET /api/game/state/{session_id}
    - Include request/response examples
    - _Requirements: 11.1, 11.2_

- [ ] 20. Final checkpoint - Complete MVP
  - Verify all core features work end-to-end
  - Verify all tests pass
  - Verify deployment is successful
  - Verify costs are under target
  - Demo the game to ensure it's playable
  - Ask the user if questions arise

---

## Notes

- Tasks marked with `*` are optional testing tasks that can be skipped for faster MVP delivery
- Each property-based test should run minimum 100 iterations
- Property tests must be tagged with: `# Feature: game-backend-api, Property {number}: {property_text}`
- Focus on getting core gameplay working before optimizing
- Deploy early and test in AWS environment
- Keep Lambda package size minimal (<50MB)
- Use ARM64 architecture for 20% cost savings
