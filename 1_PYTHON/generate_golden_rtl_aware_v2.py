#!/usr/bin/env python3
"""
Generate golden vectors matching OPTIMIZED RTL pipeline timing.

OPTIMIZED RTL Pipeline (after removing _d0 stage):
- Cycle 0: pixel_valid=1, col_addr=c → BRAM addr register  
- Cycle 1: BRAM read_pipe <= mem[c], pixel_valid_d1=1
- Cycle 2: BRAM dout <= read_pipe, pixel_valid_d2=1, window shifts, window_valid checks
          (row_count_d2 >= 3 && col_addr_d2 >= 2)

Key change: window_valid now at d2 stage with row>=3, col>=2
"""
import argparse
import os
import random

# RGB565 helpers
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

def generate_vectors_rtl_optimized(width: int, height: int, seed: int):
    """Generate with OPTIMIZED RTL pipeline timing (_d1, _d2 stages only)."""
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    gray_stream = [rgb565_to_gray8(px) for px in frame]
    
    # Pipeline state (2 stages: d1, d2 for line_buffer)
    pixel_valid_d1 = False
    pixel_valid_d2 = False
    col_addr_d1 = 0
    col_addr_d2 = 0
    row_count_d1 = 0
    row_count_d2 = 0
    pixel_in_d1 = 0
    pixel_in_d2 = 0
    
    # Additional pipeline stages for sobel_kernel and edge_mag
    window_valid_sobel = False  # sobel_kernel output (1 cycle after window_valid)
    edge_sobel = 0
    window_valid_edge = False   # edge_mag output (1 cycle after sobel_valid)
    edge_edge = 0
    
    # BRAMs
    line0_mem = [0] * width
    line1_mem = [0] * width
    line2_mem = [0] * width
    line0_q = 0     # BRAM output (available at d2)
    line1_q = 0
    line2_q = 0
    
    # Shift registers (3x3 window)
    top_row = [0, 0, 0]
    mid_row = [0, 0, 0]
    bot_row = [0, 0, 0]
    
    # Control
    col_addr = 0
    row_count = 0
    current_row = 0  # Track which row we're actually processing
    
    expected = []
    idx = 0
    
    # Add extra cycles at the end to drain pipeline
    # line_buffer: 2 cycles, sobel_kernel: 1 cycle, edge_mag: 1 cycle = 4 total
    total_cycles = height * width + 4
    
    for cycle in range(total_cycles):
        # Input stage
        if cycle < height * width:
            r = cycle // width
            c = cycle % width
            pixel_valid = True
            pixel_in = gray_stream[idx]
            idx += 1
            
            # Update row_count to match RTL: it reflects CURRENT row being processed
            # RTL increments at end of row, so row_count=r for all pixels in row r
            current_row = r
            row_count = r
        else:
            pixel_valid = False
            pixel_in = 0
            c = 0
            r = height - 1
        
        # === Cycle logic (at clock edge) ===
        
        # OUTPUT STAGE: edge_mag → pixel_valid (registered edge_edge)
        if window_valid_edge:
            expected.append(pack_edge_to_rgb565(edge_edge))
        
        # EDGE_MAG STAGE: sobel_kernel → edge_mag (1 cycle delay)
        window_valid_edge = window_valid_sobel
        edge_edge = edge_sobel
        
        # SOBEL_KERNEL STAGE: line_buffer → sobel_kernel (1 cycle delay)
        if pixel_valid_d2:
            top_row[0] = top_row[1]
            top_row[1] = top_row[2]
            top_row[2] = line2_q
            
            mid_row[0] = mid_row[1]
            mid_row[1] = mid_row[2]
            mid_row[2] = line1_q
            
            bot_row[0] = bot_row[1]
            bot_row[1] = bot_row[2]
            bot_row[2] = pixel_in_d2
            
            # Check window_valid (OPTIMIZED: row>=3, col>=2)
            window_valid = row_count_d2 >= 3 and col_addr_d2 >= 2
            
            if window_valid:
                win = [top_row[:], mid_row[:], bot_row[:]]
                edge_sobel = sobel_edge8(win)
                window_valid_sobel = True
            else:
                window_valid_sobel = False
        else:
            window_valid_sobel = False
        
        # LINE_BUFFER STAGES (d1, d2)
        if pixel_valid_d1:
            line0_q = line0_mem[col_addr_d1]
            line1_q = line1_mem[col_addr_d1]
            line2_q = line2_mem[col_addr_d1]
        
        # BRAM write (cascade pattern)
        if pixel_valid:
            line2_mem[col_addr] = line1_mem[col_addr]
            line1_mem[col_addr] = line0_mem[col_addr]
            line0_mem[col_addr] = pixel_in
        
        # Pipeline advance (sequential - end of cycle)
        pixel_in_d2 = pixel_in_d1
        pixel_in_d1 = pixel_in
        pixel_valid_d2 = pixel_valid_d1
        pixel_valid_d1 = pixel_valid
        col_addr_d2 = col_addr_d1
        col_addr_d1 = col_addr
        row_count_d2 = row_count_d1
        row_count_d1 = row_count
        
        # Address increment for next cycle
        if pixel_valid:
            if c == width - 1:
                col_addr = 0
                # row_count already updated above based on current row
            else:
                col_addr = c + 1
    
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

    frame, expected = generate_vectors_rtl_optimized(args.width, args.height, args.seed)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'sim', 'golden')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    in_mem_path = os.path.join(out_dir, 'input_rgb565.mem')
    exp_mem_path = os.path.join(out_dir, 'expected_output.mem')
    write_mem_hex(in_mem_path, frame)
    write_mem_hex(exp_mem_path, expected)

    print(f"Wrote {len(frame)} input pixels to {in_mem_path}")
    print(f"Wrote {len(expected)} expected outputs to {exp_mem_path}")
    expected_count = (args.height-2)*(args.width-2)  # Changed: now (H-2)*(W-2) due to col>=2
    print(f"Expected outputs: {len(expected)} (should be {expected_count})")

if __name__ == '__main__':
    main()
