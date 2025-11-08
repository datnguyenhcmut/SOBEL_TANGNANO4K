#!/usr/bin/env python3
"""
Model EXACT testbench timing including init cycles.
Testbench: 10 cycles rst_n=0, 5 cycles wait, 2 cycles vsync, then streaming
"""
from generate_golden_rtl_aware_v2 import *

def trace_with_init():
    width, height, seed = 64, 48, 123
    import random
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    gray_stream = [rgb565_to_gray8(px) for px in frame]
    
    # Pipeline state
    pixel_valid_d1 = False
    pixel_valid_d2 = False
    col_addr = 0
    col_addr_d1 = 0
    col_addr_d2 = 0
    row_count = 0
    row_count_d1 = 0
    row_count_d2 = 0
    pixel_in_d1 = 0
    pixel_in_d2 = 0
    
    # Sobel stages
    window_valid_sobel = False
    edge_sobel = 0
    window_valid_edge = False
    edge_edge = 0
    
    # BRAMs
    line0_mem = [0] * width
    line1_mem = [0] * width
    line2_mem = [0] * width
    line0_q = 0
    line1_q = 0
    line2_q = 0
    
    # Window
    top_row = [0, 0, 0]
    mid_row = [0, 0, 0]
    bot_row = [0, 0, 0]
    
    expected = []
    pixel_idx = 0
    
    # INIT CYCLES (match testbench exactly)
    INIT_CYCLES = 17  # 10 rst + 5 wait + 2 vsync
    
    # Total cycles: init + streaming + drain
    total_cycles = INIT_CYCLES + width * height + 4
    
    for cycle in range(total_cycles):
        # Determine if pixel_valid
        if cycle >= INIT_CYCLES and pixel_idx < width * height:
            pixel_valid = True
            pixel_in = gray_stream[pixel_idx]
            pixel_idx += 1
            
            # Calculate current row/col
            current_pixel = pixel_idx - 1
            current_row = current_pixel // width
            current_col = current_pixel % width
            row_count = current_row
        else:
            pixel_valid = False
            pixel_in = 0
        
        # === OUTPUT STAGE ===
        if window_valid_edge:
            rgb = pack_edge_to_rgb565(edge_edge)
            expected.append(rgb)
            
            # Print first few outputs
            if len(expected) <= 5:
                print(f"[Cycle {cycle:4d}] OUTPUT[{len(expected)-1:3d}] = 0x{rgb:04x}, "
                      f"row_d2={row_count_d2}, col_d2={col_addr_d2}, edge={edge_edge}")
        
        # === EDGE_MAG STAGE ===
        window_valid_edge = window_valid_sobel
        edge_edge = edge_sobel
        
        # === SOBEL_KERNEL STAGE ===
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
            
            window_valid = row_count_d2 >= 3 and col_addr_d2 >= 2
            
            if window_valid:
                win = [top_row[:], mid_row[:], bot_row[:]]
                edge_sobel = sobel_edge8(win)
                window_valid_sobel = True
            else:
                window_valid_sobel = False
        else:
            window_valid_sobel = False
        
        # === LINE_BUFFER STAGES ===
        if pixel_valid_d1:
            line0_q = line0_mem[col_addr_d1]
            line1_q = line1_mem[col_addr_d1]
            line2_q = line2_mem[col_addr_d1]
        
        # BRAM write
        if pixel_valid:
            line2_mem[col_addr] = line1_mem[col_addr]
            line1_mem[col_addr] = line0_mem[col_addr]
            line0_mem[col_addr] = pixel_in
        
        # col_addr increment (before pipeline advance to match RTL)
        next_col_addr = col_addr
        if pixel_valid:
            if col_addr == width - 1:
                next_col_addr = 0
            else:
                next_col_addr = col_addr + 1
        
        # Pipeline advance (model Verilog non-blocking: read all RHS first)
        old_pixel_valid_d1 = pixel_valid_d1
        
        pixel_valid_d2 = pixel_valid_d1
        pixel_valid_d1 = pixel_valid
        
        # d2 stage: conditional on OLD pixel_valid_d1
        if old_pixel_valid_d1:
            pixel_in_d2 = pixel_in_d1
            col_addr_d2 = col_addr_d1
            row_count_d2 = row_count_d1
        
        # d1 stage: conditional on pixel_valid
        if pixel_valid:
            pixel_in_d1 = pixel_in
            col_addr_d1 = col_addr
            row_count_d1 = row_count
        
        # Update col_addr
        col_addr = next_col_addr
    
    print(f"\nTotal outputs: {len(expected)}")
    return expected

if __name__ == '__main__':
    outputs = trace_with_init()
    print(f"First 5 outputs: {[f'0x{x:04x}' for x in outputs[:5]]}")
