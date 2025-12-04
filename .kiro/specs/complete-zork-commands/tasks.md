# Implementation Plan: Complete Zork Command Implementation

- [x] 1. Audit and document all Zork I commands
  - Review gsyntax.zil and gverbs.zil from original Zork source
  - Create comprehensive list of all verbs with syntax patterns
  - Categorize commands by functional area (movement, object, combat, meta, special)
  - Compare against current implementation to identify gaps
  - Prioritize commands by gameplay impact and implementation complexity
  - Document findings in a command audit spreadsheet or markdown file
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 2. Implement core movement commands
- [x] 2.1 Implement CLIMB command handler
  - Add handle_climb method to GameEngine
  - Support CLIMB UP and CLIMB DOWN with climbable objects
  - Validate object has climbable property
  - Check for valid exits in specified direction
  - Move player to connected room
  - Return appropriate success/failure messages with haunted theme
  - _Requirements: 2.1_

- [x] 2.2 Write property test for climb movement
  - **Property 1: Climb movement consistency**
  - **Validates: Requirements 2.1**

- [x] 2.3 Implement ENTER and EXIT commands
  - Add handle_enter and handle_exit methods to GameEngine
  - Support entering objects (vehicles, buildings, passages)
  - Support exiting current location or object
  - Validate entry/exit points exist
  - Update player location appropriately
  - Return thematic descriptions
  - _Requirements: 2.2_

- [x] 2.4 Write property test for enter/exit round-trip
  - **Property 2: Enter/Exit inverse operations**
  - **Validates: Requirements 2.2**

- [x] 2.5 Implement BOARD and DISEMBARK commands
  - Add handle_board and handle_disembark methods to GameEngine
  - Add vehicle support to world data (is_vehicle property)
  - Support boarding vehicles (boat, basket, etc.)
  - Track player's current vehicle in game state
  - Support disembarking from vehicles
  - Validate vehicle is present and accessible
  - Return appropriate messages
  - _Requirements: 2.3, 2.4_

- [x] 2.6 Write property test for board/disembark round-trip
  - **Property 3: Board/Disembark inverse operations**
  - **Validates: Requirements 2.3, 2.4**

- [-] 3. Implement object manipulation commands
- [x] 3.1 Implement LOCK and UNLOCK commands
  - Add handle_lock and handle_unlock methods to GameEngine
  - Support locking/unlocking with appropriate keys
  - Add lockable and key properties to objects
  - Validate key matches lock
  - Update object lock state
  - Return success/failure messages with haunted theme
  - _Requirements: 3.3_

- [x] 3.2 Write property test for lock/unlock round-trip
  - **Property 5: Lock/Unlock inverse operations**
  - **Validates: Requirements 3.3**

- [x] 3.3 Implement TURN command
  - Add handle_turn method to GameEngine
  - Support turning turnable objects (dials, valves, etc.)
  - Add turnable property to objects
  - Update object rotation/activation state
  - Trigger any associated effects
  - Return thematic descriptions
  - _Requirements: 3.4_

- [x] 3.4 Write property test for turn state changes
  - **Property 6: Turn command state changes**
  - **Validates: Requirements 3.4**

- [x] 3.5 Implement PUSH and PULL commands
  - Add handle_push and handle_pull methods to GameEngine
  - Support pushing/pulling moveable objects
  - Add moveable property to objects
  - Update object location or position
  - Trigger any associated effects (revealing items, etc.)
  - Return appropriate messages
  - _Requirements: 3.5_

- [x] 3.6 Write property test for push/pull relocation
  - **Property 7: Push/Pull object relocation**
  - **Validates: Requirements 3.5**

- [x] 3.7 Implement TIE and UNTIE commands
  - Add handle_tie and handle_untie methods to GameEngine
  - Support tying rope-like objects to targets
  - Add rope and tie_target properties to objects
  - Track tied state in object properties
  - Support untying previously tied objects
  - Return thematic descriptions
  - _Requirements: 3.6_

- [x] 3.8 Write property test for tie/untie round-trip
  - **Property 8: Tie/Untie inverse operations**
  - **Validates: Requirements 3.6**

- [x] 3.9 Implement FILL and POUR commands
  - Add handle_fill and handle_pour methods to GameEngine
  - Support filling containers from liquid sources
  - Support pouring liquids from containers
  - Track liquid contents in container state
  - Validate container capacity
  - Handle liquid evaporation/spillage
  - Return appropriate messages
  - _Requirements: 3.7, 3.8_

