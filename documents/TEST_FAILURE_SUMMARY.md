# Test Failure Summary Report
**Date**: 2025-12-04  
**Total Tests**: 606  
**Passed**: 547 (90.3%)  
**Failed**: 58 (9.6%)  
**Skipped**: 1 (0.2%)

---

## Critical Issues (Must Fix Before Commit)

### 1. GameState Missing Methods (7 failures)
**Issue**: `GameState` object missing `calculate_score()` method

**Affected Tests**:
- `test_properties_utility_commands.py::test_version_command_properties`
- `test_properties_utility_commands.py::test_version_command_information_types`
- `test_properties_utility_commands.py::test_diagnose_command_properties`
- `test_properties_utility_commands.py::test_diagnose_command_game_states`
- `test_properties_utility_commands.py::test_utility_commands_edge_cases` (partial)

**Error**:
```python
AttributeError: 'GameState' object has no attribute 'calculate_score'
```

**Location**: `game_engine.py:5718` and `game_engine.py:5763`

**Fix Required**: Add `calculate_score()` method to `GameState` class or change code to use `state.score` directly.

---

### 2. GameObject Missing Attribute (5 failures)
**Issue**: `GameObject` object missing `description` attribute

**Affected Tests**:
- `test_properties_utility_commands.py::test_utility_commands_state_consistency`
- `test_properties_utility_commands.py::test_utility_commands_edge_cases` (partial)
- `test_properties_utility_commands.py::test_utility_commands_sanity_integration`
- `test_properties_utility_commands.py::test_find_command_properties`
- `test_properties_utility_commands.py::test_find_command_search_targets`

**Error**:
```python
AttributeError: 'GameObject' object has no attribute 'description'
```

**Location**: `game_engine.py:5554` in `handle_find()` method

**Fix Required**: Change `item.description` to correct attribute name (likely `item.description_spooky` or similar).

---

### 3. Command Parser Issues (6 failures)

#### 3a. LOOK Command Parsing
**Issue**: `"look"` parsed as `EXAMINE` instead of `LOOK`

**Affected Tests**:
- `test_command_parser.py::TestUtilityCommands::test_look`

**Fix Required**: Add `LOOK` as separate command from `EXAMINE`, or update test expectations.

#### 3b. QUIT Command Not Recognized
**Issue**: `"quit"` parsed as `UNKNOWN` instead of `QUIT`

**Affected Tests**:
- `test_command_parser.py::TestUtilityCommands::test_quit`
- `test_command_parser.py::TestUtilityCommands::test_quit_synonyms`

**Fix Required**: Add `QUIT` command to parser vocabulary.

#### 3c. MOVE Command Conflicts with GO
**Issue**: `"move rug"` parsed as `GO` instead of `MOVE`

**Affected Tests**:
- `test_command_parser.py::TestObjectCommands::test_move_object`
- `test_command_parser.py::TestObjectCommands::test_move_synonyms`

**Fix Required**: Distinguish between `MOVE <object>` (manipulate) and `GO <direction>` (navigate).

#### 3d. LOOK AT Parsing
**Issue**: `"look at mailbox"` sets object to `"at mailbox"` instead of `"mailbox"`

**Affected Tests**:
- `test_command_parser.py::TestObjectCommands::test_look_at_object`

**Fix Required**: Strip preposition "at" from object name.

---

### 4. Method Signature Issues (12 failures)

#### 4a. handle_stand() Signature
**Issue**: Tests calling `handle_stand(game_state)` but method expects different signature

**Affected Tests**:
- `test_movement_new.py::TestStandCommand::test_stand_command_from_sitting`
- `test_movement_new.py::TestStandCommand::test_stand_command_from_lying`
- `test_movement_new.py::TestStandCommand::test_stand_command_already_standing`
- `test_movement_new.py::TestStandCommand::test_stand_command_low_sanity`
- `test_properties_movement.py::test_stand_command_properties`
- `test_properties_movement.py::test_stand_command_position_states`

