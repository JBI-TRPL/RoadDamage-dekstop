#!/usr/bin/env python3
"""
Generate icon.ico for VGTECH Road Damage Detector
Creates a simple icon with road damage theme
"""
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required to generate icons")
    print("Install with: pip install Pillow")
    sys.exit(1)

def create_icon():
    """Create a multi-resolution icon for Windows"""
    
    # Icon sizes for .ico file
    sizes = [256, 128, 64, 48, 32, 16]
    images = []
    
    for size in sizes:
        # Create image with transparent background
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Colors
        bg_color = (41, 128, 185)  # Professional blue
        road_color = (52, 73, 94)  # Dark gray (road)
        damage_color = (231, 76, 60)  # Red (damage)
        text_color = (255, 255, 255)  # White
        
        # Draw background circle
        margin = size // 10
        draw.ellipse([margin, margin, size-margin, size-margin], 
                     fill=bg_color, outline=None)
        
        # Draw road symbol (horizontal lines)
        road_margin = size // 4
        road_height = size // 15
        road_y1 = size // 2 - road_height
        road_y2 = size // 2 + road_height
        
        draw.rectangle([road_margin, road_y1, size-road_margin, road_y1 + road_height // 2], 
                      fill=road_color)
        draw.rectangle([road_margin, road_y2, size-road_margin, road_y2 + road_height // 2], 
                      fill=road_color)
        
        # Draw damage symbol (lightning bolt / crack)
        center_x = size // 2
        center_y = size // 2
        crack_size = size // 6
        
        # Simple crack/damage indicator (zigzag)
        points = [
            (center_x - crack_size//3, center_y - crack_size),
            (center_x + crack_size//4, center_y - crack_size//3),
            (center_x - crack_size//4, center_y + crack_size//3),
            (center_x + crack_size//3, center_y + crack_size),
        ]
        
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=damage_color, width=max(2, size//32))
        
        images.append(img)
    
    # Save as .ico file
    output_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
    images[0].save(output_path, format='ICO', sizes=[(img.width, img.height) for img in images])
    
    print(f"✓ Icon created: {output_path}")
    print(f"  Sizes: {', '.join([f'{s}x{s}' for s in sizes])}")
    
    # Also save as PNG for preview
    png_path = os.path.join(os.path.dirname(__file__), 'icon_preview.png')
    images[0].save(png_path, format='PNG')
    print(f"✓ Preview saved: {png_path}")
    
    return output_path

if __name__ == '__main__':
    print("VGTECH Road Damage Detector - Icon Generator")
    print("=" * 50)
    print()
    
    icon_path = create_icon()
    
    print()
    print("To use this icon:")
    print("1. The icon is already configured in build-windows.spec")
    print("2. Run build script: .\\build-scripts\\build-installer-windows.ps1")
    print("3. The Windows executable will include this icon")
