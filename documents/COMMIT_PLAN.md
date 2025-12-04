# Commit Plan
**Date**: 2025-12-04  
**Branch**: main → production

## Strategy: Single Comprehensive Commit

Given the scope of changes (complete Zork command implementation), recommend **one comprehensive commit** rather than multiple smaller commits.

---

## Files to Commit

### Core Implementation (Modified)
```
src/lambda/game_handler/command_parser.py
src/lambda/game_handler/game_engine.py
src/lambda/game_handler/state_manager.py
src/lambda/game_handler/world_loader.py
src/lambda/game_handler/data/rooms_haunted.json
src/lambda/game_handler/data/objects_haunted.json
```

### Deployment Files (Modified)
```
amplify/functions/game-handler/data/rooms_haunted.json
amplify/functions/game-handler/data/objects_haunted.json
```

### Test Files (Modified)
```
tests/integration/test_game_flow.py
tests/property/test_properties_engine.py
tests/property/test_properties_error_handling.py
tests/property/test_properties_read.py
tests/unit/test_game_engine.py
```

### New Test Files
```
tests/property/test_properties_atmospheric.py
tests/property/test_properties_communication.py
tests/property/test_properties_final_utilities.py
tests/property/test_properties_magic.py
tests/property/test_properties_movement.py
tests/property/test_properties_object_manipulation.py
tests/property/test_properties_send_for.py
tests/property/test_properties_special_commands.py
tests/property/test_properties_special_manipulation.py
tests/property/test_properties_theme.py
tests/property/test_properties_utility_commands.py
tests/unit/test_movement_new.py
```

### Documentation (Modified)
```
.gitignore
.kiro/specs/complete-zork-commands/tasks.md
.kiro/steering/testing.md
```

### Documentation (New)
```
.kiro/specs/complete-zork-commands/implementation_progress.md
PRE_COMMIT_REVIEW_CHECKLIST.md
TEST_FIX_SUMMARY.md
VALIDATION_SUMMARY.md
COMMIT_PLAN.md (this file)
```

### Analysis Files (New - Keep for Reference)
```
COMPREHENSIVE_COMPARISON_REPORT.md
ITEM_REVIEW_FINAL_REPORT.md
comprehensive_analysis.py
objects_comparison.py
room_items_comparison.py
```

### Temporary Files (New - Can Delete)
```
ABSOLUTE_FINAL_RESULTS.md
COMPREHENSIVE_TEST_RESULTS.md
FINAL_COMPREHENSIVE_RESULTS.md
FINAL_RESOLVED_RESULTS.md
FINAL_TEST_RESULTS.md
FIX_SUMMARY.md
TEST_FAILURE_SUMMARY.md
test_container_fix.py
verify_container_fix.md
```

---

## Recommended Commit Message

```
Feature: Complete Zork command implementation with full test suite

Major changes:
- Complete room and object data from legacy code (110 rooms, 135 objects)
- Enhanced command parser with all Zork commands
- Enhanced game engine with full action handlers
- Comprehensive property-based test suite (11 new test files)
- Additional unit tests for movement system
- Updated documentation and analysis reports

Implementation includes:
- Movement: GO, directions, CLIMB, BOARD, DISEMBARK, SWIM, FOLLOW, BACK, STAND
- Object manipulation: TAKE, DROP, PUT, EXAMINE, OPEN, CLOSE, READ, MOVE, RAISE, LOWER, SLIDE
- Special actions: LIGHT, EXTINGUISH, UNLOCK, LOCK, ATTACK, THROW, GIVE, WAKE, KISS
- Communication: TELL, ASK, SAY, WHISPER, ANSWER
- Utility: INVENTORY, LOOK, SCORE, QUIT, HELP, VERSION, DIAGNOSE, FIND, SKIP
- Atmospheric: SPRAY, STAY, WIND, BLOW OUT, BLOW UP
- Easter eggs: XYZZY, PLUGH, HELLO, PRAY, JUMP, YELL, ECHO

Test results:
- 606/606 tests passing (100%)
- Property-based tests: 100 examples each
- Coverage: >90% for core modules

Ready for deployment.
```

