/**
 * Image utility functions for room image mapping and preloading
 * Feature: grimoire-frontend
 */

import { DEFAULT_ROOM_IMAGE } from '../types';

/**
 * Set of unmapped rooms for debugging purposes
 */
const unmappedRooms = new Set<string>();

/**
 * Maps a room name to its corresponding image filename
 * 
 * Converts room names like "West of House" to "west_of_house.png"
 * Handles special characters and spaces in room names
 * 
 * @param roomName - The name of the room from the backend
 * @returns The path to the room image file
 * 
 * @example
 * mapRoomToImage("West of House") // returns "/images/west_of_house.png"
 * mapRoomToImage("East of House") // returns "/images/east_of_house.png"
 */
export function mapRoomToImage(roomName: string): string {
  if (!roomName || roomName.trim() === '') {
    return DEFAULT_ROOM_IMAGE;
  }

  // Convert room name to snake_case filename
  // 1. Convert to lowercase
  // 2. Replace spaces with underscores
  // 3. Remove all non-alphanumeric characters except underscores
  // 4. Collapse multiple underscores to single underscore
  // 5. Remove leading/trailing underscores
  const filename = roomName
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^a-z0-9_]/g, '')
    .replace(/_+/g, '_')
    .replace(/^_+|_+$/g, '');

  // If filename is empty after sanitization, return default
  if (filename === '') {
    return DEFAULT_ROOM_IMAGE;
  }

  // Return the full path to the image
  return `/images/${filename}.png`;
}

/**
 * Preloads an image to ensure smooth transitions
 * 
 * Creates a new Image object and loads the image before it's needed
 * This prevents loading delays during room transitions
 * 
 * @param imagePath - The path to the image to preload
 * @returns Promise that resolves when the image is loaded, or rejects on error
 * 
 * @example
 * await preloadImage("/images/west_of_house.png")
 */
export function preloadImage(imagePath: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => {
      resolve();
    };
    
    img.onerror = () => {
      // Log the unmapped room for debugging
      const roomName = extractRoomNameFromPath(imagePath);
      if (roomName) {
        unmappedRooms.add(roomName);
        logUnmappedRoom(roomName, imagePath);
      }
      
      // Reject with error, but caller should handle by using fallback
      reject(new Error(`Failed to load image: ${imagePath}`));
    };
    
    img.src = imagePath;
  });
}

/**
 * Extracts the room name from an image path
 * 
 * @param imagePath - The image path (e.g., "/images/west_of_house.png")
 * @returns The room name or null if extraction fails
 */
