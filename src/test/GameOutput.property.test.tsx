/**
 * Property-Based Tests for GameOutput Component
 * Feature: grimoire-frontend
 * 
 * Tests command output appending, response ordering, auto-scroll behavior, and line limits
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, waitFor } from '@testing-library/react';
import * as fc from 'fast-check';
import GameOutput from '../components/GameOutput';
import { OutputLine, MAX_OUTPUT_LINES } from '../types';

describe('GameOutput Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Property 8: Command Output Appending
   * For any submitted command, the command text should be appended to the game output area
   * Validates: Requirements 4.1
   */
  it('Property 8: Command Output Appending - should append all commands to output', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }), { minLength: 1, maxLength: 50 }),
        (commands) => {
          // Create output lines from commands
          const lines: OutputLine[] = commands.map((cmd, index) => ({
            id: `cmd-${index}`,
            type: 'command' as const,
            text: cmd,
            timestamp: Date.now() + index,
          }));

          // Render component
          const { container } = render(<GameOutput lines={lines} />);

          // Verify all commands are present in the output
          commands.forEach((cmd) => {
            const outputText = container.textContent || '';
            expect(outputText).toContain(cmd);
          });

          // Verify the number of command lines matches
          const commandElements = container.querySelectorAll('.output-line--command');
          expect(commandElements.length).toBe(commands.length);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 9: Response Output Ordering
   * For any command-response pair, the response should appear immediately after the command in the output area
   * Validates: Requirements 4.2
   */
  it('Property 9: Response Output Ordering - should maintain command-response ordering', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            command: fc.string({ minLength: 1, maxLength: 100 }),
            response: fc.string({ minLength: 1, maxLength: 200 }),
          }),
          { minLength: 1, maxLength: 30 }
        ),
        (pairs) => {
          // Create interleaved command-response lines
          const lines: OutputLine[] = [];
          pairs.forEach((pair, index) => {
            lines.push({
              id: `cmd-${index}`,
              type: 'command',
              text: pair.command,
              timestamp: Date.now() + index * 2,
            });
            lines.push({
              id: `resp-${index}`,
              type: 'response',
              text: pair.response,
              timestamp: Date.now() + index * 2 + 1,
            });
          });

          // Render component
          const { container } = render(<GameOutput lines={lines} />);

          // Get all output line elements
          const outputElements = container.querySelectorAll('.output-line');

          // Verify ordering: each command should be followed by its response
          pairs.forEach((pair, index) => {
            const cmdIndex = index * 2;
            const respIndex = index * 2 + 1;

            if (cmdIndex < outputElements.length) {
              const cmdElement = outputElements[cmdIndex];
              expect(cmdElement.textContent).toContain(pair.command);
              expect(cmdElement.classList.contains('output-line--command')).toBe(true);
            }

            if (respIndex < outputElements.length) {
              const respElement = outputElements[respIndex];
              expect(respElement.textContent).toContain(pair.response);
              expect(respElement.classList.contains('output-line--response')).toBe(true);
            }
          });

          // Verify total count
          expect(outputElements.length).toBe(pairs.length * 2);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 10: Auto-scroll Behavior
   * For any new content added to the output area, the scroll position should automatically 
   * move to show the most recent content
   * Validates: Requirements 4.3
   */
  it('Property 10: Auto-scroll Behavior - should auto-scroll to bottom on new content', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }), { minLength: 2, maxLength: 20 }),
        async (commands) => {
          // Create initial lines
          const initialLines: OutputLine[] = commands.slice(0, -1).map((cmd, index) => ({
            id: `cmd-${index}`,
            type: 'command' as const,
            text: cmd,
            timestamp: Date.now() + index,
          }));

          // Render with initial lines
          const { container, rerender } = render(<GameOutput lines={initialLines} />);

          // Get the output container
          const outputContainer = container.querySelector('.game-output') as HTMLDivElement;
          expect(outputContainer).toBeTruthy();

          // Add new line
          const newLines: OutputLine[] = [
            ...initialLines,
            {
              id: `cmd-${commands.length - 1}`,
              type: 'command' as const,
              text: commands[commands.length - 1],
              timestamp: Date.now() + commands.length,
            },
          ];

          // Rerender with new line
          rerender(<GameOutput lines={newLines} />);

          // Wait for scroll to complete
          await waitFor(() => {
            // Check if scrolled to bottom (within tolerance)
            const isAtBottom = 
              outputContainer.scrollHeight - outputContainer.scrollTop <= 
              outputContainer.clientHeight + 100;
            expect(isAtBottom).toBe(true);
          }, { timeout: 1000 });
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 11: Output Line Limit
   * For any output area exceeding 1000 lines, the oldest lines should be removed to maintain 
   * the 1000-line limit
   * Validates: Requirements 4.5
   */
  it('Property 11: Output Line Limit - should trim oldest entries when exceeding limit', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: MAX_OUTPUT_LINES + 1, max: MAX_OUTPUT_LINES + 500 }),
        (totalLines) => {
          // Create more lines than the limit
          const lines: OutputLine[] = Array.from({ length: totalLines }, (_, index) => ({
            id: `line-${index}`,
            type: index % 2 === 0 ? ('command' as const) : ('response' as const),
            text: `Line ${index}`,
            timestamp: Date.now() + index,
          }));

          // Render component
          const { container } = render(<GameOutput lines={lines} />);

          // Count rendered lines
          const renderedLines = container.querySelectorAll('.output-line');
          
          // Should not exceed MAX_OUTPUT_LINES
          expect(renderedLines.length).toBeLessThanOrEqual(MAX_OUTPUT_LINES);

          // Should show the most recent lines
          const lastLine = renderedLines[renderedLines.length - 1];
          expect(lastLine.textContent).toContain(`Line ${totalLines - 1}`);

          // Should not show the oldest lines
          const firstRenderedLine = renderedLines[0];
          const expectedFirstIndex = totalLines - MAX_OUTPUT_LINES;
          expect(firstRenderedLine.textContent).toContain(`Line ${expectedFirstIndex}`);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Error lines should be displayed with error styling
   */
  it('should display error lines with error styling', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            type: fc.constantFrom('command' as const, 'response' as const, 'error' as const),
            text: fc.string({ minLength: 1, maxLength: 100 }),
          }),
          { minLength: 1, maxLength: 30 }
        ),
        (lineData) => {
          const lines: OutputLine[] = lineData.map((data, index) => ({
            id: `line-${index}`,
            type: data.type,
            text: data.text,
            timestamp: Date.now() + index,
          }));

          const { container } = render(<GameOutput lines={lines} />);

          // Verify error lines have error class
          const errorLines = lines.filter(line => line.type === 'error');
          const errorElements = container.querySelectorAll('.output-line--error');
          
          expect(errorElements.length).toBe(errorLines.length);

          // Verify each error line contains its text
          errorLines.forEach((line) => {
            const outputText = container.textContent || '';
            expect(outputText).toContain(line.text);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Empty lines array should render empty output
   */
  it('should handle empty lines array', () => {
    const { container } = render(<GameOutput lines={[]} />);
    
    const outputContainer = container.querySelector('.game-output');
    expect(outputContainer).toBeTruthy();
    
    const outputLines = container.querySelectorAll('.output-line');
    expect(outputLines.length).toBe(0);
  });

  /**
   * Property: Lines should maintain unique IDs
   */
  it('should maintain unique IDs for all lines', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }), { minLength: 1, maxLength: 50 }),
        (commands) => {
          const lines: OutputLine[] = commands.map((cmd, index) => ({
            id: `unique-${index}-${Date.now()}`,
            type: 'command' as const,
            text: cmd,
            timestamp: Date.now() + index,
          }));

          const { container } = render(<GameOutput lines={lines} />);

          // All lines should be rendered
          const renderedLines = container.querySelectorAll('.output-line');
          expect(renderedLines.length).toBe(lines.length);

          // Verify all IDs are unique (React will warn if not)
          const ids = lines.map(line => line.id);
          const uniqueIds = new Set(ids);
          expect(uniqueIds.size).toBe(ids.length);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Command lines should have prompt prefix
   */
  it('should add prompt prefix to command lines', () => {
    fc.assert(
      fc.property(
        fc.array(fc.string({ minLength: 1, maxLength: 100 }), { minLength: 1, maxLength: 30 }),
        (commands) => {
          const lines: OutputLine[] = commands.map((cmd, index) => ({
            id: `cmd-${index}`,
            type: 'command' as const,
            text: cmd,
            timestamp: Date.now() + index,
          }));

          const { container } = render(<GameOutput lines={lines} />);

          // All command lines should have prompt
          const commandElements = container.querySelectorAll('.output-line--command');
          commandElements.forEach((element) => {
            const promptElement = element.querySelector('.output-line__prompt');
            expect(promptElement).toBeTruthy();
            expect(promptElement?.textContent).toContain('>');
          });
        }
      ),
      { numRuns: 100 }
    );
  });
});
