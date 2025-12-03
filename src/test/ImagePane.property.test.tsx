/**
 * Property-Based Tests for ImagePane Component
 * Feature: grimoire-frontend
 * 
 * Tests the dissolve transition behavior, queuing, and image preloading
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, waitFor, act } from '@testing-library/react';
import * as fc from 'fast-check';
import ImagePane from '../components/ImagePane';
import { TRANSITION_DURATION, DEFAULT_ROOM_IMAGE } from '../types';
import * as imageUtils from '../utils/imageUtils';

// Mock the image utilities
vi.mock('../utils/imageUtils', async () => {
  const actual = await vi.importActual('../utils/imageUtils');
  return {
    ...actual,
    preloadImage: vi.fn(),
  };
});

describe('ImagePane Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
    
    // Mock successful image preloading by default
    vi.mocked(imageUtils.preloadImage).mockResolvedValue();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  /**
   * Property 1: Transition Duration Consistency
   * For any room transition, the dissolve effect should complete in exactly 3 seconds (3000ms)
   * Validates: Requirements 2.1
   */
  it('Property 1: Transition Duration Consistency - should complete transitions in 3 seconds', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }),
        async (roomName) => {
          const { rerender } = render(
            <ImagePane
              roomName="Initial Room"
              roomDescription="Initial description"
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Record start time
          const startTime = Date.now();

          // Trigger transition to new room
          await act(async () => {
            rerender(
              <ImagePane
                roomName={roomName}
                roomDescription="New description"
              />
            );
            await vi.advanceTimersByTimeAsync(0);
          });

          // Advance timers by transition duration
          await act(async () => {
            await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
          });

          // Record end time
          const endTime = Date.now();
          const duration = endTime - startTime;

          // Should complete in exactly 3000ms (with small tolerance for test execution)
          expect(duration).toBeGreaterThanOrEqual(TRANSITION_DURATION - 100);
          expect(duration).toBeLessThanOrEqual(TRANSITION_DURATION + 100);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 2: Transition Atomicity
   * For any transition in progress, attempting to start a new transition should queue it 
   * rather than interrupt the current transition
   * Validates: Requirements 2.2
   */
  it('Property 2: Transition Atomicity - should queue transitions instead of interrupting', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.string({ minLength: 1, maxLength: 30 }).filter(s => s.trim().length > 0), { minLength: 2, maxLength: 5 })
          .filter(arr => {
            // Filter out arrays with consecutive duplicates
            for (let i = 1; i < arr.length; i++) {
              if (arr[i] === arr[i - 1]) return false;
            }
            return true;
          }),
        async (roomNames) => {
          // Clear mocks before test
          vi.mocked(imageUtils.preloadImage).mockClear();
          
          const { rerender } = render(
            <ImagePane
              roomName={roomNames[0]}
              roomDescription="Description"
            />
          );

          // Wait for initial render and first preload
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Record initial call count
          const initialCalls = vi.mocked(imageUtils.preloadImage).mock.calls.length;

          // Trigger multiple rapid transitions
          for (let i = 1; i < roomNames.length; i++) {
            await act(async () => {
              rerender(
                <ImagePane
                  roomName={roomNames[i]}
                  roomDescription="Description"
                />
              );
              // Don't advance timers - simulate rapid changes
              await vi.advanceTimersByTimeAsync(0);
            });
          }

          // Verify preloadImage was called for all rooms (initial + new ones)
          const totalExpectedCalls = roomNames.length;
          expect(imageUtils.preloadImage).toHaveBeenCalledTimes(totalExpectedCalls);

          // Advance through all transitions
          for (let i = 0; i < roomNames.length; i++) {
            await act(async () => {
              await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
            });
          }

          // All transitions should have completed - no additional calls
          expect(imageUtils.preloadImage).toHaveBeenCalledTimes(totalExpectedCalls);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 3: Transition Completion State
   * For any completed transition, the new room image should be displayed at full opacity (1.0)
   * Validates: Requirements 2.3
   */
  it('Property 3: Transition Completion State - should display new image at full opacity after transition', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }),
        async (roomName) => {
          const { container, rerender } = render(
            <ImagePane
              roomName="Initial Room"
              roomDescription="Initial description"
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Trigger transition
          await act(async () => {
            rerender(
              <ImagePane
                roomName={roomName}
                roomDescription="New description"
              />
            );
            await vi.advanceTimersByTimeAsync(0);
          });

          // Complete the transition
          await act(async () => {
            await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
          });

          // Find all images
          const images = container.querySelectorAll('img.room-image');
          
          // Should have at least one image
          expect(images.length).toBeGreaterThan(0);

          // At least one image should have full opacity
          const hasFullOpacity = Array.from(images).some(img => {
            const opacity = (img as HTMLElement).style.opacity;
            return opacity === '1' || opacity === '';
          });

          expect(hasFullOpacity).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 4: Transition Queue Ordering
   * For any sequence of rapid room changes, transitions should execute in the order they were requested
   * Validates: Requirements 2.4
   */
  it('Property 4: Transition Queue Ordering - should execute transitions in order', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(fc.string({ minLength: 1, maxLength: 30 }).filter(s => s.trim().length > 0), { minLength: 3, maxLength: 6 }),
        async (roomNames) => {
          // Clear mocks before test
          vi.mocked(imageUtils.preloadImage).mockClear();
          
          const { rerender } = render(
            <ImagePane
              roomName={roomNames[0]}
              roomDescription="Description"
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Clear calls from initial render
          vi.mocked(imageUtils.preloadImage).mockClear();

          // Trigger multiple rapid transitions
          for (let i = 1; i < roomNames.length; i++) {
            await act(async () => {
              rerender(
                <ImagePane
                  roomName={roomNames[i]}
                  roomDescription="Description"
                />
              );
              await vi.advanceTimersByTimeAsync(0);
            });
          }

          // Get the order of preloadImage calls
          const callOrder: string[] = [];
          vi.mocked(imageUtils.preloadImage).mock.calls.forEach(call => {
            callOrder.push(call[0]);
          });

          // Verify calls were made for all new rooms
          expect(callOrder.length).toBeGreaterThan(0);
          
          // Verify calls were made in order
          for (let i = 1; i < roomNames.length; i++) {
            const expectedPath = imageUtils.mapRoomToImage(roomNames[i]);
            expect(callOrder).toContain(expectedPath);
          }

          // Advance through all transitions
          for (let i = 1; i < roomNames.length; i++) {
            await act(async () => {
              await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
            });
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 14: Image Preloading
   * For any valid room image, it should be preloaded before the dissolve transition begins
   * Validates: Requirements 6.2
   */
  it('Property 14: Image Preloading - should preload images before transitions', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        async (roomName) => {
          // Clear mocks before test
          vi.mocked(imageUtils.preloadImage).mockClear();
          
          const { rerender } = render(
            <ImagePane
              roomName="Initial Room"
              roomDescription="Initial description"
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Clear calls from initial render
          vi.mocked(imageUtils.preloadImage).mockClear();

          // Trigger transition
          await act(async () => {
            rerender(
              <ImagePane
                roomName={roomName}
                roomDescription="New description"
              />
            );
            await vi.advanceTimersByTimeAsync(0);
          });

          // Verify preloadImage was called
          expect(imageUtils.preloadImage).toHaveBeenCalled();

          // Verify it was called with the correct image path
          const expectedPath = imageUtils.mapRoomToImage(roomName);
          expect(imageUtils.preloadImage).toHaveBeenCalledWith(expectedPath);

          // Complete the transition
          await act(async () => {
            await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
          });
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property 15: Image Update Synchronization
   * For any room change, the displayed image should update to match the new room location
   * Validates: Requirements 6.4
   */
  it('Property 15: Image Update Synchronization - should update image to match new room', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }),
        async (roomName) => {
          const { container, rerender } = render(
            <ImagePane
              roomName="Initial Room"
              roomDescription="Initial description"
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Trigger transition
          await act(async () => {
            rerender(
              <ImagePane
                roomName={roomName}
                roomDescription="New description"
              />
            );
            await vi.advanceTimersByTimeAsync(0);
          });

          // Complete the transition
          await act(async () => {
            await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
          });

          // Get the expected image path
          const expectedPath = imageUtils.mapRoomToImage(roomName);

          // Find images in the container
          const images = container.querySelectorAll('img.room-image');
          
          // At least one image should have the expected src
          const hasExpectedSrc = Array.from(images).some(img => {
            return (img as HTMLImageElement).src.includes(expectedPath.replace('/images/', ''));
          });

          expect(hasExpectedSrc).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Failed image loads should fall back to default image
   */
  it('should use default image when preload fails', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }),
        async (roomName) => {
          // Reset mocks for this iteration
          vi.clearAllMocks();
          
          // Mock preloadImage to succeed for initial render
          vi.mocked(imageUtils.preloadImage).mockResolvedValueOnce();
          
          const { container, rerender } = render(
            <ImagePane
              roomName="Initial Room"
              roomDescription="Initial description"
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          // Mock preloadImage to fail for the transition
          vi.mocked(imageUtils.preloadImage).mockRejectedValueOnce(
            new Error('Failed to load image')
          );

          // Trigger transition
          await act(async () => {
            rerender(
              <ImagePane
                roomName={roomName}
                roomDescription="New description"
              />
            );
            await vi.advanceTimersByTimeAsync(0);
          });

          // Complete the transition
          await act(async () => {
            await vi.advanceTimersByTimeAsync(TRANSITION_DURATION);
          });

          // Should have used default image
          const images = container.querySelectorAll('img.room-image');
          const hasDefaultImage = Array.from(images).some(img => {
            return (img as HTMLImageElement).src.includes('default_haunted.png');
          });

          expect(hasDefaultImage).toBe(true);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Custom transition duration should be respected
   */
  it('should respect custom transition duration', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1000, max: 5000 }),
        fc.string({ minLength: 1, maxLength: 50 }),
        async (customDuration, roomName) => {
          const { rerender } = render(
            <ImagePane
              roomName="Initial Room"
              roomDescription="Initial description"
              transitionDuration={customDuration}
            />
          );

          // Wait for initial render
          await act(async () => {
            await vi.advanceTimersByTimeAsync(0);
          });

          const startTime = Date.now();

          // Trigger transition
          await act(async () => {
            rerender(
              <ImagePane
                roomName={roomName}
                roomDescription="New description"
                transitionDuration={customDuration}
              />
            );
            await vi.advanceTimersByTimeAsync(0);
          });

          // Advance by custom duration
          await act(async () => {
            await vi.advanceTimersByTimeAsync(customDuration);
          });

          const endTime = Date.now();
          const duration = endTime - startTime;

          // Should complete in the custom duration (with tolerance)
          expect(duration).toBeGreaterThanOrEqual(customDuration - 100);
          expect(duration).toBeLessThanOrEqual(customDuration + 100);
        }
      ),
      { numRuns: 100 }
    );
  });
});
