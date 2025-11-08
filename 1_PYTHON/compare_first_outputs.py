#!/usr/bin/env python3
"""
Compare Python golden generator with RTL simulation output.
This helps identify where the mismatch comes from.
"""
import sys
sys.path.insert(0, '.')
from generate_golden_rtl_aware_v2 import *

def analyze_mismatch():
    width, height, seed = 64, 48, 123
    import random
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    gray_stream = [rgb565_to_gray8(px) for px in frame]
    
    # Show first few input pixels
    print("=== INPUT RGB565 (first 3 rows x 10 cols) ===")
    for r in range(3):
        row_str = ""
        for c in range(10):
            idx = r * width + c
            row_str += f"{frame[idx]:04x} "
        print(f"Row {r}: {row_str}")
    
    # Show grayscale conversion
    print("\n=== GRAYSCALE (first 3 rows x 10 cols) ===")
    for r in range(3):
        row_str = ""
        for c in range(10):
            idx = r * width + c
            row_str += f"{gray_stream[idx]:02x} "
        print(f"Row {r}: {row_str}")
    
    # Now run the full pipeline simulation
    print("\n=== RUNNING PIPELINE SIMULATION ===")
    _, expected = generate_vectors_rtl_optimized(width, height, seed)
    
    print(f"\nGenerated {len(expected)} outputs")
    print(f"Expected: {(height-3)*(width-2)} outputs")
    
    # Show first 10 expected outputs
    print("\n=== FIRST 10 EXPECTED OUTPUTS ===")
    for i in range(min(10, len(expected))):
        rgb = expected[i]
        # Extract edge magnitude from RGB565
        r5 = (rgb >> 11) & 0x1F
        edge = (r5 << 3) | (r5 >> 2)
        print(f"Output {i}: 0x{rgb:04x} (edge={edge} 0x{edge:02x})")
    
    # Load RTL output
    import os
    got_path = os.path.join(os.path.dirname(__file__), '..', 'sim', 'golden', 'got_output.mem')
    if os.path.exists(got_path):
        print("\n=== RTL OUTPUTS (from got_output.mem) ===")
        with open(got_path, 'r') as f:
            rtl_outputs = [int(line.strip(), 16) for line in f 
                          if line.strip() and not line.strip().startswith('//')]
        
        print(f"RTL generated {len(rtl_outputs)} outputs")
        
        # Compare first 10
        print("\n=== COMPARISON (first 10) ===")
        print("Idx | RTL     | Python  | Match | RTL_edge | Py_edge")
        print("----|---------|---------|-------|----------|--------")
        for i in range(min(10, len(rtl_outputs), len(expected))):
            rtl = rtl_outputs[i]
            py = expected[i]
            match = "✓" if rtl == py else "✗"
            
            rtl_r5 = (rtl >> 11) & 0x1F
            rtl_edge = (rtl_r5 << 3) | (rtl_r5 >> 2)
            
            py_r5 = (py >> 11) & 0x1F
            py_edge = (py_r5 << 3) | (py_r5 >> 2)
            
            print(f"{i:3d} | {rtl:04x}    | {py:04x}    | {match:^5} | {rtl_edge:3d} ({rtl_edge:02x}) | {py_edge:3d} ({py_edge:02x})")
    else:
        print(f"\n[WARN] RTL output file not found: {got_path}")
        print("Run 'make golden' first to generate RTL outputs")

if __name__ == '__main__':
    analyze_mismatch()
