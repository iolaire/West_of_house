# Requirements Document

## Introduction

The Grimoire Frontend is a React-based web application that presents the West of Haunted House text adventure game as an animated 3D grimoire (spellbook). Players interact with the game through text commands while experiencing atmospheric room transitions and immersive visual storytelling. The interface connects to the backend API to process commands and manage game state.

## Glossary

- **Grimoire**: An animated 3D spellbook interface that serves as the game's visual container
- **Room Image**: A visual representation of the current game location, stored in the `images/` folder
- **Dissolve Transition**: A 3-second cross-fade effect between room images when the player moves to a new location
- **Command Input**: A text field where players type natural language commands (e.g., "go north", "take lamp")
- **Game Response**: Text output from the backend API describing the result of player actions
- **Session**: A unique game instance tracked by session ID, persisted in DynamoDB
- **Backend API**: AWS Lambda functions exposed via API Gateway that process game commands

## Requirements

### Requirement 1

**User Story:** As a player, I want to see the game presented as an animated grimoire, so that I feel immersed in a magical, haunted atmosphere.

#### Acceptance Criteria

1. WHEN the application loads THEN the Grimoire SHALL render a 3D book-like interface with visible pages
2. WHEN the Grimoire is displayed THEN the Grimoire SHALL show the current room image on the left page
3. WHEN the Grimoire is displayed THEN the Grimoire SHALL show game text and command input on the right page
4. WHEN the Grimoire is idle THEN the Grimoire SHALL display subtle animations (breathing effect, page flutter, ambient glow)
5. WHERE the viewport is too small for 3D effects THEN the Grimoire SHALL adapt to a responsive 2D layout

### Requirement 2

**User Story:** As a player, I want to see smooth dissolve transitions between room images, so that location changes feel atmospheric rather than jarring.

#### Acceptance Criteria

1. WHEN the player moves to a new room THEN the Grimoire SHALL dissolve from the current room image to the new room image over 3 seconds
2. WHILE a dissolve transition is in progress THEN the Grimoire SHALL prevent new transitions from starting
3. WHEN a dissolve completes THEN the Grimoire SHALL display the new room image at full opacity
4. WHEN multiple room changes occur rapidly THEN the Grimoire SHALL queue transitions and execute them sequentially
5. WHERE no room image exists for a location THEN the Grimoire SHALL display a default haunted placeholder image

### Requirement 3

**User Story:** As a player, I want to type text commands to interact with the game, so that I can navigate, examine objects, and solve puzzles.

#### Acceptance Criteria

1. WHEN the player types a command and presses Enter THEN the Grimoire SHALL send the command to the backend API
2. WHEN the backend API responds THEN the Grimoire SHALL display the response text in the game output area
3. WHEN a command is processing THEN the Grimoire SHALL disable the input field and show a loading indicator
4. WHEN the command completes THEN the Grimoire SHALL re-enable the input field and clear it for the next command
5. WHEN the player presses the up arrow key THEN the Grimoire SHALL recall the previous command for editing

### Requirement 4

**User Story:** As a player, I want to see my command history and game responses, so that I can review what has happened and make informed decisions.

#### Acceptance Criteria

1. WHEN a command is submitted THEN the Grimoire SHALL append the command text to the game output area
2. WHEN the backend responds THEN the Grimoire SHALL append the response text below the command
3. WHEN the output area fills with text THEN the Grimoire SHALL automatically scroll to show the most recent content
4. WHEN the player scrolls up THEN the Grimoire SHALL allow reviewing previous commands and responses
5. WHEN the output area exceeds 1000 lines THEN the Grimoire SHALL trim the oldest entries to maintain performance

### Requirement 5

**User Story:** As a player, I want the game to remember my session, so that I can continue playing if I refresh the page or return later.

#### Acceptance Criteria

1. WHEN the application loads for the first time THEN the Grimoire SHALL create a new session via the backend API
2. WHEN a session is created THEN the Grimoire SHALL store the session ID in browser localStorage
3. WHEN the player refreshes the page THEN the Grimoire SHALL retrieve the session ID from localStorage and restore the game state
4. WHEN the player starts a new game THEN the Grimoire SHALL create a new session and replace the stored session ID
5. WHEN the session expires (backend TTL) THEN the Grimoire SHALL detect the error and prompt the player to start a new game

### Requirement 6

**User Story:** As a player, I want to see room images that match my current location, so that I can visualize the haunted world I'm exploring.

#### Acceptance Criteria

1. WHEN the backend API returns a room name THEN the Grimoire SHALL map the room name to the corresponding image file in the `images/` folder
2. WHEN a room image is found THEN the Grimoire SHALL preload the image before starting the dissolve transition
3. WHEN a room image fails to load THEN the Grimoire SHALL display a default haunted placeholder and log an error
4. WHEN the player moves to a new room THEN the Grimoire SHALL update the displayed image to match the new location
5. WHERE multiple rooms share similar names THEN the Grimoire SHALL use exact filename matching to select the correct image

