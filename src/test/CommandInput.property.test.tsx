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

  it('should not submit empty or whitespace-only commands', () => {
    fc.assert(
      fc.property(
        fc.array(fc.constantFrom('', '   ', '\t', '\n', '  \t  \n  '), { minLength: 1, maxLength: 10 }),
        (emptyCommands) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            emptyCommands.forEach((command) => {
              fireEvent.change(input, { target: { value: command } });
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
            });
            expect(onSubmit).not.toHaveBeenCalled();
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should trim whitespace from commands before submission', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            command: fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
            whitespace: fc.constantFrom('  ', '\t', '   \t   '),
          }),
          { minLength: 1, maxLength: 20 }
        ),
        (commandData) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            commandData.forEach(({ command, whitespace }) => {
              const paddedCommand = `${whitespace}${command}${whitespace}`;
              fireEvent.change(input, { target: { value: paddedCommand } });
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
              expect(onSubmit).toHaveBeenCalledWith(command.trim());
            });
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should navigate command history with up arrow key', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), { minLength: 2, maxLength: 10 }),
        (commands) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            commands.forEach((command) => {
              fireEvent.change(input, { target: { value: command } });
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
            });

            for (let i = commands.length - 1; i >= 0; i--) {
              fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
              expect(input.value).toBe(commands[i].trim());
            }

            fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
            expect(input.value).toBe(commands[0].trim());
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should navigate command history with down arrow key', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), { minLength: 2, maxLength: 10 }),
        (commands) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            commands.forEach((command) => {
              fireEvent.change(input, { target: { value: command } });
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
            });

            for (let i = 0; i < commands.length; i++) {
              fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
            }

            for (let i = 1; i < commands.length; i++) {
              fireEvent.keyDown(input, { key: 'ArrowDown', code: 'ArrowDown' });
              expect(input.value).toBe(commands[i].trim());
            }

            fireEvent.keyDown(input, { key: 'ArrowDown', code: 'ArrowDown' });
            expect(input.value).toBe('');
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should disable input when disabled prop is true', () => {
    const onSubmit = vi.fn();
    const { getByRole } = render(<CommandInput onSubmit={onSubmit} disabled={true} />);
    const input = getByRole('textbox') as HTMLInputElement;
    expect(input.disabled).toBe(true);
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it('should not submit commands when disabled', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0), { minLength: 1, maxLength: 20 }),
        (commands) => {
          const onSubmit = vi.fn();
          const { getByRole, rerender, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            fireEvent.change(input, { target: { value: commands[0] } });
            expect(input.value).toBe(commands[0]);
            rerender(<CommandInput onSubmit={onSubmit} disabled={true} />);
            fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
            expect(onSubmit).not.toHaveBeenCalled();
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should reset history index when user types', () => {
    fc.assert(
      fc.property(
        fc.record({
          history: fc.array(fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0), { minLength: 2, maxLength: 5 }),
          newInput: fc.string({ minLength: 1, maxLength: 50 }),
        }),
        ({ history, newInput }) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            history.forEach((command) => {
              fireEvent.change(input, { target: { value: command } });
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
            });

            fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
            expect(input.value).toBe(history[history.length - 1].trim());
            fireEvent.change(input, { target: { value: newInput } });
            expect(input.value).toBe(newInput);
            fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
            expect(input.value).toBe(history[history.length - 1].trim());
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should not add duplicate consecutive commands to history', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 100 }).filter(s => s.trim().length > 0),
        fc.integer({ min: 2, max: 5 }),
        (command, repeatCount) => {
          const onSubmit = vi.fn();
          const { getByRole, unmount } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);

          try {
            const input = getByRole('textbox') as HTMLInputElement;
            for (let i = 0; i < repeatCount; i++) {
              fireEvent.change(input, { target: { value: command } });
              fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
            }

            fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
            expect(input.value).toBe(command.trim());
            fireEvent.keyDown(input, { key: 'ArrowUp', code: 'ArrowUp' });
            expect(input.value).toBe(command.trim());
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should have proper ARIA attributes for accessibility', () => {
    const onSubmit = vi.fn();
    
    // Test enabled state
    const { getByRole: getByRoleEnabled, unmount: unmountEnabled } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);
    const enabledInput = getByRoleEnabled('textbox') as HTMLInputElement;
    expect(enabledInput.getAttribute('aria-label')).toBe('Game command input');
    expect(enabledInput.getAttribute('aria-disabled')).toBe('false');
    unmountEnabled();

    // Test disabled state
    const { getByRole: getByRoleDisabled, unmount: unmountDisabled } = render(<CommandInput onSubmit={onSubmit} disabled={true} />);
    const disabledInput = getByRoleDisabled('textbox') as HTMLInputElement;
    expect(disabledInput.getAttribute('aria-label')).toBe('Game command input');
    expect(disabledInput.getAttribute('aria-disabled')).toBe('true');
    unmountDisabled();
  });

  it('should have autocomplete and spellcheck disabled', () => {
    const onSubmit = vi.fn();
    const { getByRole } = render(<CommandInput onSubmit={onSubmit} disabled={false} />);
    const input = getByRole('textbox') as HTMLInputElement;
    expect(input.getAttribute('autocomplete')).toBe('off');
    expect(input.getAttribute('spellcheck')).toBe('false');
  });
});
