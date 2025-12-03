# Image Utilities

This module provides utilities for mapping room names to image files and preloading images for smooth transitions.

## Functions

### `mapRoomToImage(roomName: string): string`

Maps a room name from the backend to its corresponding image file path.

**Features:**
- Converts room names to snake_case filenames
- Handles special characters and spaces
- Returns default image for empty or invalid room names
- Collapses multiple underscores to single underscore
- Removes leading/trailing underscores

**Examples:**
```typescript
mapRoomToImage("West of House")  // "/images/west_of_house.png"
mapRoomToImage("Living Room")    // "/images/living_room.png"
mapRoomToImage("Kitchen")        // "/images/kitchen.png"
mapRoomToImage("")               // "/images/default_haunted.png"
mapRoomToImage("!!!")            // "/images/default_haunted.png"
```

### `preloadImage(imagePath: string): Promise<void>`

Preloads an image to ensure smooth transitions without loading delays.

**Features:**
- Returns a Promise that resolves when image is loaded
- Tracks unmapped rooms (images that fail to load)
- Logs warnings for missing images

**Example:**
```typescript
try {
  await preloadImage("/images/west_of_house.png");
  // Image is now loaded and cached
} catch (error) {
  // Image failed to load, use fallback
  console.error("Failed to load image");
}
```

### `getUnmappedRooms(): string[]`

Returns a sorted array of room names that failed to load during the session.

**Example:**
```typescript
const unmapped = getUnmappedRooms();
console.log("Missing images for:", unmapped);
// ["Mysterious Cave", "Secret Passage"]
```

### `clearUnmappedRooms(): void`

Clears the list of unmapped rooms. Useful for testing or resetting tracking.

### `exportUnmappedRoomsToText(): string`

Exports the unmapped rooms list as a formatted text report.

**Example:**
```typescript
const report = exportUnmappedRoomsToText();
console.log(report);
// Unmapped Rooms Report
// ==================================================
// Generated: 2024-12-02T20:24:57.000Z
// Total unmapped rooms: 2
//
// 1. Mysterious Cave
// 2. Secret Passage
```

### `downloadUnmappedRoomsReport(): void`

Downloads the unmapped rooms report as a text file. Useful for developers to identify missing images.

**Example:**
```typescript
// Call this in the browser console to download a report
downloadUnmappedRoomsReport();
// Downloads: unmapped-rooms-1733174697000.txt
```

## Usage in Components

### ImagePane Component

```typescript
import { mapRoomToImage, preloadImage } from '../utils';

function ImagePane({ roomName }: { roomName: string }) {
  const [imagePath, setImagePath] = useState('');

  useEffect(() => {
    const path = mapRoomToImage(roomName);
    
    // Preload before showing
    preloadImage(path)
      .then(() => setImagePath(path))
      .catch(() => setImagePath(DEFAULT_ROOM_IMAGE));
  }, [roomName]);

  return <img src={imagePath} alt={roomName} />;
}
```

## Testing

The image utilities are tested with property-based tests using fast-check:

- **Property 13: Room Name to Image Mapping** - Validates that any room name maps to a valid image path
- Tests for special characters, whitespace, case-insensitivity, and determinism
- 100+ test cases per property to ensure robustness

Run tests:
```bash
npm test -- src/test/imageUtils.property.test.ts
```

## Debugging Missing Images

If you encounter missing room images:

1. Check the browser console for warnings:
   ```
   [Image Mapping] Failed to load image for room: "Mysterious Cave"
     Attempted path: /images/mysterious_cave.png
     Falling back to: /images/default_haunted.png
   ```

2. Get the list of unmapped rooms:
   ```typescript
   import { getUnmappedRooms } from './utils';
   console.log(getUnmappedRooms());
   ```

3. Download a report:
   ```typescript
   import { downloadUnmappedRoomsReport } from './utils';
   downloadUnmappedRoomsReport();
   ```

4. Add the missing images to `public/images/` with the correct filename format (snake_case, lowercase, .png extension)

## Image Naming Convention

Images should follow this naming convention:
- Lowercase letters only
- Spaces replaced with underscores
- Special characters removed
- No leading/trailing underscores
- `.png` extension

**Examples:**
- "West of House" → `west_of_house.png`
- "Living Room" → `living_room.png`
- "Dead End #1" → `dead_end_1.png`
- "East-West Passage" → `eastwest_passage.png`
