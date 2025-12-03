#!/bin/bash
# Copy room images to public directory for frontend

echo "Copying room images to public/images..."

# Create public/images directory if it doesn't exist
mkdir -p public/images

# Copy all images from images/ to public/images/
cp -r images/* public/images/

echo "✓ Images copied successfully"
echo "Total images: $(ls -1 public/images/*.png 2>/dev/null | wc -l)"