**Error**:
```python
TypeError: GameEngine.handle_stand() missing 1 required positional argument: 'state'
```

**Fix Required**: Check method signature - likely `handle_stand(self, state)` but tests calling incorrectly.

#### 4b. handle_swim() Signature
**Issue**: Tests passing too many arguments

**Affected Tests**:
- `test_movement_new.py::TestMovementCommandsIntegration::test_stand_swim_sequence`

**Error**:
```python
TypeError: GameEngine.handle_swim() takes 2 positional arguments but 3 were given
```

**Fix Required**: Tests calling `handle_swim(game_engine, game_state)` but should be `handle_swim(game_state)`.

#### 4c. handle_follow() Signature
**Issue**: Tests passing too many arguments

**Affected Tests**:
- `test_movement_new.py::TestMovementCommandsIntegration::test_movement_state_consistency`

**Error**:
```python
TypeError: GameEngine.handle_follow() takes 3 positional arguments but 4 were given
```

**Fix Required**: Tests calling with extra `game_engine` argument.

---

### 5. World Data Not Loaded (10 failures)
**Issue**: Tests in `test_movement_new.py` not loading world data before testing

**Affected Tests**:
- `test_movement_new.py::TestBackCommand::test_back_command_with_history`
- `test_movement_new.py::TestBackCommand::test_back_command_no_history`
- `test_movement_new.py::TestBackCommand::test_back_command_low_sanity`
- `test_movement_new.py::TestFollowCommand::test_follow_creature_in_room`
- `test_movement_new.py::TestFollowCommand::test_follow_non_creature`
- `test_movement_new.py::TestFollowCommand::test_follow_creature_not_in_room`
- `test_movement_new.py::TestFollowCommand::test_follow_command_low_sanity`
- `test_movement_new.py::TestSwimCommand::test_swim_command_in_water`
- `test_movement_new.py::TestSwimCommand::test_swim_command_in_deep_dangerous_water`
- `test_movement_new.py::TestSwimCommand::test_swim_command_no_water`
- `test_movement_new.py::TestSwimCommand::test_swim_command_low_sanity`
- `test_movement_new.py::TestMovementCommandsIntegration::test_back_follow_sequence`
- `test_properties_movement.py::test_back_command_no_history`
- `test_properties_movement.py::test_back_command_low_sanity`
- `test_properties_movement.py::test_follow_creature_properties`
- `test_properties_movement.py::test_follow_non_creature`
- `test_properties_movement.py::test_swim_command_properties`
- `test_properties_movement.py::test_movement_state_consistency`

**Error**:
```python
ActionResult(success=False, message='An error occurred: World data not loaded. Call load_from_json() first.')
```

**Fix Required**: Add `world_data` fixture to `test_movement_new.py` or ensure game_engine fixture loads world data.

---

### 6. Error Message Assertion Failures (8 failures)
**Issue**: Tests expecting specific error message text, but actual messages differ

#### 6a. Unknown Command Message
**Test**: `test_game_engine.py::TestCommandExecution::test_execute_unknown_command`

**Expected**: `"don't understand"`  
**Actual**: `"I don't know what 'something' is."`

#### 6b. Unimplemented Command Message
**Test**: `test_game_engine.py::TestCommandExecution::test_execute_unimplemented_command`

**Expected**: `"not yet implemented"`  
**Actual**: `"What stirs your anger in this haunted place?"`

#### 6c. Object Not in Room
**Test**: `test_game_engine.py::TestObjectTakeDrop::test_take_object_not_in_room`

**Expected**: `"don't see"`  
**Actual**: `"The shadows reveal no nonexistent_object in this forsaken place."`

#### 6d. Already Have Object
**Test**: `test_game_engine.py::TestObjectTakeDrop::test_take_object_already_in_inventory`

**Expected**: `"already have"`  
**Actual**: `"The cursed object already weighs heavy in your possession."`

#### 6e. Don't Have Object
**Test**: `test_game_engine.py::TestObjectTakeDrop::test_drop_object_not_in_inventory`