- [x] 3.10 Write property test for fill/pour round-trip
  - **Property 9: Fill/Pour inverse operations**
  - **Validates: Requirements 3.7, 3.8**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [-] 5. Implement examination commands
- [x] 5.1 Implement LOOK UNDER and LOOK BEHIND commands
  - Add handle_look_under and handle_look_behind methods to GameEngine
  - Support looking under/behind objects
  - Reveal hidden items or information
  - Return "nothing there" message if appropriate
  - Use haunted theme descriptions
  - _Requirements: 4.2_

- [x] 5.2 Write property test for look under/behind
  - **Property 11: Look under/behind reveals information**
  - **Validates: Requirements 4.2**

- [x] 5.3 Enhance LOOK INSIDE for containers
  - Update handle_examine_container method
  - Ensure it lists all container contents
  - Handle open/closed and transparent states
  - Format contents list clearly
  - _Requirements: 4.3_

- [x] 5.4 Write property test for look inside contents
  - **Property 12: Look inside container contents**
  - **Validates: Requirements 4.3**

- [x] 5.5 Implement SEARCH command
  - Add handle_search method to GameEngine
  - Support searching objects and locations
  - Reveal hidden details or items
  - Return appropriate "found" or "nothing" messages
  - Use thematic descriptions
  - _Requirements: 4.4_

- [x] 5.6 Write property test for search reveals
  - **Property 13: Search reveals details**
  - **Validates: Requirements 4.4**

- [x] 5.7 Implement READ command
  - Add handle_read method to GameEngine
  - Support reading readable objects (books, signs, notes)
  - Add readable property and text content to objects
  - Display text content
  - Return "nothing to read" if not readable
  - _Requirements: 4.5_

- [x] 5.8 Write property test for read displays text
  - **Property 14: Read displays text**
  - **Validates: Requirements 4.5**

- [x] 5.9 Implement LISTEN command
  - Add handle_listen method to GameEngine
  - Support listening to objects and rooms
  - Add audio_description property to objects/rooms
  - Return audible information or silence message
  - Use atmospheric descriptions
  - _Requirements: 4.6_

- [x] 5.10 Write property test for listen audio info
  - **Property 15: Listen provides audio information**
  - **Validates: Requirements 4.6**

- [x] 5.11 Implement SMELL command
  - Add handle_smell method to GameEngine
  - Support smelling objects and rooms
  - Add smell_description property to objects/rooms
  - Return olfactory information or neutral message
  - Use thematic descriptions
  - _Requirements: 4.7_

- [x] 5.12 Write property test for smell olfactory info
  - **Property 16: Smell provides olfactory information**
  - **Validates: Requirements 4.7**

- [x] 6. Implement combat and interaction commands
- [x] 6.1 Implement ATTACK command
  - Add handle_attack method to GameEngine
  - Support attacking creatures with weapons
  - Add combat properties to creatures (health, strength)
  - Add weapon properties to objects (damage, weapon_type)
  - Implement basic combat resolution
  - Update creature and player states
  - Return combat descriptions with haunted theme
  - _Requirements: 5.1_

- [x] 6.2 Write property test for attack combat initiation
  - **Property 17: Attack initiates combat**
  - **Validates: Requirements 5.1**

- [x] 6.3 Implement THROW command
  - Add handle_throw method to GameEngine
  - Support throwing objects at targets
  - Validate object is in inventory
  - Move object to target location
  - Apply any throw effects (damage, activation)
  - Return thematic descriptions
  - _Requirements: 5.2_

- [x] 6.4 Write property test for throw relocation
  - **Property 18: Throw relocates object**
  - **Validates: Requirements 5.2**

- [x] 6.5 Implement GIVE command
  - Add handle_give method to GameEngine
  - Support giving objects to NPCs
  - Validate object is in inventory
  - Transfer object to NPC possession
  - Trigger NPC reactions if defined
  - Return appropriate messages
  - _Requirements: 5.3_

- [x] 6.6 Write property test for give ownership transfer
  - **Property 19: Give transfers ownership**
  - **Validates: Requirements 5.3**

- [x] 6.7 Implement TELL and ASK commands
  - Add handle_tell method to GameEngine
  - Support dialogue with NPCs
  - Add dialogue responses to NPC data
  - Return NPC responses
  - Track conversation state if needed
  - Use thematic dialogue
  - _Requirements: 5.4_

- [x] 6.8 Write property test for tell/ask dialogue
  - **Property 20: Tell/Ask generates dialogue**
  - **Validates: Requirements 5.4**

