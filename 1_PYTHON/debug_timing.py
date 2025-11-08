#!/usr/bin/env python3
"""
Debug script to trace first few outputs and verify timing.
"""
import sys
sys.path.insert(0, '.')
from generate_golden_rtl_aware_v2 import *

def trace_timing():
    width, height, seed = 64, 48, 123
    import random
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    gray_stream = [rgb565_to_gray8(px) for px in frame]
    
    # Pipeline state
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
    
    # Shift registers
    top_row = [0, 0, 0]
    mid_row = [0, 0, 0]
    bot_row = [0, 0, 0]
    
    # Control
    col_addr = 0
    row_count = 0
    
    output_count = 0
    idx = 0
    
    # Run for 4 rows + 2 drain cycles
    total_cycles = 4 * width + 2
    
    for cycle in range(total_cycles):
        # Input stage
        if cycle < height * width:
            r = cycle // width
            c = cycle % width
            pixel_valid = True
            pixel_in = gray_stream[idx]
            idx += 1
        else:
            pixel_valid = False
            pixel_in = 0
            c = 0
            r = height - 1
        
        # Shift registers update (at d2 stage)
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
            
            # Check window_valid
            window_valid = row_count_d2 >= 3 and col_addr_d2 >= 2
            
            if window_valid:
                output_count += 1
                if output_count <= 5 or output_count >= 62:
                    win = [top_row[:], mid_row[:], bot_row[:]]
                    e8 = sobel_edge8(win)
                    print(f"[OUTPUT {output_count:4d}] cycle={cycle} row_d2={row_count_d2} col_d2={col_addr_d2:2d} window={top_row[0]:02x}_{top_row[1]:02x}_{top_row[2]:02x}_{mid_row[0]:02x}_{mid_row[1]:02x}_{mid_row[2]:02x}_{bot_row[0]:02x}_{bot_row[1]:02x}_{bot_row[2]:02x} edge={e8:02x}")
        
        # BRAM read
        if pixel_valid_d1:
            line0_q = line0_mem[col_addr_d1]
            line1_q = line1_mem[col_addr_d1]
            line2_q = line2_mem[col_addr_d1]
        
        # BRAM write
        if pixel_valid:
            line2_mem[col_addr] = line1_mem[col_addr]
            line1_mem[col_addr] = line0_mem[col_addr]
            line0_mem[col_addr] = pixel_in
        
        # Pipeline advance
        pixel_in_d2 = pixel_in_d1
        pixel_in_d1 = pixel_in
        pixel_valid_d2 = pixel_valid_d1
        pixel_valid_d1 = pixel_valid
        col_addr_d2 = col_addr_d1
        col_addr_d1 = col_addr
        row_count_d2 = row_count_d1
        row_count_d1 = row_count
        
        # Address increment
        if pixel_valid:
            if c == width - 1:
                col_addr = 0
                if row_count < 0xFFFFFFFF:
                    row_count += 1
                    if row_count <= 4:
                        print(f"[ROW_INC] cycle={cycle} col={c} row_count={row_count-1} -> {row_count}")
            else:
                col_addr = c + 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Total outputs: {output_count}")
    print(f"Expected: 45 rows * 62 cols/row = {45*62}")

if __name__ == '__main__':
    trace_timing()