**Expected**: `"don't have"`  
**Actual**: `"Your trembling hands find no such cursed thing among your possessions."`

**Fix Required**: Update test assertions to match actual haunted-themed error messages, or update error messages to include expected keywords.

---

### 7. Property Test Failures (10 failures)

#### 7a. Missing Object/Parameter Messages
**Tests**:
- `test_properties_engine.py::test_incorrect_usage_guidance`
- `test_properties_engine.py::test_missing_object_messages`
- `test_properties_engine.py::test_impossible_action_explanations`
- `test_properties_engine.py::test_missing_parameter_prompts`
- `test_properties_error_handling.py::test_unimplemented_command_messages`

**Issue**: Tests checking for specific error message patterns that don't match actual implementation.

#### 7b. Object Manipulation Commands
**Tests**:
- `test_properties_object_manipulation.py::test_move_command_directions`
- `test_properties_object_manipulation.py::test_raise_command_properties`
- `test_properties_object_manipulation.py::test_lower_command_properties`
- `test_properties_object_manipulation.py::test_slide_command_properties`

**Issue**: Commands may not be implemented or tests expect different behavior.

#### 7c. Skip Command
**Tests**:
- `test_properties_final_utilities.py::test_skip_command_properties`
- `test_properties_final_utilities.py::test_skip_command_time_effects`

**Issue**: SKIP command may not be implemented.

---

### 8. Integration Test Failure (1 failure)
**Test**: `test_game_flow.py::TestPuzzleSolving::test_rug_trap_door_puzzle`

**Issue**: Complete puzzle workflow not working as expected.

**Fix Required**: Debug the rug/trap door puzzle sequence to identify where it breaks.

---

## Summary by Category

| Category | Count | Priority |
|----------|-------|----------|
| Missing GameState methods | 7 | **CRITICAL** |
| Missing GameObject attributes | 5 | **CRITICAL** |
| Command parser issues | 6 | **HIGH** |
| Method signature mismatches | 12 | **HIGH** |
| World data not loaded | 18 | **HIGH** |
| Error message assertions | 8 | **MEDIUM** |
| Property test failures | 10 | **MEDIUM** |
| Integration test failures | 1 | **MEDIUM** |

---

## Recommended Fix Order

### Phase 1: Critical Fixes (Must Fix)
1. **Add `calculate_score()` to GameState** (7 tests)
2. **Fix GameObject.description attribute** (5 tests)
3. **Fix world data loading in test_movement_new.py** (18 tests)

**Impact**: Fixes 30 failures (51.7% of all failures)

### Phase 2: High Priority Fixes
4. **Fix method signatures in test_movement_new.py** (12 tests)
5. **Fix command parser issues** (6 tests)
   - Add QUIT command
   - Fix LOOK vs EXAMINE
   - Fix MOVE vs GO
   - Fix "look at" parsing

**Impact**: Fixes 18 more failures (total 48/58 = 82.8%)

### Phase 3: Medium Priority Fixes
6. **Update error message assertions** (8 tests)
7. **Review property test expectations** (10 tests)
8. **Debug rug/trap door puzzle** (1 test)

**Impact**: Fixes remaining 10 failures (100%)

---

## Next Steps

1. **Run Phase 1 fixes first** - these are blocking many tests
2. **Re-run test suite** after each phase to verify fixes
3. **Update checklist** as issues are resolved
4. **Document any intentional behavior differences** in tests

---

## Test Execution Command

```bash
# Run all tests
pytest tests/ -v

# Run specific failing test file
pytest tests/unit/test_movement_new.py -v

# Run specific test
pytest tests/unit/test_game_engine.py::TestCommandExecution::test_execute_unknown_command -v

# Run with more detail
pytest tests/ -vv --tb=short
```

---

**Status**: Ready for fixes  
**Estimated Fix Time**: 2-4 hours  
**Blocker for Commit**: Yes - must fix critical issues before committing
