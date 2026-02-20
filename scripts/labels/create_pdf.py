from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from PIL import Image
import sys
import os
import subprocess
from pathlib import Path
import tempfile

# Image size in mm
iw_mm = 85.60
ih_mm = 53.98

# Convert to points (1 mm = 2.83465 points)
iw = iw_mm * mm
ih = ih_mm * mm

# A4 size in points
page_width, page_height = A4

# List of album IDs (replace with your actual album IDs)
album_ids = [
    "al-444",
    "al-89",
    "al-230",
    "al-236",
    "al-237",
    "al-233",
    "al-232",
    "al-234"
]

# Label dimensions: 105mm × 71mm
# Image dimensions: 85.60mm × 53.98mm
# Top/bottom margin: 6.5mm
# Centering offsets: (9.7mm, 8.51mm)

xy_coords = [
    (9.7, 15.01), (114.7, 15.01),
    (9.7, 86.01), (114.7, 86.01),
    (9.7, 157.01), (114.7, 157.01),
    (9.7, 228.01), (114.7, 228.01)
]

def generate_album_cards(album_ids):
    """Generate album card images from album IDs using make_album_card.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    make_album_card_script = os.path.join(script_dir, 'make_album_card.py')
    
    if not os.path.exists(make_album_card_script):
        raise FileNotFoundError(f"make_album_card.py not found at {make_album_card_script}")
    
    image_paths = []
    output_dir = os.getcwd()
    
    for album_id in album_ids:
        print(f"Generating card for album: {album_id}")
        
        # Call make_album_card.py
        result = subprocess.run(
            [sys.executable, make_album_card_script, album_id],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error generating card for {album_id}:")
            print(result.stderr)
            continue
        
        # Get the output image path
        image_path = os.path.join(output_dir, f"album_card_{album_id}.png")
        
        if os.path.exists(image_path):
            image_paths.append(image_path)
            print(f"✓ Generated: {image_path}")
        else:
            print(f"✗ Image not found: {image_path}")
    
    return image_paths


def draw_images(pdf_path, image_paths, xy_coords):
    c = canvas.Canvas(pdf_path, pagesize=A4)
    
    print("\n" + "="*70)
    print("IMAGE PLACEMENT DEBUG LOG")
    print("="*70)
    print(f"Image dimensions (width × height): {iw/mm:.2f}mm × {ih/mm:.2f}mm")
    print(f"A4 page: width={page_width/mm:.1f}mm, height={page_height/mm:.1f}mm\n")
    print(f"{'Idx':<3} {'User Y':<10} {'User X':<10} {'Report Y':<10} {'Report X':<10} {'Actual Pos':<20}")
    print("-"*70)
    
    # Create temp directory for rotated images
    with tempfile.TemporaryDirectory() as tmpdir:
        for idx, img_path in enumerate(image_paths):
            if idx >= len(xy_coords):
                break
            x_user, y_user = xy_coords[idx]
            
            # Read image and rotate 90 degrees with expand=True to remove black padding
            img = Image.open(img_path)
            img_rotated = img.rotate(90, expand=True)
            
            # Save rotated image to temp file
            rotated_path = os.path.join(tmpdir, f"rotated_{idx}.png")
            img_rotated.save(rotated_path)
            
            # Calculate ReportLab Y: xy_coords specify UPPER-LEFT corner from top
            # ReportLab uses bottom-left origin, so we need to convert
            # If upper-left is at y_user from top, then bottom-left is at (y_user + image_height) from top
            # Converting to bottom-relative: page_height - (y_user + image_height)
            y_reportlab = page_height/mm - (y_user + ih/mm)
            x_reportlab = x_user
            
            actual_top_mm = page_height/mm - (y_reportlab + ih/mm)
            
            print(f"{idx:<3} {y_user:<10.1f} {x_user:<10.1f} {y_reportlab:<10.1f} {x_reportlab:<10.1f} Top {actual_top_mm:.1f}mm")
            
            # Draw rotated image at position
            c.drawImage(rotated_path, x_reportlab * mm, y_reportlab * mm, width=iw, height=ih)
    
    print("="*70)
    c.save()
    print(f"\nPDF saved: {pdf_path}\n")

if __name__ == '__main__':
    # Usage: python create_pdf.py output.pdf al-1 al-2 ... al-8
    # or: python create_pdf.py output.pdf (uses default album_ids)
    
    if len(sys.argv) >= 2:
        out_pdf = sys.argv[1]
        
        if len(sys.argv) > 2:
            # Album IDs provided as arguments
            album_ids = sys.argv[2:]
        else:
            # Use default album_ids
            album_ids = album_ids
        
        print(f"Generating album cards from {len(album_ids)} album ID(s)...")
        image_paths = generate_album_cards(album_ids)
        
        if image_paths:
            draw_images(out_pdf, image_paths, xy_coords)
            print(f'✓ PDF created: {out_pdf}')
        else:
            print('✗ No album cards were generated.')
    else:
        # Default demo
        print("Generating album cards from default album IDs...")
        image_paths = generate_album_cards(album_ids)
        
        if image_paths:
            draw_images('output.pdf', image_paths, xy_coords)
            print('✓ Demo PDF created as output.pdf')
        else:
            print('✗ No album cards were generated.')
        
        print('Usage: python create_pdf.py output.pdf [al-1] [al-2] ... [al-8]')