- [x] 6.9 Implement WAKE command
  - Add handle_wake method to GameEngine
  - Support waking sleeping creatures
  - Add sleeping state to creatures
  - Change creature state from sleeping to awake
  - Trigger wake-up reactions
  - Return appropriate messages
  - _Requirements: 5.5_

- [x] 6.10 Write property test for wake state change
  - **Property 21: Wake changes creature state**
  - **Validates: Requirements 5.5**

- [x] 6.11 Implement KISS command
  - Add handle_kiss method to GameEngine
  - Support kissing NPCs
  - Return humorous or thematic responses
  - No state changes (just flavor)
  - _Requirements: 5.6_

- [x] 6.12 Write property test for kiss response
  - **Property 22: Kiss generates response**
  - **Validates: Requirements 5.6**

- [x] 7. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [-] 8. Implement utility commands
- [x] 8.1 Implement BURN command
  - Add handle_burn method to GameEngine
  - Support burning flammable objects with fire sources
  - Add flammable property to objects
  - Remove or modify burned objects
  - Apply any burn effects
  - Return thematic descriptions
  - _Requirements: 6.1_

- [x] 8.2 Write property test for burn destruction
  - **Property 23: Burn destroys flammable objects**
  - **Validates: Requirements 6.1**

- [x] 8.3 Implement CUT command
  - Add handle_cut method to GameEngine
  - Support cutting objects with cutting tools
  - Add cuttable property to objects
  - Modify cut objects (split, open, etc.)
  - Return appropriate messages
  - _Requirements: 6.2_

- [x] 8.4 Write property test for cut modification
  - **Property 24: Cut modifies objects**
  - **Validates: Requirements 6.2**

- [x] 8.5 Implement DIG command
  - Add handle_dig method to GameEngine
  - Support digging at locations with tools
  - Add diggable property to locations
  - Reveal hidden items or passages
  - Return appropriate messages
  - _Requirements: 6.3_

- [x] 8.6 Write property test for dig reveals
  - **Property 25: Dig reveals or modifies**
  - **Validates: Requirements 6.3**

- [x] 8.7 Implement INFLATE and DEFLATE commands
  - Add handle_inflate and handle_deflate methods to GameEngine
  - Support inflating/deflating inflatable objects
  - Add inflatable property to objects
  - Track inflation state
  - Return appropriate messages
  - _Requirements: 6.4_

- [x] 8.8 Write property test for inflate/deflate round-trip
  - **Property 26: Inflate/Deflate inverse operations**
  - **Validates: Requirements 6.4**

- [x] 8.9 Implement WAVE, RUB, SHAKE, SQUEEZE commands
  - Add handle_wave, handle_rub, handle_shake, handle_squeeze methods
  - Support these actions on all objects
  - Return thematic responses
  - Apply any special effects if defined
  - _Requirements: 6.5, 6.6, 6.7, 6.8_

- [x] 8.10 Write property tests for utility command responses
  - **Property 27: Wave generates response**
  - **Property 28: Rub/Touch generates response**
  - **Property 29: Shake generates response or state change**
  - **Property 30: Squeeze generates response or state change**
  - **Validates: Requirements 6.5, 6.6, 6.7, 6.8**

- [x] 9. Implement meta-game commands
- [x] 9.1 Implement SAVE command
  - Add handle_save method to GameEngine
  - Serialize current game state to JSON
  - Store in DynamoDB with unique save ID
  - Include timestamp and session info
  - Return success message with save ID
  - _Requirements: 7.1_

- [x] 9.2 Implement RESTORE command
  - Add handle_restore method to GameEngine
  - Load game state from DynamoDB by save ID
  - Deserialize JSON to GameState object
  - Validate save data integrity
  - Return success message
  - _Requirements: 7.2_

- [x] 9.3 Write property test for save/restore round-trip
  - **Property 31: Save/Restore round-trip**
  - **Validates: Requirements 7.1, 7.2**

- [x] 9.4 Implement RESTART command
  - Add handle_restart method to GameEngine
  - Reset game state to initial values
  - Clear inventory, flags, score
  - Return to starting room
  - Return confirmation message
  - _Requirements: 7.3_

- [x] 9.5 Implement SCORE command
  - Add handle_score method to GameEngine
  - Display current score and rank
  - Calculate rank based on score thresholds
  - Show treasures collected
  - Return formatted score display
  - _Requirements: 7.5_

- [x] 9.6 Write property test for score display
  - **Property 32: Score displays current value**
  - **Validates: Requirements 7.5**

