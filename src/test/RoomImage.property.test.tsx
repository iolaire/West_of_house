/**
 * Property-Based Tests for RoomImage Component
 * Feature: grimoire-frontend
 * 
 * Tests the image rendering with alt text, opacity transitions, and error handling
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render } from '@testing-library/react';
import * as fc from 'fast-check';
import RoomImage from '../components/RoomImage';
import { DEFAULT_ROOM_IMAGE } from '../types';

describe('RoomImage Property Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  /**
   * Property 17: Image Alt Text
   * For any displayed room image, the alt attribute should contain the description_spooky text
   * Validates: Requirements 8.1
   */
  it('Property 17: Image Alt Text - should use description_spooky as alt text', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 200 }), // src
        fc.string({ minLength: 1, maxLength: 500 }), // alt text (description_spooky)
        fc.boolean(), // isTransitioning
        fc.double({ min: 0, max: 1 }), // opacity
        async (src, alt, isTransitioning, opacity) => {
          const { container } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={isTransitioning}
              opacity={opacity}
            />
          );

          // Find the image element
          const img = container.querySelector('img.room-image') as HTMLImageElement;
          
          // Image should exist
          expect(img).toBeTruthy();
          
          // Alt attribute should match the provided alt text (description_spooky)
          expect(img.alt).toBe(alt);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Image should have lazy loading attribute
   * Validates: Requirements 10.2
   */
  it('should have lazy loading attribute for performance', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 200 }),
        fc.string({ minLength: 1, maxLength: 500 }),
        fc.boolean(),
        fc.double({ min: 0, max: 1 }),
        async (src, alt, isTransitioning, opacity) => {
          const { container } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={isTransitioning}
              opacity={opacity}
            />
          );

          const img = container.querySelector('img.room-image') as HTMLImageElement;
          
          // Should have lazy loading attribute
          // Note: jsdom may not fully support the loading attribute, so check for presence
          expect(img.getAttribute('loading')).toBe('lazy');
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Image opacity should match the provided opacity prop
   * Validates: Requirements 6.3
   */
  it('should apply correct opacity from props', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 200 }),
        fc.string({ minLength: 1, maxLength: 500 }),
        fc.boolean(),
        fc.double({ min: 0, max: 1, noNaN: true }),
        async (src, alt, isTransitioning, opacity) => {
          const { container } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={isTransitioning}
              opacity={opacity}
            />
          );

          const img = container.querySelector('img.room-image') as HTMLImageElement;
          
          // Opacity should match the prop
          expect(img.style.opacity).toBe(opacity.toString());
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Image should have transition class when transitioning
   * Validates: Requirements 2.1
   */
  it('should apply transitioning class when isTransitioning is true', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 200 }),
        fc.string({ minLength: 1, maxLength: 500 }),
        fc.double({ min: 0, max: 1 }),
        async (src, alt, opacity) => {
          // Test with isTransitioning = true
          const { container: containerTrue } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={true}
              opacity={opacity}
            />
          );

          const imgTrue = containerTrue.querySelector('img.room-image') as HTMLImageElement;
          expect(imgTrue.classList.contains('transitioning')).toBe(true);

          // Test with isTransitioning = false
          const { container: containerFalse } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={false}
              opacity={opacity}
            />
          );

          const imgFalse = containerFalse.querySelector('img.room-image') as HTMLImageElement;
          expect(imgFalse.classList.contains('transitioning')).toBe(false);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Image should have correct transition duration based on isTransitioning
   * Validates: Requirements 2.1
   */
  it('should apply 3s transition when transitioning, 0s otherwise', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 200 }),
        fc.string({ minLength: 1, maxLength: 500 }),
        fc.double({ min: 0, max: 1 }),
        async (src, alt, opacity) => {
          // Test with isTransitioning = true
          const { container: containerTrue } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={true}
              opacity={opacity}
            />
          );

          const imgTrue = containerTrue.querySelector('img.room-image') as HTMLImageElement;
          expect(imgTrue.style.transition).toContain('3s');

          // Test with isTransitioning = false
          const { container: containerFalse } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={false}
              opacity={opacity}
            />
          );

          const imgFalse = containerFalse.querySelector('img.room-image') as HTMLImageElement;
          expect(imgFalse.style.transition).toContain('0s');
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Image src should match the provided src prop
   * Validates: Requirements 6.3
   */
  it('should render image with correct src attribute', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 200 }).filter(s => s.trim().length > 0),
        fc.string({ minLength: 1, maxLength: 500 }),
        fc.boolean(),
        fc.double({ min: 0, max: 1 }),
        async (src, alt, isTransitioning, opacity) => {
          const { container } = render(
            <RoomImage
              src={src}
              alt={alt}
              isTransitioning={isTransitioning}
              opacity={opacity}
            />
          );

          const img = container.querySelector('img.room-image') as HTMLImageElement;
          
          // Src should match the provided src (use getAttribute to get the raw value)
          expect(img.getAttribute('src')).toBe(src);
        }
      ),
      { numRuns: 100 }
    );
  });
});
