# Testing Standards and Practices

## Overview

This project uses a comprehensive testing strategy combining unit tests, property-based tests, integration tests, and end-to-end tests. All tests follow strict conventions to ensure consistency, maintainability, and thorough coverage.

## Test Organization

### Directory Structure

```
tests/
├── unit/                         # Unit tests for individual components
│   ├── test_command_parser.py
│   ├── test_game_engine.py
│   ├── test_sanity_system.py
│   └── test_world_loader.py
├── property/                     # Property-based tests (Hypothesis)
│   ├── test_properties_parser.py
│   ├── test_properties_engine.py
│   ├── test_properties_sanity.py
│   └── test_properties_state.py
├── integration/                  # End-to-end game flow tests
│   └── test_game_flow.py
├── e2e/                          # Playwright browser tests
│   ├── mailbox-parchment.spec.ts
│   └── reverse-chronological-order.spec.ts
└── conftest.py                   # Shared pytest configuration

src/test/                         # Frontend tests (React/TypeScript)
├── CommandInput.property.test.tsx
├── GameApiClient.property.test.ts
├── RoomImage.property.test.tsx
└── setup.ts                      # Vitest configuration
```

## Backend Testing (Python)

### Test Framework

- **Unit Tests**: pytest
- **Property-Based Tests**: Hypothesis library
- **Minimum Iterations**: 100 examples per property test (`@settings(max_examples=100)`)
- **Test Command**: `pytest` (from project root)
- **Coverage**: `pytest --cov=src tests/`

### Import Pattern (CRITICAL)

All Python test files MUST include this import pattern at the top:

```python
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler'))

import pytest
from hypothesis import given, strategies as st, settings
# ... other imports
```

**Why**: Tests are in `tests/` but source code is in `src/lambda/game_handler/`. This pattern ensures imports work correctly regardless of where tests are run from.

### Test Tagging Convention

Every property-based test MUST include a feature tag and property number in the docstring:

```python
# Feature: game-backend-api, Property 4: Command parsing determinism
@settings(max_examples=100)
@given(command=st.text(min_size=1, max_size=100))
def test_command_parsing_determinism(command):
    """
    For any command string, parsing it multiple times should always produce the same result.
    
    **Validates: Requirements 2.2**
    
    This property ensures that command parsing is deterministic and consistent,
    which is critical for reliable game behavior.
    """
```

**Format**:
- First line: `# Feature: {feature-name}, Property {number}: {property-description}`
- Docstring first line: Natural language property statement starting with "For any..."
- `**Validates: Requirements X.Y**`: Links to requirements document
- Additional explanation of why this property matters

### Property-Based Test Structure

#### 1. Property Statement Format

All property tests should follow this structure:

```python
@settings(max_examples=100)
@given(
    param1=st.strategy1(),
    param2=st.strategy2()
)
def test_property_name(param1, param2):
    """
    For any [input conditions], [expected behavior] should [always/never] [outcome].
    
    **Validates: Requirements X.Y**
    
    [Explanation of why this property is important]
    """
    # Arrange: Set up test conditions
    # Act: Perform operation
    # Assert: Verify property holds
```

#### 2. Custom Strategies

Create composite strategies for complex test data:

```python
@st.composite
def valid_room_and_direction(draw, world_data):
    """
    Generate a valid room ID and a direction from that room.
    
    Returns tuple of (room_id, direction, target_room_id) where the exit exists.
    """
    room_ids = list(world_data.rooms.keys())
    room_id = draw(st.sampled_from(room_ids))
    room = world_data.get_room(room_id)
    
    if room.exits:
        direction = draw(st.sampled_from(list(room.exits.keys())))
        target_room_id = room.exits[direction]
        return (room_id, direction, target_room_id)
    else:
        return (room_id, None, None)
```

**Best Practices**:
- Use `@st.composite` decorator for complex data generation
- Document what the strategy generates
- Use `assume(False)` to skip invalid examples
- Return tuples or named tuples for multiple values

#### 3. Fixtures for Shared Resources

Use pytest fixtures for expensive setup:

