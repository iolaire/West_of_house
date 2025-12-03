#!/bin/bash

# Convert PNG images to WebP format for better performance
# This script converts all PNG images in public/images/ to WebP format
# while preserving the original PNG files as fallbacks

set -e

echo "🖼️  Converting PNG images to WebP format..."

# Check if cwebp is installed
if ! command -v cwebp &> /dev/null; then
    echo "⚠️  cwebp is not installed. Skipping WebP conversion."
    echo "   To install cwebp:"
    echo "   - macOS: brew install webp"
    echo "   - Ubuntu/Debian: sudo apt-get install webp"
    echo "   - Windows: Download from https://developers.google.com/speed/webp/download"
    echo ""
    echo "   Continuing without WebP conversion (PNG fallbacks will be used)..."
    exit 0
fi

# Source and destination directories
SOURCE_DIR="public/images"
DEST_DIR="public/images"

# Create destination directory if it doesn't exist
mkdir -p "$DEST_DIR"

# Counter for converted images
converted=0
skipped=0

# Convert each PNG to WebP
for png_file in "$SOURCE_DIR"/*.png; do
    # Skip if no PNG files found
    if [ ! -f "$png_file" ]; then
        echo "No PNG files found in $SOURCE_DIR"
        exit 0
    fi
    
    # Get filename without extension
    filename=$(basename "$png_file" .png)
    webp_file="$DEST_DIR/${filename}.webp"
    
    # Skip if WebP already exists and is newer than PNG
    if [ -f "$webp_file" ] && [ "$webp_file" -nt "$png_file" ]; then
        echo "⏭️  Skipping $filename (WebP is up to date)"
        ((skipped++))
        continue
    fi
    
    # Convert PNG to WebP with quality 85 (good balance of size and quality)
    echo "🔄 Converting $filename.png to WebP..."
    cwebp -q 85 "$png_file" -o "$webp_file" > /dev/null 2>&1
    
    if [ $? -eq 0 ]; then
        # Get file sizes for comparison
        png_size=$(du -h "$png_file" | cut -f1)
        webp_size=$(du -h "$webp_file" | cut -f1)
        echo "✅ Converted $filename: $png_size (PNG) → $webp_size (WebP)"
        ((converted++))
    else
        echo "❌ Failed to convert $filename"
    fi
done

echo ""
echo "✨ Conversion complete!"
echo "   Converted: $converted images"
echo "   Skipped: $skipped images (already up to date)"
echo ""
echo "💡 Note: PNG files are preserved as fallbacks for older browsers"
