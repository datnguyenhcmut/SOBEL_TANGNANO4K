#!/usr/bin/env python3
"""
Generate golden vectors matching RTL pipeline timing exactly.

RTL Pipeline:
- Cycle 0: pixel_valid=1, col_addr=c → BRAM ceb=1, adb=c
- Cycle 1: read_pipe <= mem[c] (BRAM cycle 1)
- Cycle 2: dout <= read_pipe, pixel_valid_d0=1, line_q_d captured
- Cycle 3: pixel_valid_d1=1, shift registers updated, window_valid checks
          (row_count_d1 >= 2 && col_addr_d1 >= 1)

So output appears 3 cycles after input pixel arrives.
"""
import argparse
import os
import random

# RGB565 helpers (same as before)
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
    w = (77 * r8) + (151 * g8) + (28 * b8)
    return (w >> 8) & 0xFF

def pack_edge_to_rgb565(edge8: int) -> int:
    r5 = (edge8 >> 3) & 0x1F
    g6 = (edge8 >> 2) & 0x3F
    b5 = (edge8 >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5

def sobel_gx_gy(win):
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
    s >>= 3
    if s > 255:
        s = 255
    return s

def generate_vectors_rtl(width: int, height: int, seed: int):
    """Generate with RTL-accurate pipeline timing."""
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    gray_stream = [rgb565_to_gray8(px) for px in frame]
    
    # Simulate RTL cycle-by-cycle
    # Pipeline state
    pixel_valid_d0 = False
    pixel_valid_d1 = False
    col_addr_d0 = 0
    col_addr_d1 = 0
    row_count_d0 = 0
    row_count_d1 = 0
    
    # Line BRAMs (with read pipeline)
    line0_mem = [0] * width
    line1_mem = [0] * width
    line2_mem = [0] * width
    line0_pipe = 0  # read_pipe register
    line1_pipe = 0
    line2_pipe = 0
    line0_q = 0     # dout
    line1_q = 0
    line2_q = 0
    line0_q_d = 0   # registered output
    line1_q_d = 0
    line2_q_d = 0
    
    # Shift registers (3x3 window)
    top_row = [0, 0, 0]
    mid_row = [0, 0, 0]
    bot_row = [0, 0, 0]
    
    # Control
    col_addr = 0
    row_count = 0
    pixel_in_d0 = 0
    pixel_in_d1 = 0
    
    expected = []
    idx = 0
    
    for r in range(height):
        for c in range(width):
            pixel_valid = True
            pixel_in = gray_stream[idx]
            
            # === Cycle logic (at clock edge) ===
            
            # Shift registers update (at d1 stage) - BEFORE updating pipeline
            if pixel_valid_d1:
                top_row[0] = top_row[1]
                top_row[1] = top_row[2]
                top_row[2] = line2_q_d
                
                mid_row[0] = mid_row[1]
                mid_row[1] = mid_row[2]
                mid_row[2] = line1_q_d
                
                bot_row[0] = bot_row[1]
                bot_row[1] = bot_row[2]
                bot_row[2] = pixel_in_d1
                
                # Check window_valid
                if row_count_d1 >= 2 and col_addr_d1 >= 1:
                    win = [top_row[:], mid_row[:], bot_row[:]]
                    e8 = sobel_edge8(win)
                    expected.append(pack_edge_to_rgb565(e8))
            
            # Register BRAM outputs (at d0 stage)
            if pixel_valid_d0:
                line0_q_d = line0_q
                line1_q_d = line1_q
                line2_q_d = line2_q
            
            # BRAM output register (2nd cycle of read)
            line0_q = line0_pipe
            line1_q = line1_pipe  
            line2_q = line2_pipe
            
            # BRAM read pipeline (1st cycle of read)
            if pixel_valid:
                line0_pipe = line0_mem[col_addr]
            if pixel_valid_d0:
                line1_pipe = line1_mem[col_addr_d0]
            if pixel_valid_d1:
                line2_pipe = line2_mem[col_addr_d1]
            
            # BRAM write (write current pixel to line0, cascade down)
            if pixel_valid:
                line2_mem[col_addr] = line1_mem[col_addr]
                line1_mem[col_addr] = line0_mem[col_addr]
                line0_mem[col_addr] = pixel_in
            
            # Pipeline advance (sequential - end of cycle)
            pixel_in_d1 = pixel_in_d0
            pixel_in_d0 = pixel_in
            pixel_valid_d1 = pixel_valid_d0
            pixel_valid_d0 = pixel_valid
            col_addr_d1 = col_addr_d0
            col_addr_d0 = col_addr
            row_count_d1 = row_count_d0
            row_count_d0 = row_count
            
            # Address increment for next cycle
            if c == width - 1:
                col_addr = 0
                # Row counter increments at end of row (like RTL)
                if row_count < 0xFFFFFFFF:  # saturate
                    row_count += 1
            else:
                col_addr = c + 1
            
            idx += 1
    
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

    frame, expected = generate_vectors_rtl(args.width, args.height, args.seed)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'sim', 'golden')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    in_mem_path = os.path.join(out_dir, 'input_rgb565.mem')
    exp_mem_path = os.path.join(out_dir, 'expected_output.mem')
    write_mem_hex(in_mem_path, frame)
    write_mem_hex(exp_mem_path, expected)

    print(f"Wrote {len(frame)} input pixels to {in_mem_path}")
    print(f"Wrote {len(expected)} expected outputs to {exp_mem_path}")
    print(f"Expected outputs: {len(expected)} (should be {(args.height-2)*(args.width-1)})")

if __name__ == '__main__':
    main()