```python
@pytest.fixture(scope="module")
def world_data():
    """Load world data once for all tests."""
    world = WorldData()
    data_dir = os.path.join(os.path.dirname(__file__), '../../src/lambda/game_handler/data')
    world.load_from_json(data_dir)
    return world

@pytest.fixture(scope="module")
def game_engine(world_data):
    """Create game engine instance."""
    return GameEngine(world_data)

@pytest.fixture
def fresh_state():
    """Create a fresh game state for each test."""
    return GameState.create_new_game()
```

**Scopes**:
- `scope="module"`: Share across all tests in file (for expensive setup like loading world data)
- `scope="function"` (default): Create fresh for each test (for mutable state)

#### 4. Property Categories

**Invariant Properties** (things that should always be true):
```python
def test_sanity_bounds(initial_sanity, sanity_changes):
    """For any sequence of sanity changes, sanity should always stay in [0, 100]."""
    # Test that bounds are never violated
```

**Round-Trip Properties** (operations that should be reversible):
```python
def test_take_then_drop_returns_object_to_room(data):
    """For any game state, taking an object and dropping it should return it to the room."""
    # Take object -> Drop object -> Verify back in room
```

**Idempotence Properties** (repeating operation has same effect):
```python
def test_command_parsing_determinism(command):
    """For any command string, parsing it multiple times should produce the same result."""
    # Parse 3 times -> All results identical
```

**Conservation Properties** (totals are preserved):
```python
def test_inventory_reflects_take_drop_operations(data):
    """For any sequence of take/drop, inventory should match expected state."""
    # Track expected inventory -> Verify actual matches
```

**Ordering Properties** (operations maintain order):
```python
def test_sanity_loss_decreases(initial_sanity, loss_amount):
    """For any sanity value, applying loss should never increase sanity."""
    # old_sanity >= new_sanity
```

### Unit Test Structure

Unit tests should be organized into classes by feature:

```python
class TestMovementCommands:
    """Test parsing of movement commands."""
    
    def test_explicit_go_north(self):
        """Test 'go north' command."""
        parser = CommandParser()
        result = parser.parse("go north")
        
        assert result.verb == "GO"
        assert result.direction == "NORTH"
    
    def test_implicit_north(self):
        """Test 'north' command (implicit GO)."""
        parser = CommandParser()
        result = parser.parse("north")
        
        assert result.verb == "GO"
        assert result.direction == "NORTH"
```

**Best Practices**:
- Group related tests in classes
- Use descriptive class names: `TestMovementCommands`, `TestObjectCommands`, `TestUtilityCommands`
- One assertion concept per test (but multiple asserts for related checks are OK)
- Use descriptive test names that explain what is being tested

### Integration Test Structure

Integration tests verify complete workflows:

```python
class TestCompleteGameFlow:
    """
    Integration test for complete game flow.
    
    Tests: New game → Move → Take object → Examine → Drop → Score
    Verifies state persistence across commands.
    
    Requirements: 1.1, 2.1, 3.2, 4.2, 4.3, 13.1
    """
    
    def test_complete_game_flow(self, game_engine, command_parser, fresh_state, world_data):
        """Test a complete game flow from start to finish."""
        # Step 1: Verify initial game state
        assert fresh_state.session_id is not None
        assert fresh_state.current_room == "west_of_house"
        
        # Step 2: Move to different room
        parsed_command = command_parser.parse("go north")
        result = game_engine.execute_command(parsed_command, fresh_state)
        assert result.success is True
        
        # ... more steps
```

**Best Practices**:
- Document the complete workflow in class docstring
- List all requirements being validated
- Use numbered steps with comments
- Verify state at each step
- Test realistic user scenarios

### Hypothesis Settings and Health Checks

```python
from hypothesis import settings, HealthCheck

# Suppress health checks for function-scoped fixtures
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(st.sampled_from(['mailbox', 'leaflet', 'lamp']))
def test_with_fixture(game_engine, object_name):
    """Test that uses a fixture with Hypothesis."""
    pass
```

**When to suppress health checks**:
- Using function-scoped fixtures with `@given` (Hypothesis warns about this)
- Tests that intentionally take longer to run
- Tests with complex setup that can't be moved to module scope

**Never suppress** without understanding why the health check is failing!

## Frontend Testing (React/TypeScript)

### Test Framework

