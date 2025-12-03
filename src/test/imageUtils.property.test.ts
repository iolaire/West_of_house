/**
 * Property-Based Tests for Image Utilities
 * Feature: grimoire-frontend, Property 13: Room Name to Image Mapping
 * Validates: Requirements 6.1
 * 
 * Property 13: Room Name to Image Mapping
 * For any room name returned by the backend, the grimoire should map it to a 
 * corresponding image file path in the `/images` directory
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
   * corresponding image file path in the `/images` directory
   */
  it('Property 13: Room Name to Image Mapping - should map any room name to valid image path', () => {
    fc.assert(
      fc.property(
        fc.string({ minLength: 1, maxLength: 100 }),
        (roomName) => {
          const imagePath = mapRoomToImage(roomName);

          // Should return a string
          expect(typeof imagePath).toBe('string');

          // Should start with /images/
          expect(imagePath).toMatch(/^\/images\//);

          // Should end with .png
          expect(imagePath).toMatch(/\.png$/);

          // Should not contain spaces
          expect(imagePath).not.toContain(' ');

          // Extract filename (could be empty for default image)
          const filename = imagePath.replace('/images/', '').replace('.png', '');
          
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
          expect(imagePath).toMatch(/^\/images\/[a-z0-9_]+\.png$/);
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
            const filename = imagePath.replace('/images/', '').replace('.png', '');
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
      { room: 'West of House', expected: '/images/west_of_house.png' },
      { room: 'East of House', expected: '/images/east_of_house.png' },
      { room: 'North of House', expected: '/images/north_of_house.png' },
      { room: 'South of House', expected: '/images/south_of_house.png' },
      { room: 'Kitchen', expected: '/images/kitchen.png' },
      { room: 'Living Room', expected: '/images/living_room.png' },
      { room: 'Attic', expected: '/images/attic.png' },
      { room: 'Cellar', expected: '/images/cellar.png' },
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
          expect(imagePath).toMatch(/^\/images\/[a-z0-9_]+\.png$/);

          // Should not be empty
          const filename = imagePath.replace('/images/', '').replace('.png', '');
          expect(filename.length).toBeGreaterThan(0);
        }
      ),
      { numRuns: 100 }
    );
  });
});