- [x] 9.7 Implement verbosity commands (VERBOSE, BRIEF, SUPERBRIEF)
  - Add handle_verbose, handle_brief, handle_superbrief methods
  - Add verbosity field to GameState
  - Add visited_rooms tracking to GameState
  - Update room description logic to respect verbosity
  - VERBOSE: always show full descriptions
  - BRIEF: full on first visit, abbreviated after
  - SUPERBRIEF: room name only
  - Return confirmation messages
  - _Requirements: 7.6, 7.7, 7.8_

- [-] 10. Implement special and easter egg commands
- [x] 10.1 Implement easter egg commands (XYZZY, PLUGH)
  - Add handle_easter_egg method to GameEngine
  - Recognize XYZZY, PLUGH, and other magic words
  - Return humorous or thematic responses
  - Optionally trigger special effects
  - _Requirements: 8.1_

- [x] 10.2 Implement HELLO command
  - Add handle_hello method to GameEngine
  - Return greeting response
  - Vary response based on context
  - Use haunted theme
  - _Requirements: 8.2_

- [x] 10.3 Implement CURSE command
  - Add handle_curse method to GameEngine
  - Recognize profanity and curse words
  - Return chiding response
  - Don't penalize player
  - _Requirements: 8.3_

- [x] 10.4 Write property test for profanity handling
  - **Property 33: Profanity handling**
  - **Validates: Requirements 8.3**

- [x] 10.5 Implement PRAY, JUMP, YELL commands
  - Add handle_pray, handle_jump, handle_yell methods
  - Return thematic responses
  - Apply any special effects if appropriate
  - _Requirements: 8.4, 8.5, 8.6_

- [x] 10.6 Implement ECHO command
  - Add handle_echo method to GameEngine
  - Echo back player's words
  - Format echo appropriately
  - _Requirements: 8.7_

- [x] 10.7 Write property test for echo
  - **Property 34: Echo repeats input**
  - **Validates: Requirements 8.7**

- [x] 11. Enhance error handling and feedback
- [x] 11.1 Improve unimplemented command messages
  - Update execute_command to provide specific messages
  - Indicate command is recognized but not yet available
  - Suggest alternative commands
  - _Requirements: 9.1_

- [x] 11.2 Write property test for unimplemented messages
  - **Property 35: Unimplemented command messages**
  - **Validates: Requirements 9.1**

- [x] 11.3 Add incorrect usage guidance
  - Detect common syntax errors
  - Provide usage examples
  - Suggest correct syntax
  - _Requirements: 9.2_

- [x] 11.4 Write property test for usage guidance
  - **Property 36: Incorrect usage guidance**
  - **Validates: Requirements 9.2**

- [x] 11.5 Improve missing object messages
  - Clearly state object not present
  - Check both room and inventory
  - Suggest looking around
  - _Requirements: 9.3_

- [x] 11.6 Write property test for missing object messages
  - **Property 37: Missing object messages**
  - **Validates: Requirements 9.3**

- [x] 11.7 Add impossible action explanations
  - Explain why action cannot be done
  - Provide hints when appropriate
  - Maintain immersion
  - _Requirements: 9.4_

- [x] 11.8 Write property test for impossible action explanations
  - **Property 38: Impossible action explanations**
  - **Validates: Requirements 9.4**

- [x] 11.9 Add missing parameter prompts
  - Detect incomplete commands
  - Prompt for missing objects
  - Guide player to complete command
  - _Requirements: 9.5_

- [x] 11.10 Write property test for missing parameter prompts
  - **Property 39: Missing parameter prompts**
  - **Validates: Requirements 9.5**

- [x] 12. Enhance command parser for synonyms and variations
- [x] 12.1 Add synonym support to parser
  - Expand synonym dictionary in command_parser.py
  - Map all Zork synonyms to primary verbs
  - Test synonym recognition
  - _Requirements: 10.1_

- [x] 12.2 Write property test for synonym equivalence
  - **Property 40: Synonym equivalence**
  - **Validates: Requirements 10.1**

- [x] 12.3 Add abbreviation support
  - Recognize common abbreviations (N, S, E, W, I, X, etc.)
  - Expand to full commands
  - Test abbreviation handling
  - _Requirements: 10.2_

- [x] 12.4 Write property test for abbreviation expansion
  - **Property 41: Abbreviation expansion**
  - **Validates: Requirements 10.2**

- [x] 12.5 Add variation mapping
  - Handle command variations (GET/TAKE, LOOK/EXAMINE, etc.)
  - Map to canonical forms
  - Test variation handling
  - _Requirements: 10.3_

- [x] 12.6 Write property test for variation mapping
  - **Property 42: Variation mapping**
  - **Validates: Requirements 10.3**