- **Test Framework**: Vitest with React Testing Library
- **Property-Based Tests**: fast-check library
- **Minimum Iterations**: 100 runs per property (`{ numRuns: 100 }`)
- **Test Command**: `npm test` (includes `--run` flag automatically)
- **Watch Mode**: `npm run test:watch`
- **UI Mode**: `npm run test:ui`

### Test File Naming

- Property tests: `*.property.test.tsx` or `*.property.test.ts`
- Unit tests: `*.test.tsx` or `*.test.ts`
- Location: `src/test/` directory

### Property Test Structure (Frontend)

```typescript
/**
 * Property-Based Tests for CommandInput Component
 * Feature: grimoire-frontend
 * 
 * Tests input state after completion
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, fireEvent, cleanup } from '@testing-library/react';
import * as fc from 'fast-check';
import CommandInput from '../components/CommandInput';

describe('CommandInput Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  /**
   * Property 7: Input State After Completion
   * For any completed command, the input field should be re-enabled and cleared
   * Validates: Requirements 3.4
   */
  it('Property 7: Input State After Completion - should clear input after submission', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
          { minLength: 1, maxLength: 30 }
        ),
        (commands) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(
            <CommandInput onSubmit={onSubmit} disabled={false} />
          );

          try {
            const input = getByRole('textbox') as HTMLInputElement;

            commands.forEach((command) => {
              fireEvent.change(input, { target: { value: command } });
              expect(input.value).toBe(command);
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
              expect(onSubmit).toHaveBeenCalledWith(command.trim());
              expect(input.value).toBe('');
            });

            expect(onSubmit).toHaveBeenCalledTimes(commands.length);
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

**Key Patterns**:
- Always use `try/finally` with `unmount()` to prevent memory leaks
- Use `vi.fn()` for mock functions
- Clear mocks in `beforeEach`, restore in `afterEach`
- Always call `cleanup()` after each test
- Use `fc.assert()` with `fc.property()` for property tests
- Specify `{ numRuns: 100 }` for consistency with backend tests

### Test Setup File

Create `src/test/setup.ts` for shared configuration:

```typescript
/**
 * Test setup file for vitest
 * Feature: grimoire-frontend
 */

import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock environment variables
process.env.VITE_API_BASE_URL = 'http://localhost:3001';
process.env.VITE_API_TIMEOUT = '30000';

// Mock localStorage
class LocalStorageMock {
  private store: Record<string, string> = {};
  
  clear() { this.store = {}; }
  getItem(key: string) { return this.store[key] || null; }
  setItem(key: string, value: string) { this.store[key] = String(value); }
  removeItem(key: string) { delete this.store[key]; }
  get length() { return Object.keys(this.store).length; }
  key(index: number) { return Object.keys(this.store)[index] || null; }
}

global.localStorage = new LocalStorageMock() as Storage;

// Mock AWS Amplify
vi.mock('aws-amplify/data', () => ({
  generateClient: vi.fn(() => ({
    models: {
      GameSession: {
        create: vi.fn(),
        get: vi.fn(),
        update: vi.fn(),
        delete: vi.fn(),
      },
    },
    graphql: vi.fn(),
  })),
}));
```

## End-to-End Testing (Playwright)

### Test Structure

```typescript
/**
 * E2E Test: Mailbox and Parchment Interaction
 * Feature: complete-zork-commands
 * 
 * Verifies the complete workflow:
 * 1. Open the mailbox
 * 2. Take the parchment (leaflet object)
 * 3. Read the parchment
 */

import { test, expect } from '@playwright/test';

