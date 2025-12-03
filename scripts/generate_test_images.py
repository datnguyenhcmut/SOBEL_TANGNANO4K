"""
Generate simple test images for Tang Nano 4K Binarization Testing
Uses PIL only (simpler than OpenCV)

Requirements:
    pip install pillow

Usage:
    python generate_test_images.py
"""

from PIL import Image, ImageDraw, ImageFont
import os

# Create output directory
output_dir = '../data/test_images'
os.makedirs(output_dir, exist_ok=True)

WIDTH = 640
HEIGHT = 480

print("Generating test images for Tang Nano 4K...")
print(f"Resolution: {WIDTH}x{HEIGHT}")
print(f"Output: {output_dir}/")

# =========================================================================
# TEST 1: Blank screen (NO edges expected)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(200, 200, 200))
draw = ImageDraw.Draw(img)
draw.text((200, 200), "TEST 1: BLANK", fill=(0, 0, 0))
draw.text((150, 250), "Expected: ~0% edges", fill=(0, 0, 0))
img.save(f'{output_dir}/test1_blank.png')
print("✓ Test 1: Blank screen")

# =========================================================================
# TEST 2: Simple rectangle (Clear edges)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(200, 200, 200))
draw = ImageDraw.Draw(img)
draw.rectangle([150, 100, 490, 380], fill=(50, 50, 50))
draw.text((150, 30), "TEST 2: RECTANGLE", fill=(0, 0, 0))
draw.text((120, 450), "Expected: 4 clear edges", fill=(0, 0, 0))
img.save(f'{output_dir}/test2_rectangle.png')
print("✓ Test 2: Rectangle")

# =========================================================================
# TEST 3: Circle (Curved edge)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(220, 220, 220))
draw = ImageDraw.Draw(img)
draw.ellipse([250, 140, 390, 340], fill=(30, 30, 30))
draw.text((200, 30), "TEST 3: CIRCLE", fill=(0, 0, 0))
draw.text((120, 450), "Expected: Circular edge", fill=(0, 0, 0))
img.save(f'{output_dir}/test3_circle.png')
print("✓ Test 3: Circle")

# =========================================================================
# TEST 4: Multiple objects
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(210, 210, 210))
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 200, 200], fill=(40, 40, 40))
draw.rectangle([250, 100, 400, 250], fill=(60, 60, 60))
draw.rectangle([450, 50, 600, 200], fill=(80, 80, 80))
draw.rectangle([150, 280, 490, 430], fill=(100, 100, 100))
draw.text((100, 20), "TEST 4: MULTIPLE OBJECTS", fill=(0, 0, 0))
draw.text((120, 460), "Expected: ~15-20% edges", fill=(0, 0, 0))
img.save(f'{output_dir}/test4_multiple.png')
print("✓ Test 4: Multiple objects")

# =========================================================================
# TEST 5: Gradient (Weak edges)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT))
pixels = img.load()
for x in range(WIDTH):
    color = int(255 * x / WIDTH)
    for y in range(HEIGHT):
        pixels[x, y] = (color, color, color)
draw = ImageDraw.Draw(img)
draw.text((180, 220), "TEST 5: GRADIENT", fill=(128, 128, 128))
draw.text((120, 260), "Expected: Weak/no edges", fill=(128, 128, 128))
img.save(f'{output_dir}/test5_gradient.png')
print("✓ Test 5: Gradient")

# =========================================================================
# TEST 6: High contrast (Strong edges)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(255, 255, 255))
draw = ImageDraw.Draw(img)
draw.rectangle([100, 80, 250, 200], fill=(0, 0, 0))
draw.rectangle([300, 150, 540, 400], fill=(0, 0, 0))
draw.text((120, 30), "TEST 6: HIGH CONTRAST", fill=(0, 0, 0))
draw.text((80, 450), "Expected: Strong edges (LED1=ON)", fill=(0, 0, 0))
img.save(f'{output_dir}/test6_contrast.png')
print("✓ Test 6: High contrast")

# =========================================================================
# TEST 7: Grid pattern (Complex edges)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(200, 200, 200))
draw = ImageDraw.Draw(img)
# Draw grid
for i in range(0, WIDTH, 80):
    draw.line([(i, 0), (i, HEIGHT)], fill=(50, 50, 50), width=2)
for i in range(0, HEIGHT, 80):
    draw.line([(0, i), (WIDTH, i)], fill=(50, 50, 50), width=2)
draw.text((200, 220), "TEST 7: GRID", fill=(0, 0, 0))
draw.text((100, 260), "Expected: Grid pattern edges", fill=(0, 0, 0))
img.save(f'{output_dir}/test7_grid.png')
print("✓ Test 7: Grid pattern")

# =========================================================================
# TEST 8: Text (Character edges)
# =========================================================================
img = Image.new('RGB', (WIDTH, HEIGHT), color=(200, 200, 200))
draw = ImageDraw.Draw(img)
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()
draw.text((100, 150), "TANG NANO", fill=(0, 0, 0), font=font)
draw.text((150, 250), "SOBEL TEST", fill=(0, 0, 0), font=font)
draw.text((120, 400), "TEST 8: TEXT EDGES", fill=(50, 50, 50))
img.save(f'{output_dir}/test8_text.png')
print("✓ Test 8: Text")

print("\n✓ All test images generated!")
print(f"\nOutput directory: {output_dir}/")
print("\nTest images:")
print("  1. test1_blank.png      - Expect ~0% edges")
print("  2. test2_rectangle.png  - Expect 4 clear edges")
print("  3. test3_circle.png     - Expect circular edge")
print("  4. test4_multiple.png   - Expect 15-20% edges")
print("  5. test5_gradient.png   - Expect weak edges")
print("  6. test6_contrast.png   - Expect strong edges (LED1=ON)")
print("  7. test7_grid.png       - Expect grid pattern")
print("  8. test8_text.png       - Expect character outlines")
print("\nHow to test:")
print("1. Display images on PC monitor (fullscreen)")
print("2. Point Tang Nano 4K camera at screen")
print("3. Observe VGA output for edge detection")
print("4. Compare with expected results above")
print("\nAlternatively:")
print("  - Print images and test with camera")
print("  - Use smartphone to display images")
