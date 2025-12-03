/**
 * Property-Based Tests for LoadingIndicator Component
 * Feature: grimoire-frontend, Property 6: Input State During Processing
 * 
 * Tests that loading indicator is visible during command processing
 * and that input is disabled when loading
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, cleanup } from '@testing-library/react';
import * as fc from 'fast-check';
import LoadingIndicator from '../components/LoadingIndicator';
import CommandInput from '../components/CommandInput';

describe('LoadingIndicator Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  /**
   * Property 6: Input State During Processing
   * For any command being processed, the input field should be disabled 
   * and a loading indicator should be visible
   * Validates: Requirements 3.3
   */
  it('Property 6: Input State During Processing - loading indicator visible when isVisible is true', () => {
    fc.assert(
      fc.property(
        fc.boolean(),
        (isVisible) => {
          const { container, queryByRole, unmount } = render(
            <LoadingIndicator isVisible={isVisible} />
          );

          try {
            const statusElement = queryByRole('status');

            if (isVisible) {
              // When isVisible is true, loading indicator should be present
              expect(statusElement).not.toBeNull();
              expect(statusElement).toHaveAttribute('aria-live', 'polite');
              expect(statusElement).toHaveAttribute('aria-label', 'Processing command');
              
              // Should contain the spinner and text
              const spinner = container.querySelector('.loading-indicator__spinner');
              const text = container.querySelector('.loading-indicator__text');
              expect(spinner).not.toBeNull();
              expect(text).not.toBeNull();
              expect(text?.textContent).toBe('Processing...');
            } else {
              // When isVisible is false, loading indicator should not be present
              expect(statusElement).toBeNull();
              expect(container.querySelector('.loading-indicator')).toBeNull();
            }
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should show loading indicator when command is processing', () => {
    fc.assert(
      fc.property(
        fc.array(
          fc.record({
            isLoading: fc.boolean(),
            command: fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
          }),
          { minLength: 1, maxLength: 20 }
        ),
        (states) => {
          const onSubmit = vi.fn();
          
          states.forEach(({ isLoading, command }) => {
            const { getByRole: getInputByRole, unmount: unmountInput } = render(
              <CommandInput onSubmit={onSubmit} disabled={isLoading} />
            );
            
            const { queryByRole: queryIndicatorByRole, unmount: unmountIndicator } = render(
              <LoadingIndicator isVisible={isLoading} />
            );

            try {
              const input = getInputByRole('textbox') as HTMLInputElement;
              const indicator = queryIndicatorByRole('status');

              // Input should be disabled when loading
              expect(input.disabled).toBe(isLoading);

              // Loading indicator should be visible when loading
              if (isLoading) {
                expect(indicator).not.toBeNull();
              } else {
                expect(indicator).toBeNull();
              }
            } finally {
              unmountInput();
              unmountIndicator();
            }
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should have proper accessibility attributes', () => {
    const { getByRole, container } = render(<LoadingIndicator isVisible={true} />);
    
    const statusElement = getByRole('status');
    expect(statusElement).toHaveAttribute('aria-live', 'polite');
    expect(statusElement).toHaveAttribute('aria-label', 'Processing command');
    
    // Should have screen reader text
    const srText = container.querySelector('.loading-indicator__sr-only');
    expect(srText).not.toBeNull();
    expect(srText?.textContent).toBe('Command is being processed');
  });

  it('should render three pulsing dots', () => {
    const { container } = render(<LoadingIndicator isVisible={true} />);
    
    const dots = container.querySelectorAll('.loading-indicator__dot');
    expect(dots.length).toBe(3);
    
    // Each dot should have the correct class
    expect(dots[0].classList.contains('loading-indicator__dot--1')).toBe(true);
    expect(dots[1].classList.contains('loading-indicator__dot--2')).toBe(true);
    expect(dots[2].classList.contains('loading-indicator__dot--3')).toBe(true);
  });

  it('should render processing text', () => {
    const { container } = render(<LoadingIndicator isVisible={true} />);
    
    const text = container.querySelector('.loading-indicator__text');
    expect(text).not.toBeNull();
    expect(text?.textContent).toBe('Processing...');
  });

  it('should not render when isVisible is false', () => {
    const { container, queryByRole } = render(<LoadingIndicator isVisible={false} />);
    
    expect(queryByRole('status')).toBeNull();
    expect(container.querySelector('.loading-indicator')).toBeNull();
  });

  it('should toggle visibility correctly', () => {
    fc.assert(
      fc.property(
        fc.array(fc.boolean(), { minLength: 2, maxLength: 10 }),
        (visibilityStates) => {
          visibilityStates.forEach((isVisible) => {
            const { queryByRole, unmount } = render(
              <LoadingIndicator isVisible={isVisible} />
            );

            try {
              const statusElement = queryByRole('status');
              
              if (isVisible) {
                expect(statusElement).not.toBeNull();
              } else {
                expect(statusElement).toBeNull();
              }
            } finally {
              unmount();
            }
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  it('should maintain consistent structure when visible', () => {
    fc.assert(
      fc.property(
        fc.constant(true),
        (isVisible) => {
          const { container, getByRole, unmount } = render(
            <LoadingIndicator isVisible={isVisible} />
          );

          try {
            // Should have status role
            const statusElement = getByRole('status');
            expect(statusElement).not.toBeNull();

            // Should have spinner with 3 dots
            const spinner = container.querySelector('.loading-indicator__spinner');
            expect(spinner).not.toBeNull();
            
            const dots = container.querySelectorAll('.loading-indicator__dot');
            expect(dots.length).toBe(3);

            // Should have text
            const text = container.querySelector('.loading-indicator__text');
            expect(text).not.toBeNull();
            expect(text?.textContent).toBe('Processing...');

            // Should have screen reader text
            const srText = container.querySelector('.loading-indicator__sr-only');
            expect(srText).not.toBeNull();
          } finally {
            unmount();
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});
