# Implementation Plan

- [x] 1. Set up React project structure and dependencies
  - Initialize React project with Vite
  - Install required dependencies (React 18+, TypeScript)
  - Configure TypeScript with strict mode
  - Set up CSS Modules or Styled Components
  - Create directory structure (components, services, hooks, types)
  - Configure environment variables for API endpoints
  - _Requirements: 9.4_

- [x] 2. Create core data models and types
  - Define TypeScript interfaces for AppState, OutputLine, GameResponse
  - Define API client types (SessionExpiredError, ApiError)
  - Define component prop types
  - Create constants for transition duration, cache keys, etc.
  - _Requirements: 9.2_

- [x] 3. Implement API client service
  - Create GameApiClient class with baseUrl configuration
  - Implement createSession() method for new game sessions
  - Implement sendCommand() method for game commands
  - Add error handling for network errors, session expiration, API errors
  - Add request timeout configuration
  - _Requirements: 3.1, 5.1, 9.1, 9.3, 9.5_

- [x] 3.1 Write property test for API client
  - **Property 18: Response Parsing**
  - **Validates: Requirements 9.2**

- [x] 4. Implement session management with localStorage
  - Create SessionManager context provider
  - Implement session creation and storage in localStorage
  - Implement session retrieval on app load
  - Handle session expiration detection
  - Provide session context to child components
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 4.1 Write property test for session storage
  - **Property 12: Session Storage**
  - **Validates: Requirements 5.2**

- [x] 5. Create room image mapping utility
  - Implement mapRoomToImage() function (room name → filename)
  - Handle special characters and spaces in room names
  - Add fallback to default_haunted.png for missing images
  - Create image preloading utility function
  - Log non-mappable rooms (rooms without matching images) to a text file for debugging
  - Maintain a list of unmapped rooms to help identify missing images
  - _Requirements: 6.1, 6.2, 6.3_

- [x] 5.1 Write property test for room name mapping
  - **Property 13: Room Name to Image Mapping**
  - **Validates: Requirements 6.1**

- [x] 6. Implement ImagePane component with dissolve transitions
  - Create ImagePane component with state management
  - Implement 3-second dissolve transition logic
  - Add transition queue for rapid room changes
  - Implement image preloading before transitions
  - Handle transition atomicity (prevent interruptions)
  - Add error handling for failed image loads
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.2, 6.4_

- [x] 6.1 Write property test for transition duration
  - **Property 1: Transition Duration Consistency**
  - **Validates: Requirements 2.1**

- [x] 6.2 Write property test for transition atomicity
  - **Property 2: Transition Atomicity**
  - **Validates: Requirements 2.2**

- [x] 6.3 Write property test for transition completion
  - **Property 3: Transition Completion State**
  - **Validates: Requirements 2.3**

- [x] 6.4 Write property test for transition queue ordering
  - **Property 4: Transition Queue Ordering**
  - **Validates: Requirements 2.4**

- [x] 6.5 Write property test for image preloading
  - **Property 14: Image Preloading**
  - **Validates: Requirements 6.2**

- [x] 6.6 Write property test for image update synchronization
  - **Property 15: Image Update Synchronization**
  - **Validates: Requirements 6.4**

- [x] 7. Create RoomImage component
  - Implement image rendering with alt text from description_spooky
  - Add CSS transition for opacity changes
  - Handle image load errors with fallback
  - Apply proper sizing and centering styles
  - Add lazy loading attribute
  - _Requirements: 6.3, 8.1, 10.2_

- [x] 7.1 Write property test for alt text
  - **Property 17: Image Alt Text**
  - **Validates: Requirements 8.1**

- [x] 8. Implement GameOutput component
  - Create scrollable output area for command history
  - Render OutputLine components for commands and responses
  - Implement auto-scroll to bottom on new content
  - Allow manual scrolling to review history
  - Implement 1000-line limit with trimming of oldest entries
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 8.1 Write property test for command output appending
  - **Property 8: Command Output Appending**
  - **Validates: Requirements 4.1**

- [x] 8.2 Write property test for response output ordering
  - **Property 9: Response Output Ordering**
  - **Validates: Requirements 4.2**

- [x] 8.3 Write property test for auto-scroll behavior
  - **Property 10: Auto-scroll Behavior**
  - **Validates: Requirements 4.3**