test.describe('Mailbox and Parchment Workflow', () => {
  test('should open mailbox, take parchment, and read it', async ({ page }) => {
    await page.goto('/');
    
    // Wait for the game to load
    await page.waitForSelector('.command-input', { timeout: 10000 });
    await page.waitForTimeout(3000);
    
    const input = page.locator('.command-input');
    
    // Step 1: Open the mailbox
    console.log('Step 1: Opening mailbox...');
    await input.fill('open mailbox');
    await input.press('Enter');
    await page.waitForTimeout(2000);
    
    // Verify mailbox opened
    const outputLines = page.locator('.output-line');
    const allText = await outputLines.allTextContents();
    const openResponse = allText.find(text => 
      text.toLowerCase().includes('mailbox') && 
      (text.toLowerCase().includes('open') || text.toLowerCase().includes('parchment'))
    );
    
    expect(openResponse).toBeTruthy();
    console.log('✓ Mailbox opened:', openResponse?.substring(0, 80));
    
    // ... more steps
  });
});
```

**Best Practices**:
- Document complete workflow in test description
- Use numbered steps with console.log for debugging
- Add appropriate waits between actions
- Verify each step before proceeding
- Use descriptive selectors (`.command-input`, `.output-line`)
- Test both primary and alternate object names

## Common Testing Patterns

### 1. Testing Bounds and Constraints

```python
@settings(max_examples=100)
@given(
    initial_value=st.integers(min_value=0, max_value=100),
    changes=st.lists(st.integers(min_value=-50, max_value=50), min_size=1, max_size=20)
)
def test_value_stays_in_bounds(initial_value, changes):
    """For any sequence of changes, value should stay in [0, 100]."""
    value = initial_value
    for change in changes:
        value = max(0, min(100, value + change))
        assert 0 <= value <= 100
```

### 2. Testing State Transitions

```python
@settings(max_examples=100)
@given(st.data())
def test_state_transition(data):
    """For any valid state transition, state should update correctly."""
    initial_state = create_initial_state()
    action = data.draw(valid_action_strategy())
    
    new_state = apply_action(initial_state, action)
    
    assert is_valid_state(new_state)
    assert state_changed_correctly(initial_state, new_state, action)
```

### 3. Testing Error Handling

```python
@settings(max_examples=100)
@given(invalid_input=st.text())
def test_handles_invalid_input_gracefully(invalid_input):
    """For any invalid input, system should not crash and return error."""
    result = process_input(invalid_input)
    
    # Should not raise exception
    assert result is not None
    # Should indicate failure
    assert result.success is False
    # Should provide error message
    assert len(result.message) > 0
```

### 4. Testing Serialization

```python
@settings(max_examples=100)
@given(state=game_state_strategy())
def test_serialization_round_trip(state):
    """For any game state, serialize → deserialize should preserve all fields."""
    # Serialize
    serialized = state.to_dict()
    
    # Deserialize
    restored = GameState.from_dict(serialized)
    
    # Verify all fields preserved
    assert restored.field1 == state.field1
    assert restored.field2 == state.field2
    # ... check all critical fields
```

### 5. Testing Collections

```python
@settings(max_examples=100)
@given(
    items=st.lists(st.text(min_size=1), min_size=0, max_size=20, unique=True)
)
def test_collection_operations(items):
    """For any sequence of add/remove operations, collection state should be consistent."""
    collection = []
    expected = set()
    
    for item in items:
        collection.append(item)
        expected.add(item)
    
    assert set(collection) == expected
```

## Assertion Best Practices

### Good Assertions

```python
# Specific and descriptive
assert result.success is True, f"Taking {object_id} should succeed"

# Multiple related assertions
assert object_id in state.inventory, "Object should be in inventory after taking"
assert object_id not in current_room.items, "Object should not be in room after taking"

# Bounds checking with context
assert 0 <= state.sanity <= 100, \
    f"Sanity {state.sanity} out of bounds after change {change}"
```

### Bad Assertions

```python
# Too vague
assert result  # What are we checking?

# No context on failure
assert x == y  # Why should they be equal?

# Testing implementation details
assert len(internal_cache) == 5  # Fragile, couples to implementation
```

## Test Data Management

### Fixtures and Caching

```python
# conftest.py
@pytest.fixture(autouse=True)
def clear_world_cache():
    """Clear WorldData cache before each test to ensure fresh data."""
    WorldData.clear_cache()
    yield
    WorldData.clear_cache()
```

**Why**: Ensures tests don't interfere with each other through shared cached data.

### Test Data Location

- Backend game data: `src/lambda/game_handler/data/`
- Test fixtures: `tests/conftest.py`
- Mock data: Create in test file or fixture

## Running Tests

### Backend (Python)

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_command_parser.py

# Run specific test
pytest tests/unit/test_command_parser.py::TestMovementCommands::test_explicit_go_north

# Run with coverage
pytest --cov=src tests/

# Run only property tests
pytest tests/property/

# Run with verbose output
pytest -v

# Run with print statements visible
pytest -s
```

