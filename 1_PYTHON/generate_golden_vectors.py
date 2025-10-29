#!/usr/bin/env python3
"""
Generate golden input/output vectors for Sobel pipeline matching the RTL behavior.
- Input: random RGB565 frame (deterministic with seed)
- Output: two mem files in sim/golden/
    * input_rgb565.mem       (WIDTH*HEIGHT lines, 16-bit hex)
    * expected_output.mem    ((HEIGHT-2)*(WIDTH-1) lines, 16-bit hex)

Border behavior matches RTL line_buffer:
- Valid windows start at row >= 2 and col >= 1
- Right neighbor uses wrap-around (col+1 wraps to 0)
- Top-of-frame not valid until two full rows have been received
- Additional pipeline stages in RTL are handled by comparing only when pixel_valid is asserted,
  and by emitting expected outputs in the order windows become valid.
"""
import argparse
import os
import random

# RGB565 pack/unpack helpers

def expand5to8(v5: int) -> int:
    return ((v5 & 0x1F) << 3) | ((v5 & 0x1F) >> 2)

def expand6to8(v6: int) -> int:
    return ((v6 & 0x3F) << 2) | ((v6 & 0x3F) >> 4)

def rgb565_to_rgb8(rgb: int):
    r5 = (rgb >> 11) & 0x1F
    g6 = (rgb >> 5) & 0x3F
    b5 = rgb & 0x1F
    return expand5to8(r5), expand6to8(g6), expand5to8(b5)

def rgb565_to_gray8(rgb: int) -> int:
    r8, g8, b8 = rgb565_to_rgb8(rgb)
    # Weighted: (77*R + 151*G + 28*B) >> 8
    w = (77 * r8) + (151 * g8) + (28 * b8)
    return (w >> 8) & 0xFF

def pack_edge_to_rgb565(edge8: int) -> int:
    r5 = (edge8 >> 3) & 0x1F
    g6 = (edge8 >> 2) & 0x3F
    b5 = (edge8 >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


def sobel_gx_gy(win):
    # win is 3x3 list of ints (0..255)
    p0,p1,p2 = win[0]
    p3,p4,p5 = win[1]
    p6,p7,p8 = win[2]
    gx = -p0 + p2 - 2*p3 + 2*p5 - p6 + p8
    gy = -p0 - 2*p1 - p2 + p6 + 2*p7 + p8
    return gx, gy

def sobel_edge8(win) -> int:
    gx, gy = sobel_gx_gy(win)
    ax = abs(int(gx))
    ay = abs(int(gy))
    s = ax + ay
    s >>= 3  # mirror RTL scaling (shift before saturation)
    if s > 255:
        s = 255
    return s


def generate_vectors(width: int, height: int, seed: int):
    rnd = random.Random(seed)
    # Generate random RGB565 frame
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    # Precompute grayscale stream
    gray_stream = [rgb565_to_gray8(px) for px in frame]

    # Simulate RTL line_buffer behavior cycle-accurately:
    # - Three line memories updated at each pixel column (non-blocking in RTL means reads see old values)
    # - window_valid condition: row_count >= 2 and col >= 1
    line_mem0 = [0] * width
    line_mem1 = [0] * width
    line_mem2 = [0] * width
    row_count = 0

    expected = []
    idx = 0
    for r in range(height):
        for c in range(width):
            gcur = gray_stream[idx]
            # Compute expected using current contents (before update), if valid
            if row_count >= 2 and c >= 1:
                xm1 = c - 1
                xp1 = (c + 1) % width
                p0 = line_mem2[xm1]; p1 = line_mem2[c]; p2 = line_mem2[xp1]
                p3 = line_mem1[xm1]; p4 = line_mem1[c]; p5 = line_mem1[xp1]
                p6 = line_mem0[xm1]; p7 = line_mem0[c]; p8 = line_mem0[xp1]
                win = [[p0,p1,p2], [p3,p4,p5], [p6,p7,p8]]
                e8 = sobel_edge8(win)
                expected.append(pack_edge_to_rgb565(e8))
            # Update line memories after computing
            line_mem2[c] = line_mem1[c]
            line_mem1[c] = line_mem0[c]
            line_mem0[c] = gcur
            idx += 1
        row_count += 1
    return frame, expected


def write_mem_hex(path: str, values):
    with open(path, 'w') as f:
        for v in values:
            f.write(f"{v:04x}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--width', type=int, default=64)
    ap.add_argument('--height', type=int, default=48)
    ap.add_argument('--seed', type=int, default=123)
    args = ap.parse_args()

    frame, expected = generate_vectors(args.width, args.height, args.seed)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'sim', 'golden')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    in_mem_path = os.path.join(out_dir, 'input_rgb565.mem')
    exp_mem_path = os.path.join(out_dir, 'expected_output.mem')
    write_mem_hex(in_mem_path, frame)
    write_mem_hex(exp_mem_path, expected)

    print(f"Wrote {len(frame)} input pixels to {in_mem_path}")
    print(f"Wrote {len(expected)} expected outputs to {exp_mem_path}")

if __name__ == '__main__':
    main()