function extractRoomNameFromPath(imagePath: string): string | null {
  const match = imagePath.match(/\/images\/(.+)\.png$/);
  if (match && match[1]) {
    // Convert snake_case back to Title Case for logging
    return match[1]
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  return null;
}

/**
 * Logs an unmapped room to the console and maintains a list
 * 
 * @param roomName - The name of the room that couldn't be mapped
 * @param attemptedPath - The path that was attempted
 */
function logUnmappedRoom(roomName: string, attemptedPath: string): void {
  console.error(
    `[Image Mapping] Failed to load image for room: "${roomName}"`,
    `\n  Attempted path: ${attemptedPath}`,
    `\n  Falling back to: ${DEFAULT_ROOM_IMAGE}`
  );
}

/**
 * Gets the list of all unmapped rooms encountered during the session
 * Useful for debugging and identifying missing images
 * 
 * @returns Array of room names that failed to load
 */
export function getUnmappedRooms(): string[] {
  return Array.from(unmappedRooms).sort();
}

/**
 * Clears the list of unmapped rooms
 * Useful for testing or resetting the tracking
 */
export function clearUnmappedRooms(): void {
  unmappedRooms.clear();
}

/**
 * Exports unmapped rooms to a text format for debugging
 * 
 * @returns A formatted string listing all unmapped rooms
 */
export function exportUnmappedRoomsToText(): string {
  const rooms = getUnmappedRooms();
  
  if (rooms.length === 0) {
    return 'No unmapped rooms found.';
  }
  
  const header = `Unmapped Rooms Report\n${'='.repeat(50)}\n`;
  const timestamp = `Generated: ${new Date().toISOString()}\n`;
  const count = `Total unmapped rooms: ${rooms.length}\n\n`;
  const roomList = rooms.map((room, index) => `${index + 1}. ${room}`).join('\n');
  
  return header + timestamp + count + roomList;
}

/**
 * Downloads the unmapped rooms report as a text file
 * Useful for developers to identify missing images
 */
export function downloadUnmappedRoomsReport(): void {
  const content = exportUnmappedRoomsToText();
  const blob = new Blob([content], { type: 'text/plain' });
  const url = URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `unmapped-rooms-${Date.now()}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

/**
 * Converts a PNG image path to WebP format
 * 
 * @param imagePath - The original image path (e.g., "/images/west_of_house.png")
 * @returns The WebP version of the image path
 * 
 * @example
 * getWebPPath("/images/west_of_house.png") // returns "/images/west_of_house.webp"
 */
export function getWebPPath(imagePath: string): string {
  // If already WebP or not a PNG, return as-is
  if (imagePath.endsWith('.webp') || !imagePath.endsWith('.png')) {
    return imagePath;
  }
  
  return imagePath.replace(/\.png$/, '.webp');
}

/**
 * Ensures a path is in PNG format
 * 
 * @param imagePath - The image path
 * @returns The PNG version of the image path
 * 
 * @example
 * getPNGPath("/images/west_of_house.webp") // returns "/images/west_of_house.png"
 */
export function getPNGPath(imagePath: string): string {
  // If already PNG, return as-is
  if (imagePath.endsWith('.png')) {
    return imagePath;
  }
  
  // Convert WebP to PNG
  if (imagePath.endsWith('.webp')) {
    return imagePath.replace(/\.webp$/, '.png');
  }
  
  // For other formats, assume PNG
  return imagePath;
}

/**
 * Responsive image sizes configuration
 */
interface ResponsiveSizes {
  webp: {
    srcSet: string;
  };
  png: {
    srcSet: string;
  };
  sizes: string;
}

/**
 * Generates responsive image srcset for different screen sizes
 * 
 * Creates multiple image sizes for optimal loading on different devices:
 * - Small (640w): Mobile devices
 * - Medium (1024w): Tablets
 * - Large (1920w): Desktop displays
 * 
 * @param imagePath - The base image path
 * @returns Object containing WebP and PNG srcsets with sizes attribute
 * 
 * @example
 * getResponsiveSizes("/images/west_of_house.png")
 * // returns {
 * //   webp: { srcSet: "/images/west_of_house.webp 1920w, ..." },
 * //   png: { srcSet: "/images/west_of_house.png 1920w, ..." },
 * //   sizes: "(max-width: 640px) 100vw, ..."
 * // }
 */
export function getResponsiveSizes(imagePath: string): ResponsiveSizes {
  // For now, we'll use the same image for all sizes
  // In a production environment, you would generate multiple sizes during build
  // and reference them here (e.g., west_of_house-640w.png, west_of_house-1024w.png)
  
  const webpPath = getWebPPath(imagePath);
  const pngPath = getPNGPath(imagePath);
  
  // Since we don't have pre-generated responsive images yet,
  // we'll use the same image for all sizes
  // The browser will scale it appropriately
  return {
    webp: {
      srcSet: `${webpPath} 1920w`,
    },
    png: {
      srcSet: `${pngPath} 1920w`,
    },
    // Sizes attribute tells the browser how much space the image will take
    // This helps it choose the right image from srcset
    sizes: '(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 600px',
  };
}

/**
 * Preloads adjacent room images based on available exits
 * This improves transition smoothness by loading images before they're needed
 * 
 * @param adjacentRooms - Array of room names that are adjacent to the current room
 * @returns Promise that resolves when all adjacent images are preloaded
 * 
 * @example
 * await preloadAdjacentRooms(["North of House", "South of House"])
 */
export async function preloadAdjacentRooms(adjacentRooms: string[]): Promise<void> {
  // Preload up to 3 adjacent rooms to avoid excessive bandwidth usage
  const roomsToPreload = adjacentRooms.slice(0, 3);
  
  const preloadPromises = roomsToPreload.map(roomName => {
    const imagePath = mapRoomToImage(roomName);
    // Try WebP first, fall back to PNG if it fails
    return preloadImage(getWebPPath(imagePath))
      .catch(() => preloadImage(getPNGPath(imagePath)))
      .catch(() => {
        // Ignore errors for adjacent room preloading
        // They'll be handled when the user actually navigates to that room
      });
  });
  
  await Promise.all(preloadPromises);
}
