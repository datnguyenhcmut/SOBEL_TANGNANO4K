#!/usr/bin/env python3
"""
Display input frame as 2D array to manually verify window formation
"""
import random

width, height, seed = 64, 48, 123
rnd = random.Random(seed)
frame_rgb = [rnd.getrandbits(16) for _ in range(width*height)]

def rgb565_to_gray8(rgb: int) -> int:
    r5 = (rgb >> 11) & 0x1F
    g6 = (rgb >> 5) & 0x3F
    b5 = rgb & 0x1F
    r8 = (r5 << 3) | (r5 >> 2)
    g8 = (g6 << 2) | (g6 >> 4)
    b8 = (b5 << 3) | (b5 >> 2)
    gray = (77*r8 + 151*g8 + 28*b8) >> 8
    return gray if gray <= 255 else 255

frame_gray = [[rgb565_to_gray8(frame_rgb[r*width + c]) for c in range(width)] for r in range(height)]

# Show region around row=3, col=7 (where RTL outputs first value)
print("Input frame (grayscale) around row=3, col=7:")
print("Row/Col:  ", "  ".join(f"{c:2d}" for c in range(5, 10)))
for r in range(1, 6):
    print(f"Row {r}: ", "  ".join(f"{frame_gray[r][c]:02x}" for c in range(5, 10)))

# Expected window at row=3, col=7 (output position)
print("\nExpected window at (row=3, col=7):")
print("  Window should use:")
print("    top_row (row=1): cols [6,7,8]")
print("    mid_row (row=2): cols [6,7,8]")
print("    bot_row (row=3): cols [6,7,8]")

print("\n  Actual values:")
for r_offset, r_name in [(-2, "top"), (-1, "mid"), (0, "bot")]:
    r = 3 + r_offset
    row_vals = [frame_gray[r][c] for c in [6, 7, 8]]
    print(f"    {r_name}_row: {' '.join(f'0x{v:02x}' for v in row_vals)}")

# Calculate expected Sobel
window = []
for r_offset in [-2, -1, 0]:
    window.append([frame_gray[3+r_offset][c] for c in [6, 7, 8]])

def sobel_edge(win):
    gx = -win[0][0] + win[0][2] - 2*win[1][0] + 2*win[1][2] - win[2][0] + win[2][2]
    gy = -win[0][0] - 2*win[0][1] - win[0][2] + win[2][0] + 2*win[2][1] + win[2][2]
    edge = (abs(gx) + abs(gy)) >> 3
    return min(edge, 31)

edge = sobel_edge(window)
r5 = g6 = b5 = edge
rgb565 = (r5 << 11) | (g6 << 5) | b5

print(f"\n  Expected Sobel: gx=..., gy=..., edge={edge} (0x{edge:02x})")
print(f"  Expected RGB565 output: 0x{rgb565:04x}")

# Show RTL actual
print(f"\n  RTL actual output[1]: 0x4a69")
print(f"  Python expected output[1]: 0x2104")