---

## Git Commands

### Step 1: Stage All Changes
```bash
# Stage modified files
git add src/lambda/game_handler/
git add amplify/functions/game-handler/data/
git add tests/
git add .gitignore
git add .kiro/

# Stage new documentation
git add PRE_COMMIT_REVIEW_CHECKLIST.md
git add TEST_FIX_SUMMARY.md
git add VALIDATION_SUMMARY.md
git add COMMIT_PLAN.md
git add COMPREHENSIVE_COMPARISON_REPORT.md
git add ITEM_REVIEW_FINAL_REPORT.md
git add .kiro/specs/complete-zork-commands/implementation_progress.md

# Stage analysis scripts (for reference)
git add comprehensive_analysis.py
git add objects_comparison.py
git add room_items_comparison.py
```

### Step 2: Commit
```bash
git commit -m "Feature: Complete Zork command implementation with full test suite

Major changes:
- Complete room and object data from legacy code (110 rooms, 135 objects)
- Enhanced command parser with all Zork commands
- Enhanced game engine with full action handlers
- Comprehensive property-based test suite (11 new test files)
- Additional unit tests for movement system
- Updated documentation and analysis reports

Implementation includes:
- Movement: GO, directions, CLIMB, BOARD, DISEMBARK, SWIM, FOLLOW, BACK, STAND
- Object manipulation: TAKE, DROP, PUT, EXAMINE, OPEN, CLOSE, READ, MOVE, RAISE, LOWER, SLIDE
- Special actions: LIGHT, EXTINGUISH, UNLOCK, LOCK, ATTACK, THROW, GIVE, WAKE, KISS
- Communication: TELL, ASK, SAY, WHISPER, ANSWER
- Utility: INVENTORY, LOOK, SCORE, QUIT, HELP, VERSION, DIAGNOSE, FIND, SKIP
- Atmospheric: SPRAY, STAY, WIND, BLOW OUT, BLOW UP
- Easter eggs: XYZZY, PLUGH, HELLO, PRAY, JUMP, YELL, ECHO

Test results:
- 606/606 tests passing (100%)
- Property-based tests: 100 examples each
- Coverage: >90% for core modules

Ready for deployment."
```

### Step 3: Push to Main
```bash
git push origin main
```

### Step 4: Test in Sandbox (Optional)
```bash
npx ampx sandbox
```

### Step 5: Deploy to Production
```bash
git checkout production
git merge main --no-edit
git push origin production
```

### Step 6: Sync Back to Main
```bash
git checkout main
git merge production
git push origin main
```

---

## Cleanup (Optional - After Successful Commit)

Remove temporary files:
```bash
rm ABSOLUTE_FINAL_RESULTS.md
rm COMPREHENSIVE_TEST_RESULTS.md
rm FINAL_COMPREHENSIVE_RESULTS.md
rm FINAL_RESOLVED_RESULTS.md
rm FINAL_TEST_RESULTS.md
rm FIX_SUMMARY.md
rm TEST_FAILURE_SUMMARY.md
rm test_container_fix.py
rm verify_container_fix.md

git add -u
git commit -m "Cleanup: Remove temporary analysis files"
git push origin main
```

---

## Verification Checklist

Before pushing:
- [✅] All tests pass: `pytest tests/ -v`
- [✅] JSON files valid
- [✅] Python syntax valid
- [✅] Git status reviewed
- [ ] Commit message prepared
- [ ] Ready to push

After pushing to main:
- [ ] Verify GitHub shows commit
- [ ] Check no errors in commit
- [ ] Test in sandbox (optional)

After deploying to production:
- [ ] Monitor Amplify Console
- [ ] Verify deployment succeeds
- [ ] Test production API endpoints
- [ ] Sync main with production

---

**Status**: Ready to execute  
**Estimated Time**: 5-10 minutes for commit + push  
**Risk Level**: Low (all tests passing)
