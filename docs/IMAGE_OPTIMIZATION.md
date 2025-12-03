# Image Optimization Guide

This document describes the image optimization strategies implemented for the West of Haunted House frontend to improve performance and reduce costs.

## Overview

The frontend implements multiple image optimization techniques to reduce bandwidth usage and improve loading performance:

1. **Lazy Loading**: Images load only when needed
2. **WebP Format**: Modern image format with 75% smaller file sizes
3. **Browser Caching**: Long-term caching reduces repeat downloads
4. **Responsive Images**: Appropriate sizes for different devices
5. **Adjacent Room Preloading**: Smooth transitions by preloading nearby rooms

## Implementation Details

### 1. Lazy Loading

**Status**: ✅ Implemented

Images use the native `loading="lazy"` attribute, which tells the browser to defer loading images until they're near the viewport.

**Benefits**:
- Reduces initial page load time
- Saves bandwidth for images that are never viewed
- Improves Core Web Vitals scores

**Code Location**: `src/components/RoomImage.tsx`

```typescript
<img loading="lazy" ... />
```

### 2. WebP Format with PNG Fallback

**Status**: ✅ Implemented

The application serves images in WebP format (75% smaller than PNG) with automatic fallback to PNG for older browsers.

**Benefits**:
- 75% reduction in image file size
- Faster loading times
- Significant cost savings on data transfer

**Implementation**:
- Build script converts PNG to WebP: `npm run convert-webp`
- `<picture>` element provides format negotiation
- Automatic fallback to PNG if WebP fails

**Code Locations**:
- Conversion script: `scripts/convert-images-to-webp.sh`
- Component: `src/components/RoomImage.tsx`
- Utilities: `src/utils/imageUtils.ts`

**Usage**:
```bash
# Convert images during build
npm run build

# Or manually convert
npm run convert-webp
```

**Requirements**:
- Install `cwebp` tool:
  - macOS: `brew install webp`
  - Ubuntu/Debian: `sudo apt-get install webp`
  - Windows: Download from https://developers.google.com/speed/webp/download

### 3. Browser Caching

**Status**: ✅ Implemented

Static assets are cached for 1 year with immutable flag, while HTML is never cached.

**Benefits**:
- 50% reduction in data transfer for returning players
- Instant loading for cached images
- Reduced server load

**Configuration**:
- Amplify config: `amplify.yml` (customHeaders section)
- Static headers: `public/_headers`

**Cache Headers**:
```
Images:     Cache-Control: public, max-age=31536000, immutable
JS/CSS:     Cache-Control: public, max-age=31536000, immutable
HTML:       Cache-Control: public, max-age=0, must-revalidate
```

### 4. Responsive Images

**Status**: ✅ Implemented (basic)

Images use `srcset` and `sizes` attributes to serve appropriate sizes for different devices.

**Benefits**:
- Smaller images for mobile devices
- Reduced bandwidth on mobile networks
- Better performance on all devices

**Code Location**: `src/utils/imageUtils.ts` (`getResponsiveSizes()`)

**Current Implementation**:
- Single image size with responsive scaling
- Browser handles scaling based on viewport

**Future Enhancement**:
- Generate multiple image sizes during build (640w, 1024w, 1920w)
- Serve optimal size for each device

### 5. Adjacent Room Preloading

**Status**: ✅ Implemented

The application preloads images for adjacent rooms (up to 3) to ensure smooth transitions.

**Benefits**:
- Instant transitions when moving to adjacent rooms
- Better user experience
- No loading delays during gameplay

**Code Location**: `src/utils/imageUtils.ts` (`preloadAdjacentRooms()`)

**Usage**:
```typescript
// Preload images for rooms the player can move to
await preloadAdjacentRooms(["North of House", "South of House"]);
```

## Cost Impact

### Before Optimization
- Average image size: 2 MB (PNG)
- Images per game: 10 rooms visited
- Data transfer per game: 20 MB
- Monthly cost (1000 games): ~$3.00