### Frontend (React/TypeScript)

```bash
# Run all tests (includes --run flag automatically)
npm test

# Run specific test file
npm test src/test/CommandInput.property.test.tsx

# Run tests in watch mode
npm run test:watch

# Run tests with UI
npm run test:ui

# Run with coverage
npm test -- --coverage
```

### E2E (Playwright)

```bash
# Run all E2E tests
npx playwright test

# Run specific test file
npx playwright test tests/e2e/mailbox-parchment.spec.ts

# Run with UI
npx playwright test --ui

# Run in headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug
```

## Test Coverage Goals

- **Unit Tests**: 80%+ line coverage for core logic
- **Property Tests**: All critical invariants and properties
- **Integration Tests**: All major user workflows
- **E2E Tests**: Critical user paths and regressions

## Common Pitfalls to Avoid

### 1. Flaky Tests

**Bad**:
```python
# Depends on timing
time.sleep(0.1)
assert result is not None
```

**Good**:
```python
# Use proper synchronization
result = wait_for_result(timeout=5)
assert result is not None
```

### 2. Test Interdependence

**Bad**:
```python
# Test B depends on Test A running first
def test_a():
    global shared_state
    shared_state = setup()

def test_b():
    assert shared_state.value == 5  # Breaks if test_a doesn't run
```

**Good**:
```python
# Each test is independent
def test_a():
    state = setup()
    assert state.value == 5

def test_b():
    state = setup()
    assert state.value == 5
```

### 3. Over-Mocking

**Bad**:
```python
# Mock everything
mock_world = Mock()
mock_engine = Mock()
mock_parser = Mock()
# Test becomes meaningless
```

**Good**:
```python
# Only mock external dependencies
real_world = WorldData()
real_engine = GameEngine(real_world)
mock_api_client = Mock()  # External API
```

### 4. Testing Implementation Details

**Bad**:
```python
# Tests internal structure
assert len(parser._internal_cache) == 5
assert parser._parse_count == 10
```

**Good**:
```python
# Tests behavior
result = parser.parse("go north")
assert result.verb == "GO"
assert result.direction == "NORTH"
```

### 5. Unclear Test Names

**Bad**:
```python
def test_1():
def test_parser():
def test_it_works():
```

**Good**:
```python
def test_explicit_go_north():
def test_parser_handles_empty_command():
def test_sanity_stays_within_bounds():
```

## Debugging Failed Tests

### 1. Read the Assertion Message

```python
# Good assertion messages help debugging
assert result.success is True, \
    f"Expected success for command '{command}', got error: {result.message}"
```

### 2. Use Print Debugging

```bash
# Run with -s to see print statements
pytest -s tests/unit/test_command_parser.py
```

### 3. Run Single Test

```bash
# Isolate the failing test
pytest tests/unit/test_command_parser.py::test_explicit_go_north -v
```

### 4. Use Hypothesis Verbosity

```python
@settings(max_examples=100, verbosity=Verbosity.verbose)
@given(...)
def test_property(...):
    pass
```

### 5. Reproduce Hypothesis Failures

```python
# Hypothesis prints the failing example
# Use @example decorator to reproduce
@example(command="specific failing input")
@given(command=st.text())
def test_property(command):
    pass
```

## Continuous Integration

Tests should run automatically on:
- Every commit to `main` branch
- Every pull request
- Before deployment to `production` branch

**CI Configuration** (example):
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Python tests
        run: pytest --cov=src tests/
      - name: Run TypeScript tests
        run: npm test
      - name: Run E2E tests
        run: npx playwright test
```

## Summary

**Key Principles**:
1. **Consistency**: Follow established patterns for test structure and naming
2. **Clarity**: Write tests that clearly express intent and expected behavior
3. **Independence**: Each test should run independently without side effects
4. **Coverage**: Test critical paths, edge cases, and error conditions
5. **Maintainability**: Write tests that are easy to understand and modify
6. **Speed**: Keep tests fast; use fixtures and caching appropriately
7. **Reliability**: Avoid flaky tests; use proper synchronization

**Remember**: Tests are documentation. They should clearly communicate what the system does and how it should behave.
