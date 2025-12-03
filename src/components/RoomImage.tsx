/**
 * RoomImage Component
 * Feature: grimoire-frontend
 * 
 * Renders a room image with opacity transitions
 * Handles image load errors with fallback
 * 
 * Requirements: 6.3, 8.1, 10.2
 */

import React, { useState } from 'react';
import { RoomImageProps, DEFAULT_ROOM_IMAGE } from '../types';

/**
 * RoomImage component
 * 
 * Displays a room image with CSS opacity transitions
 * Provides alt text for accessibility
 * Handles image load errors with fallback
 */
const RoomImage: React.FC<RoomImageProps> = ({
  src,
  alt,
  isTransitioning,
  opacity,
}) => {
  const [imageSrc, setImageSrc] = useState<string>(src);
  const [hasError, setHasError] = useState<boolean>(false);

  /**
   * Handle image load errors
   * Falls back to default haunted image
   */
  const handleError = () => {
    if (!hasError && imageSrc !== DEFAULT_ROOM_IMAGE) {
      console.error(`Failed to load image: ${imageSrc}`);
      setImageSrc(DEFAULT_ROOM_IMAGE);
      setHasError(true);
    }
  };

  /**
   * Handle successful image load
   * Resets error state
   */
  const handleLoad = () => {
    setHasError(false);
  };

  // Update image source when prop changes
  React.useEffect(() => {
    setImageSrc(src);
    setHasError(false);
  }, [src]);

  return (
    <img
      src={imageSrc}
      alt={alt}
      className={`room-image ${isTransitioning ? 'transitioning' : ''}`}
      style={{
        opacity,
        transition: `opacity ${isTransitioning ? '3s' : '0s'} ease-in-out`,
      }}
      onError={handleError}
      onLoad={handleLoad}
      loading="lazy"
    />
  );
};

export default RoomImage;
