/**
 * RoomImage Component
 * Feature: grimoire-frontend
 * 
 * Renders a room image with opacity transitions
 * Handles image load errors with fallback
 * Supports WebP format with PNG fallback for better performance
 * Implements responsive images with srcset for different screen sizes
 * 
 * Requirements: 6.2, 6.3, 8.1, 10.2
 */

import React, { useState } from 'react';
import { RoomImageProps, DEFAULT_ROOM_IMAGE } from '../types';
import { getWebPPath, getPNGPath, getResponsiveSizes } from '../utils/imageUtils';
import '../styles/RoomImage.css';

/**
 * RoomImage component
 * 
 * Displays a room image with CSS opacity transitions
 * Provides alt text for accessibility
 * Handles image load errors with fallback
 * Uses WebP format with PNG fallback for optimal performance
 * Implements responsive images for different screen sizes
 */
const RoomImage: React.FC<RoomImageProps> = ({
  src,
  alt,
  isTransitioning,
  opacity,
}) => {
  const [imageSrc, setImageSrc] = useState<string>(src);
  const [hasError, setHasError] = useState<boolean>(false);
  const [useWebP, setUseWebP] = useState<boolean>(true);

  /**
   * Handle image load errors
   * Falls back to PNG if WebP fails, then to default haunted image
   */
  const handleError = () => {
    if (!hasError) {
      // First try: WebP failed, try PNG
      if (useWebP && imageSrc !== DEFAULT_ROOM_IMAGE) {
        console.warn(`WebP failed for ${imageSrc}, falling back to PNG`);
        setUseWebP(false);
        setImageSrc(getPNGPath(src));
        return;
      }
      
      // Second try: PNG failed, use default
      if (imageSrc !== DEFAULT_ROOM_IMAGE) {
        console.error(`Failed to load image: ${imageSrc}`);
        setImageSrc(DEFAULT_ROOM_IMAGE);
        setHasError(true);
      }
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
    setUseWebP(true);
    setHasError(false);
  }, [src]);

  // Get the appropriate image path (WebP or PNG)
  const currentImagePath = useWebP ? getWebPPath(imageSrc) : getPNGPath(imageSrc);
  
  // Get responsive sizes for srcset
  const responsiveSizes = getResponsiveSizes(currentImagePath);

  return (
    <picture>
      {/* WebP source with responsive sizes */}
      {useWebP && (
        <source
          type="image/webp"
          srcSet={responsiveSizes.webp.srcSet}
          sizes={responsiveSizes.sizes}
        />
      )}
      
      {/* PNG fallback with responsive sizes */}
      <source
        type="image/png"
        srcSet={responsiveSizes.png.srcSet}
        sizes={responsiveSizes.sizes}
      />
      
      {/* Default img element for browsers that don't support picture */}
      <img
        src={currentImagePath}
        alt={alt}
        className={`room-image ${isTransitioning ? 'transitioning' : ''}`}
        style={{
          opacity,
          transition: `opacity ${isTransitioning ? '3s' : '0s'} ease-in-out`,
        }}
        onError={handleError}
        onLoad={handleLoad}
        loading="lazy"
        role="presentation"
        aria-hidden="true"
      />
    </picture>
  );
};

export default RoomImage;