- [x] 8.4 Write property test for output line limit
  - **Property 11: Output Line Limit**
  - **Validates: Requirements 4.5**

- [x] 9. Create CommandInput component
  - Implement text input field with Enter key submission
  - Add command history navigation with up arrow key
  - Clear input after command submission
  - Disable input during command processing
  - Show blinking cursor when enabled
  - _Requirements: 3.1, 3.4, 3.5_

- [x] 9.1 Write property test for input state after completion
  - **Property 7: Input State After Completion**
  - **Validates: Requirements 3.4**

- [x] 10. Implement LoadingIndicator component
  - Create pulsing or spinning indicator
  - Show/hide based on isLoading prop
  - Position near command input
  - _Requirements: 3.3, 7.1_

- [x] 10.1 Write property test for input state during processing
  - **Property 6: Input State During Processing**
  - **Validates: Requirements 3.3**

- [x] 11. Create GrimoireContainer component
  - Implement two-column grid layout (image left, text right)
  - Manage overall game state (currentRoom, roomImage, gameOutput)
  - Coordinate image transitions with text updates
  - Handle responsive layout for narrow viewports
  - Integrate ImagePane, GameOutput, CommandInput, LoadingIndicator
  - _Requirements: 1.2, 1.3, 1.5, 10.1, 10.5_

- [x] 12. Implement command submission flow
  - Connect CommandInput to API client
  - Display command in GameOutput
  - Send command to backend API
  - Parse response and extract description_spooky, response_spooky
  - Display response in GameOutput
  - Trigger room image transition if room changed
  - Handle errors and display error messages
  - _Requirements: 3.1, 3.2, 4.1, 4.2, 7.2, 12.1, 12.2_

- [x] 12.1 Write property test for API response display
  - **Property 5: API Response Display**
  - **Validates: Requirements 3.2**

- [x] 12.2 Write property test for error message display
  - **Property 16: Error Message Display**
  - **Validates: Requirements 7.2**

- [x] 12.3 Write property test for spooky description display
  - **Property 19: Spooky Description Display**
  - **Validates: Requirements 12.1**

- [x] 12.4 Write property test for spooky response display
  - **Property 20: Spooky Response Display**
  - **Validates: Requirements 12.2**

- [x] 12.5 Write property test for original description exclusion
  - **Property 21: Original Description Exclusion**
  - **Validates: Requirements 12.3**

- [x] 12.6 Write property test for original response exclusion
  - **Property 22: Original Response Exclusion**
  - **Validates: Requirements 12.4**

- [x] 13. Create App component with error boundary
  - Set up SessionManager context provider
  - Initialize session on mount
  - Wrap application in ErrorBoundary
  - Render GrimoireContainer
  - _Requirements: 5.1_

- [ ] 14. Implement visual design system
  - Create CSS variables for color palette (WCAG AA compliant)
  - Define typography system (Crimson Text, Cinzel fonts)
  - Set up spacing system and layout breakpoints
  - Create component styles (grimoire-container, image-pane, text-pane)
  - Add focus indicators for accessibility
  - Implement prefers-reduced-motion support
  - _Requirements: 8.5, 8.6, 8.7, 10.3, 10.4, 11.1, 11.2, 11.3, 11.4_

- [ ] 15. Implement accessibility features
  - Add ARIA labels and roles to all interactive elements
  - Ensure keyboard navigation with Tab key
  - Add visible focus indicators
  - Test with screen readers
  - Verify color contrast ratios
  - Add prefers-reduced-motion CSS media query
  - _Requirements: 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ] 16. Optimize images for performance and cost
  - Implement lazy loading for room images
  - Add image preloading for adjacent rooms
  - Configure browser caching headers (1 year)
  - Compress images to WebP format with PNG fallback
  - Add responsive images with srcset
  - _Requirements: 6.2_

- [ ] 17. Configure Amplify deployment
  - Create amplify.yml configuration file
  - Set up environment variables for API endpoints
  - Configure build commands and artifact paths
  - Set up cache headers for static assets
  - Test deployment to sandbox environment
  - _Requirements: 9.4_

- [ ] 18. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Deploy to production
  - Merge to production branch
  - Monitor Amplify build pipeline
  - Verify deployment success
  - Test live application
  - Monitor CloudWatch metrics
  - _Requirements: All_
