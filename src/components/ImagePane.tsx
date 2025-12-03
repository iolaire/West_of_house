/**
 * ImagePane Component
 * Feature: grimoire-frontend
 * 
 * Displays room images with 3-second dissolve transitions
 * Handles transition queuing, image preloading, and error fallbacks
 * 
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 6.2, 6.4
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { ImagePaneProps, TRANSITION_DURATION, DEFAULT_ROOM_IMAGE } from '../types';
import { mapRoomToImage, preloadImage } from '../utils/imageUtils';
import RoomImage from './RoomImage';
import '../styles/ImagePane.css';

/**
 * ImagePane component with dissolve transitions
 * 
 * Manages room image display with smooth 3-second cross-fade transitions
 * Queues multiple transitions and executes them sequentially
 * Preloads images before starting transitions
 */
const ImagePane: React.FC<ImagePaneProps> = ({
  roomName,
  roomDescription,
  transitionDuration = TRANSITION_DURATION,
}) => {
  // Current displayed image - initialize with the room's image if provided
  const [currentImage, setCurrentImage] = useState<string>(() => 
    roomName ? mapRoomToImage(roomName) : DEFAULT_ROOM_IMAGE
  );
  
  // Next image to transition to (null when not transitioning)
  const [nextImage, setNextImage] = useState<string | null>(null);
  
  // Whether a transition is currently in progress
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);
  
  // Queue of pending room transitions
  const [, setTransitionQueue] = useState<string[]>([]);
  
  // Ref to track the current transition timeout
  const transitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Ref to track if component is mounted (for cleanup)
  const isMountedRef = useRef<boolean>(true);
  
  // Ref to track if currently transitioning (avoids stale closure issues)
  const isTransitioningRef = useRef<boolean>(false);

  /**
   * Starts a transition to a new room image
   * If a transition is in progress, queues the new transition
   */
  const startTransition = useCallback(
    (newRoomName: string, skipPreload: boolean = false) => {
      // Map room name to image path
      const newImagePath = mapRoomToImage(newRoomName);

      // If already transitioning, queue this transition
      if (isTransitioningRef.current) {
        setTransitionQueue((prev) => [...prev, newRoomName]);
        // Preload in background for queued transitions
        if (!skipPreload) {
          preloadImage(newImagePath).catch(() => {
            // Ignore errors, they'll be handled when transition actually starts
          });
        }
        return;
      }

      // Wait for preload to complete before starting transition
      const preloadPromise = skipPreload ? Promise.resolve() : preloadImage(newImagePath);
      preloadPromise
        .then(() => {
          if (!isMountedRef.current) return;

          // Start the transition
          isTransitioningRef.current = true;
          setIsTransitioning(true);
          setNextImage(newImagePath);

          // After transition duration, complete the transition
          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;

            setCurrentImage(newImagePath);
            setNextImage(null);
            isTransitioningRef.current = false;
            setIsTransitioning(false);

            // Process next item in queue
            setTransitionQueue((prev) => {
              if (prev.length > 0) {
                const [next, ...rest] = prev;
                // Start next transition on next tick, skipping preload since we already did it
                if (next) {
                  setTimeout(() => startTransition(next, true), 0);
                }
                return rest;
              }
              return prev;
            });
          }, transitionDuration);
        })
        .catch((error) => {
          // Image failed to load, use default image
          console.error('Failed to preload image:', error);
          
          if (!isMountedRef.current) return;

          // Use default image instead
          const fallbackPath = DEFAULT_ROOM_IMAGE;
          
          isTransitioningRef.current = true;
          setIsTransitioning(true);
          setNextImage(fallbackPath);

          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;

            setCurrentImage(fallbackPath);
            setNextImage(null);
            isTransitioningRef.current = false;
            setIsTransitioning(false);

            // Process next item in queue
            setTransitionQueue((prev) => {
              if (prev.length > 0) {
                const [next, ...rest] = prev;
                // Start next transition on next tick, skipping preload since we already did it
                if (next) {
                  setTimeout(() => startTransition(next, true), 0);
                }
                return rest;
              }
              return prev;
            });
          }, transitionDuration);
        });
    },
    [transitionDuration]
  );

  // Ref to track previous room name to avoid duplicate transitions
  const prevRoomNameRef = useRef<string>('');

  /**
   * Effect to handle room changes
   * Triggers transition when roomName changes (but not on initial mount)
   */
  useEffect(() => {
    // Skip transition on initial mount (when prevRoomNameRef is empty)
    if (prevRoomNameRef.current === '') {
      prevRoomNameRef.current = roomName || '';
      return;
    }
    
    if (roomName && roomName !== prevRoomNameRef.current) {
      prevRoomNameRef.current = roomName;
      startTransition(roomName);
    }
  }, [roomName, startTransition]);

  /**
   * Cleanup effect
   * Clears timeout and marks component as unmounted
   */
  useEffect(() => {
    // Mark as mounted
    isMountedRef.current = true;
    
    return () => {
      isMountedRef.current = false;
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div 
      className="image-pane"
      role="img"
      aria-label={`Room image: ${roomName || 'Unknown location'}. ${roomDescription}`}
    >
      {/* Current image (fading out during transition) */}
      <RoomImage
        src={currentImage}
        alt={roomDescription}
        isTransitioning={isTransitioning}
        opacity={isTransitioning ? 0 : 1}
      />
      
      {/* Next image (fading in during transition) */}
      {nextImage && (
        <RoomImage
          src={nextImage}
          alt={roomDescription}
          isTransitioning={isTransitioning}
          opacity={isTransitioning ? 1 : 0}
        />
      )}
      
      {/* Screen reader announcement for room changes */}
      <div className="visually-hidden" role="status" aria-live="polite">
        {isTransitioning ? `Transitioning to ${roomName || 'new location'}` : `Now viewing ${roomName || 'current location'}`}
      </div>
    </div>
  );
};

export default ImagePane;
