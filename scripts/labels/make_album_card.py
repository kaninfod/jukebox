#!/usr/bin/env python3
"""
Album Card Generator

Creates a credit card-sized (portrait) image with:
- Upper part: Album cover (square, fills width)
- Lower part: Album title and artist name with extended cover color

Usage:
    python make_album_card.py <album_id>
    
Example:
    python make_album_card.py al-444
"""

import sys
import os
import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from colorsys import rgb_to_hsv, hsv_to_rgb
import textwrap

# Configuration
API_BASE_URL = "https://jukeplayer.hinge.icu"
OUTPUT_DIR = os.getcwd()

# Credit card dimensions (portrait)
CARD_WIDTH = 540
CARD_HEIGHT = 860

# Cover dimensions (square, fills width)
COVER_SIZE = CARD_WIDTH
LOWER_HEIGHT = CARD_HEIGHT - COVER_SIZE

# Text configuration
TEXT_PADDING = 20
TITLE_FONT_SIZE = 36
ARTIST_FONT_SIZE = 28
LINE_SPACING = 10


def get_system_font(size):
    """Get a system font or fallback to default."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Windows/Fonts/arial.ttf",
    ]
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
    
    return ImageFont.load_default()


def fetch_cover(album_id):
    """Fetch album cover image from API."""
    url = f"{API_BASE_URL}/api/subsonic/cover/{album_id}"
    print(f"Fetching cover from: {url}")
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    return Image.open(BytesIO(response.content)).convert("RGB")


def fetch_album_info(album_id):
    """Fetch album info (title, artist) from API."""
    url = f"{API_BASE_URL}/api/subsonic/album_info/{album_id}"
    print(f"Fetching album info from: {url}")
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    title = data.get("album", "Unknown Album")
    artist = data.get("artist", "Unknown Artist")
    
    return title, artist


def get_dominant_color(image):
    """
    Extract a dominant color from the bottom portion of the image.
    Average the bottom 10% of pixels to get a representative color.
    """
    width, height = image.size
    bottom_section = image.crop((0, int(height * 0.98), width, height))
    
    # Resize to small image and get average color
    bottom_section_small = bottom_section.resize((1, 1))
    pixel = bottom_section_small.getpixel((0, 0))
    
    return pixel


def get_complementary_color(rgb_color):
    """
    Calculate the complementary color by rotating hue by 180 degrees,
    with enhanced saturation and adjusted brightness for better contrast.
    """
    # Normalize RGB to 0-1 range
    r, g, b = [x / 255.0 for x in rgb_color]
    
    # Convert to HSV
    h, s, v = rgb_to_hsv(r, g, b)
    
    # Rotate hue by 180 degrees (0.5 in normalized form)
    h = (h + 0.5) % 1.0
    
    # Boost saturation for more vibrant text
    s = min(1.0, s + 0.3)
    
    # Adjust brightness: if background is dark, make text bright; if light, make it darker
    if v < 0.5:
        # Dark background - make text brighter
        v = 0.9
    else:
        # Light background - make text darker
        v = 0.3
    
    # Convert back to RGB
    r, g, b = hsv_to_rgb(h, s, v)
    
    # Convert back to 0-255 range and return as tuple of integers
    return tuple(int(x * 255) for x in (r, g, b))


def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    lines = []
    words = text.split()
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return lines


def create_album_card(album_id):
    """Create the album card image."""
    
    print(f"Creating album card for: {album_id}")
    
    # Fetch data
    print("Step 1: Fetching album cover...")
    cover = fetch_cover(album_id)
    
    print("Step 2: Fetching album info...")
    title, artist = fetch_album_info(album_id)
    
    # Resize cover to fit
    print("Step 3: Processing cover image...")
    cover = cover.resize((COVER_SIZE, COVER_SIZE), Image.Resampling.LANCZOS)
    
    # Get dominant color
    dominant_color = get_dominant_color(cover)
    print(f"Dominant color: {dominant_color}")
    
    # Get complementary color for text
    text_color = get_complementary_color(dominant_color)
    print(f"Text color: {text_color}")
    
    # Create new image
    print("Step 4: Creating card image...")
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), dominant_color)
    
    # Paste cover at top
    card.paste(cover, (0, 0))
    
    # Draw text on lower part
    print("Step 5: Adding text...")
    draw = ImageDraw.Draw(card)
    
    title_font = get_system_font(TITLE_FONT_SIZE)
    artist_font = get_system_font(ARTIST_FONT_SIZE)
    
    # Calculate text area
    text_area_width = CARD_WIDTH - (2 * TEXT_PADDING)
    text_start_y = COVER_SIZE + TEXT_PADDING
    
    # Wrap and draw title
    title_lines = wrap_text(title, title_font, text_area_width, draw)
    current_y = text_start_y
    
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        line_height = bbox[3] - bbox[1]
        
        # Center horizontally
        line_bbox = draw.textbbox((0, 0), line, font=title_font)
        line_width = line_bbox[2] - line_bbox[0]
        x = (CARD_WIDTH - line_width) // 2
        
        draw.text((x, current_y), line, fill=text_color, font=title_font)
        current_y += line_height + LINE_SPACING
    
    # Add space between title and artist
    current_y += 10
    
    # Wrap and draw artist
    artist_lines = wrap_text(artist, artist_font, text_area_width, draw)
    
    for line in artist_lines:
        bbox = draw.textbbox((0, 0), line, font=artist_font)
        line_height = bbox[3] - bbox[1]
        
        # Center horizontally
        line_bbox = draw.textbbox((0, 0), line, font=artist_font)
        line_width = line_bbox[2] - line_bbox[0]
        x = (CARD_WIDTH - line_width) // 2
        
        draw.text((x, current_y), line, fill=text_color, font=artist_font)
        current_y += line_height + LINE_SPACING
    
    # Save output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, f"album_card_{album_id}.png")
    
    print(f"Step 6: Saving image...")
    card.save(output_path, "PNG")
    print(f"✓ Album card created: {output_path}")
    
    return output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python make_album_card.py <album_id>")
        print("Example: python make_album_card.py al-444")
        sys.exit(1)
    
    album_id = sys.argv[1]
    
    try:
        create_album_card(album_id)
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating album card: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
