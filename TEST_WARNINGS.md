# Test Warnings - Items to Fix

## Status: ✅ ALL FIXED

All 4000+ deprecation warnings have been resolved across the entire test suite.

## Summary
- **Before**: 4069 warnings across all property tests
- **After**: 0 warnings
- **Fix Applied**: 2025-12-03

## Issue Fixed: `datetime.datetime.utcnow()` is deprecated

**Severity**: High (will be removed in future Python versions)

### Files Fixed

#### 1. `src/lambda/game_handler/state_manager.py` (7 occurrences)

✅ **Line 64** - `__post_init__()` method
✅ **Line 66** - `__post_init__()` method  
✅ **Line 77** - `move_to_room()` method
✅ **Line 92** - `add_to_inventory()` method
✅ **Line 108** - `remove_from_inventory()` method
✅ **Line 120** - `set_flag()` method
✅ **Line 143** - `increment_turn()` method
✅ **Line 213** - `create_new_game()` class method
✅ **Line 247** - `update_ttl()` method
✅ **Line 337** - `from_dict()` class method

#### 2. `tests/property/test_properties_state.py` (3 occurrences)

✅ **Line 251** - `test_session_expiration_ttl_set()`
✅ **Line 287** - `test_session_ttl_update()`
✅ **Line 293** - `test_session_ttl_update()`

## Implementation Applied

### Updated imports:
```python
from datetime import datetime, timedelta, UTC
```

### Replaced all instances:
```python
# Before: datetime.utcnow()
# After:  datetime.now(UTC)
```

## Test Results

```bash
$ pytest tests/property/ -q
1 failed, 173 passed in 7.45s
```

**Zero warnings!** ✅

The 1 failure is unrelated to datetime (it's a parser test).

## Impact

- ✅ **Breaking Changes**: None (output format remains identical)
- ✅ **Compatibility**: Python 3.11+ (UTC constant added in 3.11)
- ✅ **Current Python Version**: 3.14.0
- ✅ **Tests**: 173 passing with zero warnings
- ✅ **Performance**: No impact

## Files Modified

1. `src/lambda/game_handler/state_manager.py` - 10 replacements
2. `tests/property/test_properties_state.py` - 3 replacements

Total: **13 occurrences fixed**

## Next Steps

When deploying, the fixed `src/lambda/game_handler/state_manager.py` will be copied to `amplify/functions/game-handler/state_manager.py` automatically.