- [x] 12.7 Improve preposition parsing
  - Handle all common prepositions (IN, ON, WITH, TO, FROM, etc.)
  - Parse multi-word commands correctly
  - Test preposition handling
  - _Requirements: 10.4_

- [x] 12.8 Write property test for preposition parsing
  - **Property 43: Preposition parsing**
  - **Validates: Requirements 10.4**

- [x] 12.9 Add article handling
  - Ignore articles (A, AN, THE) appropriately
  - Test commands with and without articles
  - _Requirements: 10.5_

- [x] 12.10 Write property test for article handling
  - **Property 44: Article handling**
  - **Validates: Requirements 10.5**

- [x] 13. Implement context-sensitive command handling
- [x] 13.1 Add disambiguation system
  - Detect ambiguous commands
  - Prompt for clarification
  - Track disambiguation context
  - _Requirements: 11.3_

- [x] 13.2 Write property test for disambiguation prompts
  - **Property 45: Disambiguation prompts**
  - **Validates: Requirements 11.3**

- [x] 13.3 Add prerequisite checking system
  - Define prerequisites for commands
  - Check prerequisites before execution
  - Return helpful error messages
  - _Requirements: 11.4_

- [x] 13.4 Write property test for prerequisite checking
  - **Property 46: Prerequisite checking**
  - **Validates: Requirements 11.4**

- [x] 13.5 Add multi-object handling
  - Support commands affecting multiple objects
  - Process each object appropriately
  - Return combined results
  - _Requirements: 11.5_

- [x] 13.6 Write property test for multi-object handling
  - **Property 47: Multi-object handling**
  - **Validates: Requirements 11.5**

- [-] 14. Ensure haunted theme consistency across all commands
- [x] 14.1 Review all command responses for haunted narrative
  - Audit all response messages
  - Replace original Zork descriptions with haunted theme equivalents
  - Ensure spooky/haunted language in all text
  - Update any generic messages to use haunted vocabulary
  - _Requirements: 12.1_

- [x] 14.2 Write property test for spooky narrative consistency
  - **Property 48: Spooky narrative consistency**
  - **Validates: Requirements 12.1**

- [x] 14.3 Update object references to use haunted titles
  - Review all commands that reference objects
  - Ensure haunted theme object titles are used
  - Update object descriptions to haunted equivalents
  - Test object name consistency
  - _Requirements: 12.2_

- [x] 14.4 Write property test for haunted object titles
  - **Property 49: Haunted object title usage**
  - **Validates: Requirements 12.2**

- [x] 14.5 Update room descriptions to haunted theme
  - Review all commands that display room information
  - Replace original room descriptions with spooky versions
  - Ensure consistency with room data JSON
  - Test room description display
  - _Requirements: 12.3_

- [x] 14.6 Write property test for spooky room descriptions
  - **Property 50: Spooky room descriptions**
  - **Validates: Requirements 12.3**

- [x] 14.7 Ensure haunted vocabulary in feedback messages
  - Review all command feedback messages
  - Replace generic terms with haunted theme vocabulary
  - Maintain consistent tone across all messages
  - Test vocabulary consistency
  - _Requirements: 12.4_

- [ ] 14.8 Write property test for haunted vocabulary
  - **Property 51: Haunted vocabulary consistency**
  - **Validates: Requirements 12.4**

- [ ] 14.9 Update game element terminology
  - Review all references to game elements (items, locations, actions)
  - Replace with haunted theme terminology
  - Ensure consistency across all commands
  - Test terminology usage
  - _Requirements: 12.5_

- [ ] 14.10 Write property test for haunted terminology
  - **Property 52: Haunted terminology consistency**
  - **Validates: Requirements 12.5**

- [ ] 15. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Integration testing and polish
- [ ] 16.1 Run full test suite
  - Execute all unit tests
  - Execute all property tests
  - Execute all integration tests
  - Fix any failing tests

- [ ] 16.2 Test command sequences
  - Test common command combinations
  - Test puzzle solutions
  - Test edge cases
  - Verify state consistency

- [ ] 16.3 Performance testing
  - Test command execution speed
  - Test property test execution time
  - Optimize slow operations
  - Ensure acceptable performance

- [ ] 16.4 User acceptance testing
  - Test with sample gameplay scenarios
  - Verify all commands work as expected
  - Check for usability issues
  - Gather feedback

- [ ] 16.5 Bug fixes and polish
  - Fix any discovered bugs
  - Improve error messages
  - Enhance descriptions
  - Final code review

- [ ] 16.6 Documentation updates
  - Update API documentation
  - Update command reference
  - Update testing documentation
  - Update deployment guide