### Requirement 7

**User Story:** As a player, I want helpful UI feedback, so that I understand the game's state and know when actions are processing.

#### Acceptance Criteria

1. WHEN a command is processing THEN the Grimoire SHALL display a loading spinner or pulsing indicator
2. WHEN an error occurs THEN the Grimoire SHALL display an error message in the game output area
3. WHEN the player types an invalid command THEN the Grimoire SHALL display the backend's error response without crashing
4. WHEN the network connection fails THEN the Grimoire SHALL display a connection error message and suggest retrying
5. WHEN the game is waiting for input THEN the Grimoire SHALL show a blinking cursor in the command input field

### Requirement 8

**User Story:** As a player, I want the grimoire interface to be accessible, so that players with disabilities can enjoy the game.

#### Acceptance Criteria

1. WHEN room images are displayed THEN the Grimoire SHALL use the `description_spooky` text as the alt attribute for accessibility
2. WHEN the player uses keyboard-only navigation THEN the Grimoire SHALL allow full game interaction without requiring a mouse
3. WHEN the player presses Tab THEN the Grimoire SHALL move focus between interactive elements in logical order
4. WHEN screen readers are used THEN the Grimoire SHALL provide ARIA labels and roles for game output, input fields, and navigation
5. WHEN the player uses keyboard-only navigation THEN the Grimoire SHALL show visible focus indicators on all interactive elements
6. WHEN text is displayed THEN the Grimoire SHALL use sufficient color contrast ratios (WCAG AA minimum 4.5:1 for body text)
7. WHERE animations cause motion sensitivity issues THEN the Grimoire SHALL respect the user's prefers-reduced-motion setting and disable dissolve transitions

### Requirement 9

**User Story:** As a developer, I want the frontend to integrate cleanly with the backend API, so that game logic remains centralized and maintainable.

#### Acceptance Criteria

1. WHEN the frontend sends a command THEN the Grimoire SHALL use the `/game` POST endpoint with session ID and command text
2. WHEN the backend responds THEN the Grimoire SHALL parse the JSON response containing room name, description, and game state
3. WHEN the backend returns an error status THEN the Grimoire SHALL handle the error gracefully and display a user-friendly message
4. WHEN the API endpoint changes THEN the Grimoire SHALL use environment variables for the API base URL
5. WHERE the backend is unavailable THEN the Grimoire SHALL display a maintenance message and prevent command submission

### Requirement 10

**User Story:** As a player, I want the grimoire interface to be visually polished, so that the game feels professional and immersive.

#### Acceptance Criteria

1. WHEN the grimoire is displayed THEN the Grimoire SHALL use a clean, book-like layout with the image on the left and text on the right
2. WHEN images are displayed THEN the Grimoire SHALL ensure images are properly sized and centered within their container
3. WHEN text is displayed THEN the Grimoire SHALL use appropriate spacing, line height, and margins for readability
4. WHEN the dissolve transition runs THEN the Grimoire SHALL use CSS transitions for smooth, hardware-accelerated animation
5. WHERE the viewport is narrow THEN the Grimoire SHALL stack the image above the text in a single-column layout

### Requirement 11

**User Story:** As a player, I want the grimoire's visual style to match the haunted atmosphere of the room images, so that the interface feels cohesive and immersive.

#### Acceptance Criteria

1. WHEN the design system is created THEN the Grimoire SHALL derive color palette from the room images in the `images/` folder
2. WHEN text is displayed THEN the Grimoire SHALL use fonts that complement the gothic, haunted aesthetic of the room artwork
3. WHEN the grimoire is styled THEN the Grimoire SHALL use colors extracted from the room images (dark purples, deep blues, aged yellows, blood reds)
4. WHEN typography is applied THEN the Grimoire SHALL use serif fonts for body text and decorative fonts for headings that match the spooky theme
5. WHERE multiple room images have different color schemes THEN the Grimoire SHALL use a unified palette that works harmoniously with all images

### Requirement 12

**User Story:** As a player, I want to see haunted descriptions that match the spooky theme, so that the text and visuals create a cohesive horror atmosphere.

#### Acceptance Criteria

1. WHEN the backend returns room data THEN the Grimoire SHALL display the `description_spooky` field under the corresponding room image
2. WHEN the backend returns object data THEN the Grimoire SHALL display the `response_spooky` field for object interactions
3. WHEN room descriptions are shown THEN the Grimoire SHALL never display `description_original` fields
4. WHEN object responses are shown THEN the Grimoire SHALL never display `response_original` fields
5. WHERE spooky variants are missing from backend data THEN the Grimoire SHALL log a warning and display a generic haunted message
