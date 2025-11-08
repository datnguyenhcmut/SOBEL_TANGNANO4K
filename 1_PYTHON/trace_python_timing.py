#!/usr/bin/env python3
"""
Detailed cycle-by-cycle trace showing EXACT window for each output.
This will help identify the timing offset between Python and RTL.
"""
import sys
sys.path.insert(0, '.')
from generate_golden_rtl_aware_v2 import *

def trace_detailed():
    width, height, seed = 64, 48, 123
    import random
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    gray_stream = [rgb565_to_gray8(px) for px in frame]
    
    # Pipeline state (2 stages: d1, d2)
    pixel_valid_d1 = False
    pixel_valid_d2 = False
    col_addr_d1 = 0
    col_addr_d2 = 0
    row_count_d1 = 0
    row_count_d2 = 0
    pixel_in_d1 = 0
    pixel_in_d2 = 0
    
    # BRAMs
    line0_mem = [0] * width
    line1_mem = [0] * width
    line2_mem = [0] * width
    line0_q = 0
    line1_q = 0
    line2_q = 0
    
    # Shift registers (3x3 window)
    top_row = [0, 0, 0]
    mid_row = [0, 0, 0]
    bot_row = [0, 0, 0]
    
    # Control
    col_addr = 0
    row_count = 0
    current_row = 0
    
    expected = []
    idx = 0
    
    # Run enough cycles to get at least 10 outputs
    total_cycles = 5 * width + 10
    
    print("=== DETAILED CYCLE-BY-CYCLE TRACE ===\n")
    print("Cycle | r c | pv_d2 row_d2 col_d2 | window_valid | window                           | edge | output")
    print("------|-----|---------------------|--------------|----------------------------------|------|-------")
    
    for cycle in range(total_cycles):
        # Input stage
        if cycle < height * width:
            r = cycle // width
            c = cycle % width
            pixel_valid = True
            pixel_in = gray_stream[idx]
            idx += 1
            current_row = r
            row_count = r
        else:
            pixel_valid = False
            pixel_in = 0
            c = 0
            r = height - 1
        
        # === Cycle logic (at clock edge) ===
        
        # Shift registers update (at d2 stage) - AFTER BRAM read completes
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
            
            window_str = f"{top_row[0]:02x}_{top_row[1]:02x}_{top_row[2]:02x}_{mid_row[0]:02x}_{mid_row[1]:02x}_{mid_row[2]:02x}_{bot_row[0]:02x}_{bot_row[1]:02x}_{bot_row[2]:02x}"
            
            if window_valid:
                win = [top_row[:], mid_row[:], bot_row[:]]
                e8 = sobel_edge8(win)
                r5 = (e8 >> 3) & 0x1F
                g6 = (e8 >> 2) & 0x3F
                b5 = (e8 >> 3) & 0x1F
                rgb565 = (r5 << 11) | (g6 << 5) | b5
                expected.append(rgb565)
                
                output_idx = len(expected) - 1
                print(f"{cycle:5d} | {r:1d} {c:2d} | {int(pixel_valid_d2):1d}     {row_count_d2:2d}      {col_addr_d2:2d}      | YES          | {window_str} | {e8:3d}  | [{output_idx:3d}] 0x{rgb565:04x}")
                
                if output_idx >= 9:
                    break
            else:
                wv_str = "NO" if pixel_valid_d2 else "--"
                if pixel_valid_d2 and (row_count_d2 == 2 or (row_count_d2 == 3 and col_addr_d2 <= 3)):
                    print(f"{cycle:5d} | {r:1d} {c:2d} | {int(pixel_valid_d2):1d}     {row_count_d2:2d}      {col_addr_d2:2d}      | {wv_str:12} | {window_str} |      |")
        
        # BRAM read (2-cycle latency: addr @ d0 → data @ d2)
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
            else:
                col_addr = c + 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Generated {len(expected)} outputs")
    print(f"\nFirst 10 expected outputs:")
    for i in range(min(10, len(expected))):
        print(f"  [{i}] 0x{expected[i]:04x}")

if __name__ == '__main__':
    trace_detailed()
