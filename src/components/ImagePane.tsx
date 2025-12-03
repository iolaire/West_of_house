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
  // Current displayed image
  const [currentImage, setCurrentImage] = useState<string>(DEFAULT_ROOM_IMAGE);
  
  // Next image to transition to (null when not transitioning)
  const [nextImage, setNextImage] = useState<string | null>(null);
  
  // Whether a transition is currently in progress
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);
  
  // Queue of pending room transitions
  const [transitionQueue, setTransitionQueue] = useState<string[]>([]);
  
  // Ref to track the current transition timeout
  const transitionTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Ref to track if component is mounted (for cleanup)
  const isMountedRef = useRef<boolean>(true);

  /**
   * Starts a transition to a new room image
   * If a transition is in progress, queues the new transition
   */
  const startTransition = useCallback(
    (newRoomName: string) => {
      // If already transitioning, queue this transition
      if (isTransitioning) {
        setTransitionQueue((prev) => [...prev, newRoomName]);
        return;
      }

      // Map room name to image path
      const newImagePath = mapRoomToImage(newRoomName);

      // Preload the image before starting transition
      preloadImage(newImagePath)
        .then(() => {
          if (!isMountedRef.current) return;

          // Start the transition
          setIsTransitioning(true);
          setNextImage(newImagePath);

          // After transition duration, complete the transition
          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;

            setCurrentImage(newImagePath);
            setNextImage(null);
            setIsTransitioning(false);

            // Process next item in queue
            setTransitionQueue((prev) => {
              if (prev.length > 0) {
                const [next, ...rest] = prev;
                // Start next transition on next tick
                setTimeout(() => startTransition(next), 0);
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
          
          setIsTransitioning(true);
          setNextImage(fallbackPath);

          transitionTimeoutRef.current = setTimeout(() => {
            if (!isMountedRef.current) return;

            setCurrentImage(fallbackPath);
            setNextImage(null);
            setIsTransitioning(false);

            // Process next item in queue
            setTransitionQueue((prev) => {
              if (prev.length > 0) {
                const [next, ...rest] = prev;
                setTimeout(() => startTransition(next), 0);
                return rest;
              }
              return prev;
            });
          }, transitionDuration);
        });
    },
    [isTransitioning, transitionDuration]
  );

  /**
   * Effect to handle room changes
   * Triggers transition when roomName changes
   */
  useEffect(() => {
    if (roomName) {
      startTransition(roomName);
    }
  }, [roomName, startTransition]);

  /**
   * Cleanup effect
   * Clears timeout and marks component as unmounted
   */
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
      if (transitionTimeoutRef.current) {
        clearTimeout(transitionTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="image-pane">
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
    </div>
  );
};

export default ImagePane;
