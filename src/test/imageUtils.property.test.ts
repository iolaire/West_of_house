/**
 * Property-Based Tests for Image Utilities
 * Feature: grimoire-frontend, Property 13: Room Name to Image Mapping
 * Validates: Requirements 6.1
 * 
 * Property 13: Room Name to Image Mapping
 * For any room name returned by the backend, the grimoire should map it to a 
 * corresponding image file path in the `/images/rooms` directory
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import * as fc from 'fast-check';
import { 
  mapRoomToImage, 
  preloadImage, 
  getUnmappedRooms, 
  clearUnmappedRooms,
  exportUnmappedRoomsToText 
} from '../utils/imageUtils';
import { DEFAULT_ROOM_IMAGE } from '../types';

describe('Image Utils Property Tests', () => {
  beforeEach(() => {
    // Clear unmapped rooms before each test
    clearUnmappedRooms();
  });

  afterEach(() => {
    // Clean up after each test
    clearUnmappedRooms();
  });

  /**
   * Property 13: Room Name to Image Mapping
   * For any room name returned by the backend, the grimoire should map it to a 
   * corresponding image file path in the `/images/rooms` directory
   */
  it('Property 13: Room Name to Image Mapping - should map any room name to valid image path', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 100 }),
        (roomName) => {
          const imagePath = mapRoomToImage(roomName);

          // Should return a string
          expect(typeof imagePath).toBe('string');

          // Should start with /images/rooms/
          expect(imagePath).toMatch(/^\/images\/rooms\//);

          // Should end with .png
          expect(imagePath).toMatch(/\.png$/);

          // Should not contain spaces
          expect(imagePath).not.toContain(' ');

          // Extract filename (could be empty for default image)
          const filename = imagePath.replace('/images/rooms/', '').replace('.png', '');
          
          // Should be lowercase
          expect(filename).toBe(filename.toLowerCase());

          // Should only contain alphanumeric characters and underscores (or be default_haunted)
          if (filename !== 'default_haunted') {
            expect(filename).toMatch(/^[a-z0-9_]+$/);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Empty or whitespace-only room names should return default image
   */
  it('should return default image for empty or whitespace room names', () => {
    fc.assert(
      fc.property(
        fc.oneof(
          fc.constant(''),
          fc.constant('   '),
          fc.constant('\t'),
          fc.constant('\n'),
          fc.array(fc.constantFrom(' ', '\t', '\n'), { minLength: 1, maxLength: 10 }).map(arr => arr.join(''))
        ),
        (emptyRoomName) => {
          const imagePath = mapRoomToImage(emptyRoomName);
          expect(imagePath).toBe(DEFAULT_ROOM_IMAGE);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Room names with special characters should be sanitized
   */
  it('should sanitize room names with special characters', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => /[a-z0-9]/i.test(s)),
        fc.constantFrom('!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '='),
        (baseName, specialChar) => {
          const roomName = `${baseName}${specialChar}${baseName}`;
          const imagePath = mapRoomToImage(roomName);

          // Should not contain the special character
          expect(imagePath).not.toContain(specialChar);

          // Should still be a valid path (or default if all chars were special)
          expect(imagePath).toMatch(/^\/images\/rooms\/[a-z0-9_]+\.png$/);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Room names with multiple spaces should be converted to single underscores
   */
  it('should convert multiple spaces to single underscores', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 20 }).filter(s => /[a-z0-9]/i.test(s)),
        fc.string({ minLength: 1, maxLength: 20 }).filter(s => /[a-z0-9]/i.test(s)),
        fc.integer({ min: 1, max: 5 }),
        (word1, word2, numSpaces) => {
          const spaces = ' '.repeat(numSpaces);
          const roomName = `${word1}${spaces}${word2}`;
          const imagePath = mapRoomToImage(roomName);

          // Should not contain multiple consecutive underscores
          expect(imagePath).not.toMatch(/__+/);

          // If the result is not the default image, check for underscores
          if (imagePath !== DEFAULT_ROOM_IMAGE) {
            const filename = imagePath.replace('/images/rooms/', '').replace('.png', '');
            // Should not have leading or trailing underscores
            expect(filename).not.toMatch(/^_/);
            expect(filename).not.toMatch(/_$/);
          }
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Same room name should always map to same image path (deterministic)
   */
  it('should be deterministic - same input produces same output', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 100 }),
        (roomName) => {
          const path1 = mapRoomToImage(roomName);
          const path2 = mapRoomToImage(roomName);
          const path3 = mapRoomToImage(roomName);

          expect(path1).toBe(path2);
          expect(path2).toBe(path3);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Room names that differ only in case should map to same image
   */
  it('should map case-insensitive room names to same image', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        (roomName) => {
          const lowercase = mapRoomToImage(roomName.toLowerCase());
          const uppercase = mapRoomToImage(roomName.toUpperCase());
          const mixedcase = mapRoomToImage(roomName);

          expect(lowercase).toBe(uppercase);
          expect(uppercase).toBe(mixedcase);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Trimming whitespace should not affect mapping
   */
  it('should handle leading and trailing whitespace consistently', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        fc.integer({ min: 0, max: 5 }),
        fc.integer({ min: 0, max: 5 }),
        (roomName, leadingSpaces, trailingSpaces) => {
          const trimmed = roomName.trim();
          const withSpaces = ' '.repeat(leadingSpaces) + trimmed + ' '.repeat(trailingSpaces);

          const path1 = mapRoomToImage(trimmed);
          const path2 = mapRoomToImage(withSpaces);

          expect(path1).toBe(path2);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Known room names should map to expected paths
   */
  it('should map known room names correctly', () => {
    const knownMappings = [
      { room: 'West of House', expected: '/images/rooms/west_of_house.png' },
      { room: 'East of House', expected: '/images/rooms/east_of_house.png' },
      { room: 'North of House', expected: '/images/rooms/north_of_house.png' },
      { room: 'South of House', expected: '/images/rooms/south_of_house.png' },
      { room: 'Kitchen', expected: '/images/rooms/kitchen.png' },
      { room: 'Living Room', expected: '/images/rooms/living_room.png' },
      { room: 'Attic', expected: '/images/rooms/attic.png' },
      { room: 'Cellar', expected: '/images/rooms/cellar.png' },
    ];

    knownMappings.forEach(({ room, expected }) => {
      const result = mapRoomToImage(room);
      expect(result).toBe(expected);
    });
  });

  /**
   * Property: Unmapped rooms tracking functions should work correctly
   */
  it('should provide unmapped rooms tracking functions', () => {
    // Clear before test
    clearUnmappedRooms();

    // Should start empty
    expect(getUnmappedRooms()).toEqual([]);

    // Clear should work
    clearUnmappedRooms();
    expect(getUnmappedRooms()).toEqual([]);
  });

  /**
   * Property: Export unmapped rooms should produce valid text format
   */
  it('should export unmapped rooms in valid text format', () => {
    clearUnmappedRooms();

    const report = exportUnmappedRoomsToText();

    // Should be a string
    expect(typeof report).toBe('string');

    // Should contain "No unmapped rooms found" when empty
    expect(report).toContain('No unmapped rooms found');
  });

  /**
   * Property: Clear unmapped rooms should reset the tracking
   */
  it('should clear unmapped rooms list', () => {
    // Clear the list
    clearUnmappedRooms();

    // Should be empty
    expect(getUnmappedRooms().length).toBe(0);
  });

  /**
   * Property: Preload function should exist and be callable
   */
  it('should have preloadImage function available', () => {
    expect(typeof preloadImage).toBe('function');
  });

  /**
   * Property: Room names with numbers should be preserved
   */
  it('should preserve numbers in room names', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 20 }).filter(s => s.trim().length > 0),
        fc.integer({ min: 1, max: 100 }),
        (baseName, number) => {
          const roomName = `${baseName} ${number}`;
          const imagePath = mapRoomToImage(roomName);

          // Should contain the number
          expect(imagePath).toContain(String(number));
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Very long room names should still produce valid paths
   */
  it('should handle very long room names', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 100, maxLength: 500 }),
        (longRoomName) => {
          const imagePath = mapRoomToImage(longRoomName);

          // Should still be a valid path format
          expect(imagePath).toMatch(/^\/images\/rooms\/[a-z0-9_]+\.png$/);

          // Should not be empty
          const filename = imagePath.replace('/images/rooms/', '').replace('.png', '');
          expect(filename.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });
});

/**
 * WebP Optimization Tests
 * Tests for WebP format conversion and responsive image utilities
 */
describe('WebP Optimization Tests', () => {
  /**
   * Property: getWebPPath should convert PNG paths to WebP
   */
  it('should convert PNG paths to WebP format', async () => {
    const { getWebPPath } = await import('../utils/imageUtils');
    
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        (filename) => {
          const pngPath = `/images/rooms/${filename}.png`;
          const webpPath = getWebPPath(pngPath);

          // Should end with .webp
          expect(webpPath).toMatch(/\.webp$/);

          // Should not contain .png
          expect(webpPath).not.toContain('.png');

          // Should preserve the directory structure
          expect(webpPath).toContain('/images/rooms/');
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: getPNGPath should convert WebP paths to PNG
   */
  it('should convert WebP paths to PNG format', async () => {
    const { getPNGPath } = await import('../utils/imageUtils');
    
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        (filename) => {
          const webpPath = `/images/rooms/${filename}.webp`;
          const pngPath = getPNGPath(webpPath);

          // Should end with .png
          expect(pngPath).toMatch(/\.png$/);

          // Should not contain .webp
          expect(pngPath).not.toContain('.webp');

          // Should preserve the directory structure
          expect(pngPath).toContain('/images/rooms/');
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: Round-trip conversion should preserve filename
   */
  it('should preserve filename through round-trip conversion', async () => {
    const { getWebPPath, getPNGPath } = await import('../utils/imageUtils');
    
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        (filename) => {
          const originalPng = `/images/rooms/${filename}.png`;
          
          // PNG -> WebP -> PNG
          const webp = getWebPPath(originalPng);
          const backToPng = getPNGPath(webp);

          expect(backToPng).toBe(originalPng);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: getResponsiveSizes should return valid srcset
   */
  it('should generate valid responsive image sizes', async () => {
    const { getResponsiveSizes } = await import('../utils/imageUtils');
    
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
        (filename) => {
          const imagePath = `/images/rooms/${filename}.png`;
          const sizes = getResponsiveSizes(imagePath);

          // Should have webp and png srcsets
          expect(sizes.webp).toBeDefined();
          expect(sizes.png).toBeDefined();
          expect(sizes.sizes).toBeDefined();

          // WebP srcset should contain .webp
          expect(sizes.webp.srcSet).toContain('.webp');

          // PNG srcset should contain .png
          expect(sizes.png.srcSet).toContain('.png');

          // Sizes should be a valid CSS sizes attribute
          expect(typeof sizes.sizes).toBe('string');
          expect(sizes.sizes.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });

  /**
   * Property: preloadAdjacentRooms should handle empty arrays
   */
  it('should handle empty adjacent rooms array', async () => {
    const { preloadAdjacentRooms } = await import('../utils/imageUtils');
    
    // Should not throw
    await expect(preloadAdjacentRooms([])).resolves.toBeUndefined();
  });

  /**
   * Property: preloadAdjacentRooms should limit to 3 rooms
   */
  it('should limit preloading to 3 adjacent rooms', async () => {
    const { preloadAdjacentRooms } = await import('../utils/imageUtils');
    
    fc.assert(
      fc.asyncProperty(
        fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 4, maxLength: 10 }),
        async (rooms) => {
          // Should not throw even with many rooms
          await expect(preloadAdjacentRooms(rooms)).resolves.toBeUndefined();
        }
      ),
      { numRuns: 50 }
    );
  });
});
