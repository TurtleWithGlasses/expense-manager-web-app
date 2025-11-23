#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate PWA icons and splash screens from the base icon
Requires: pip install Pillow
"""

import sys
import io
from PIL import Image, ImageDraw, ImageFont
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Icon sizes needed for PWA
ICON_SIZES = [32, 72, 96, 128, 144, 152, 192, 384, 512]

# Shortcut icon size
SHORTCUT_ICON_SIZE = 96

# Splash screen sizes (iOS specific)
SPLASH_SIZES = {
    'iphone5': (640, 1136),
    'iphone6': (750, 1334),
    'iphoneplus': (1242, 2208),
    'iphonex': (1125, 2436),
    'iphonexr': (828, 1792),
    'iphonexsmax': (1242, 2688),
    'ipad': (1536, 2048),
    'ipadpro1': (1668, 2224),
    'ipadpro2': (2048, 2732),
}

# Colors (matching your theme)
PRIMARY_COLOR = '#3b82f6'  # Blue
BACKGROUND_DARK = '#1a1f2e'  # Dark theme background
TEXT_COLOR = '#e5e7eb'  # Light text


def ensure_dir(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def generate_icons():
    """Generate all required icon sizes"""
    print("Generating PWA icons...")

    base_icon_path = 'static/money_icon.png'
    icons_dir = 'static/icons'

    ensure_dir(icons_dir)

    if not os.path.exists(base_icon_path):
        print(f"Error: Base icon not found at {base_icon_path}")
        print("Please ensure static/money_icon.png exists")
        return False

    try:
        # Load base icon
        base_icon = Image.open(base_icon_path)
        base_icon = base_icon.convert('RGBA')

        # Generate each size
        for size in ICON_SIZES:
            # Resize icon
            icon = base_icon.resize((size, size), Image.Resampling.LANCZOS)

            # Save icon
            output_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
            icon.save(output_path, 'PNG', quality=95, optimize=True)
            print(f"  ✓ Created {output_path}")

        # Create badge icon (72x72) - same as regular icon
        badge_icon = base_icon.resize((72, 72), Image.Resampling.LANCZOS)
        badge_path = os.path.join(icons_dir, 'badge-72x72.png')
        badge_icon.save(badge_path, 'PNG', quality=95, optimize=True)
        print(f"  ✓ Created {badge_path}")

        print(f"\n✅ Generated {len(ICON_SIZES) + 1} icon files")
        return True

    except Exception as e:
        print(f"Error generating icons: {e}")
        return False


def generate_shortcut_icons():
    """Generate icons for app shortcuts"""
    print("\nGenerating shortcut icons...")

    icons_dir = 'static/icons'
    ensure_dir(icons_dir)

    size = SHORTCUT_ICON_SIZE

    # Create a simple icon with text
    shortcuts = {
        'expense': ('💸', '#ef4444'),  # Red for expense
        'income': ('💰', '#10b981'),   # Green for income
        'dashboard': ('📊', '#3b82f6'), # Blue for dashboard
    }

    for name, (emoji, color) in shortcuts.items():
        try:
            # Create a new image with rounded corners
            img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw rounded rectangle background
            draw.rounded_rectangle(
                [(0, 0), (size, size)],
                radius=size // 5,
                fill=color
            )

            # Try to add emoji text (may not work on all systems)
            try:
                # Use a large font size
                font_size = size // 2
                # Try to load a font that supports emoji
                try:
                    font = ImageFont.truetype("seguiemj.ttf", font_size)  # Windows emoji font
                except:
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Apple Color Emoji.ttc", font_size)  # macOS
                    except:
                        # Fallback to default
                        font = ImageFont.load_default()

                # Calculate text position (centered)
                text_bbox = draw.textbbox((0, 0), emoji, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = (size - text_width) // 2 - text_bbox[0]
                text_y = (size - text_height) // 2 - text_bbox[1]

                # Draw emoji
                draw.text((text_x, text_y), emoji, font=font, fill='white')
            except Exception as e:
                print(f"  ⚠ Could not add emoji to {name} icon: {e}")
                # Just use the colored background

            # Save shortcut icon
            output_path = os.path.join(icons_dir, f'shortcut-{name}.png')
            img.save(output_path, 'PNG', quality=95, optimize=True)
            print(f"  ✓ Created {output_path}")

        except Exception as e:
            print(f"  ✗ Error creating {name} shortcut icon: {e}")

    print(f"✅ Generated {len(shortcuts)} shortcut icons")


def generate_splash_screens():
    """Generate splash screens for iOS"""
    print("\nGenerating splash screens...")

    splash_dir = 'static/splash'
    ensure_dir(splash_dir)

    base_icon_path = 'static/money_icon.png'

    if not os.path.exists(base_icon_path):
        print("  ⚠ Base icon not found, skipping splash screens")
        return

    try:
        base_icon = Image.open(base_icon_path)
        base_icon = base_icon.convert('RGBA')

        for name, (width, height) in SPLASH_SIZES.items():
            # Create splash screen background
            splash = Image.new('RGB', (width, height), BACKGROUND_DARK)

            # Calculate icon size (20% of screen width)
            icon_size = int(width * 0.2)
            icon = base_icon.resize((icon_size, icon_size), Image.Resampling.LANCZOS)

            # Center the icon
            x = (width - icon_size) // 2
            y = (height - icon_size) // 2 - int(height * 0.1)  # Slightly above center

            # Paste icon on splash screen
            splash.paste(icon, (x, y), icon)

            # Save splash screen
            output_path = os.path.join(splash_dir, f'{name}.png')
            splash.save(output_path, 'PNG', quality=90, optimize=True)
            print(f"  ✓ Created {output_path}")

        print(f"✅ Generated {len(SPLASH_SIZES)} splash screens")

    except Exception as e:
        print(f"Error generating splash screens: {e}")


def create_placeholder_screenshots():
    """Create placeholder screenshots for manifest"""
    print("\nCreating placeholder screenshots...")

    screenshots_dir = 'static/screenshots'
    ensure_dir(screenshots_dir)

    screenshots = {
        'desktop-dashboard': (1280, 720),
        'mobile-entries': (750, 1334),
    }

    for name, (width, height) in screenshots.items():
        try:
            # Create a simple placeholder
            img = Image.new('RGB', (width, height), BACKGROUND_DARK)
            draw = ImageDraw.Draw(img)

            # Add text
            text = "Screenshot Placeholder"
            try:
                font = ImageFont.truetype("arial.ttf", 48)
            except:
                font = ImageFont.load_default()

            # Center text
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2

            draw.text((x, y), text, font=font, fill=TEXT_COLOR)

            # Add note
            note = f"Replace with actual {name} screenshot"
            note_y = y + text_height + 20
            draw.text((width // 4, note_y), note, font=font, fill='#9ca3af')

            # Save screenshot
            output_path = os.path.join(screenshots_dir, f'{name}.png')
            img.save(output_path, 'PNG', quality=90)
            print(f"  ✓ Created {output_path}")

        except Exception as e:
            print(f"  ✗ Error creating {name} screenshot: {e}")

    print("✅ Created placeholder screenshots")
    print("   ⚠ Replace these with actual app screenshots for best results")


def main():
    print("=" * 60)
    print("PWA Icon Generator for BudgetPulse")
    print("=" * 60)

    # Check if Pillow is installed
    try:
        from PIL import Image
    except ImportError:
        print("Error: Pillow is not installed")
        print("Install it with: pip install Pillow")
        return

    # Generate all assets
    icons_ok = generate_icons()

    if icons_ok:
        generate_shortcut_icons()
        generate_splash_screens()
        create_placeholder_screenshots()

        print("\n" + "=" * 60)
        print("✅ PWA assets generation complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Replace placeholder screenshots with actual app screenshots")
        print("2. Test PWA installation on mobile devices")
        print("3. Deploy to production and verify manifest.json is accessible")
    else:
        print("\n❌ Icon generation failed")
        print("Please ensure static/money_icon.png exists and try again")


if __name__ == '__main__':
    main()