### After Optimization
- Average image size: 500 KB (WebP)
- First visit: 10 rooms × 500 KB = 5 MB
- Return visit: 0 MB (cached)
- Assuming 50% returning players:
  - New players: 500 games × 5 MB = 2.5 GB
  - Returning players: 500 games × 0 MB = 0 GB
  - Total: 2.5 GB
- Monthly cost (1000 games): ~$0.38

**Total Savings**: ~$2.62/month (87% reduction)

## Performance Metrics

### Expected Improvements
- **Initial Load Time**: 60% faster (lazy loading + WebP)
- **Transition Time**: Instant (preloading)
- **Bandwidth Usage**: 75% reduction (WebP + caching)
- **Lighthouse Score**: +20 points (performance)

### Monitoring
Monitor these metrics in production:
- CloudWatch: Data transfer metrics
- Browser DevTools: Network tab
- Lighthouse: Performance audits
- Real User Monitoring: Core Web Vitals

## Build Process

### Development
```bash
# Start dev server (no WebP conversion)
npm run dev
```

### Production Build
```bash
# Full build with optimizations
npm run build

# Steps:
# 1. Copy images from images/ to public/images/
# 2. Convert PNG to WebP (preserves PNG as fallback)
# 3. Compile TypeScript
# 4. Build with Vite
# 5. Output to dist/ directory
```

### Manual WebP Conversion
```bash
# Convert images without full build
npm run convert-webp
```

## Browser Support

### WebP Support
- ✅ Chrome 23+
- ✅ Firefox 65+
- ✅ Safari 14+
- ✅ Edge 18+
- ❌ IE 11 (falls back to PNG)

### Lazy Loading Support
- ✅ Chrome 77+
- ✅ Firefox 75+
- ✅ Safari 15.4+
- ✅ Edge 79+
- ❌ Older browsers (loads immediately)

## Troubleshooting

### WebP Conversion Fails
**Problem**: `cwebp: command not found`

**Solution**: Install WebP tools
```bash
# macOS
brew install webp

# Ubuntu/Debian
sudo apt-get install webp
```

### Images Not Caching
**Problem**: Images reload on every page visit

**Solution**: Check cache headers in browser DevTools
1. Open Network tab
2. Reload page
3. Check response headers for `Cache-Control`
4. Verify Amplify customHeaders in `amplify.yml`

### WebP Not Loading
**Problem**: Browser shows PNG instead of WebP

**Solution**: Check browser support
1. Open DevTools Console
2. Check for WebP load errors
3. Verify WebP files exist in `public/images/`
4. Check `<picture>` element in DOM

### Large Bundle Size
**Problem**: Build output is too large

**Solution**: Verify images are in `public/` not `src/`
- Images in `public/` are served as static assets
- Images in `src/` are bundled with JavaScript
- Move images to `public/images/` directory

## Future Enhancements

### Phase 2 Optimizations
1. **Multiple Image Sizes**: Generate 640w, 1024w, 1920w variants
2. **AVIF Format**: Even better compression than WebP
3. **CDN Integration**: CloudFront for global distribution
4. **Image Sprites**: Combine small images into sprites
5. **Progressive Loading**: Blur-up technique for better UX
6. **Service Worker**: Offline caching with Cache API

### Advanced Techniques
1. **Adaptive Quality**: Adjust quality based on network speed
2. **Smart Preloading**: ML-based prediction of next room
3. **Image Placeholders**: Low-quality placeholders while loading
4. **Intersection Observer**: More sophisticated lazy loading

## References

- [WebP Documentation](https://developers.google.com/speed/webp)
- [Responsive Images Guide](https://developer.mozilla.org/en-US/docs/Learn/HTML/Multimedia_and_embedding/Responsive_images)
- [Browser Caching Best Practices](https://web.dev/http-cache/)
- [Lazy Loading Images](https://web.dev/lazy-loading-images/)
- [AWS Amplify Custom Headers](https://docs.aws.amazon.com/amplify/latest/userguide/custom-headers.html)
