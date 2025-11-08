# Main runner để test Sobel algorithm
# Run này trước khi implement Verilog

import sys
import os

def main():
    print("=" * 60)
    print("SOBEL EDGE DETECTION - PYTHON STUDY")
    print("Tang Nano 4K FPGA Project")
    print("=" * 60)
    
    print("\nStep 1: Algorithm Understanding & Implementation")
    print("Running sobel_study.py...")
    
    try:
        exec(open('sobel_study.py', encoding='utf-8').read())
        print("✓ Algorithm study completed successfully")
    except Exception as e:
        print(f"✗ Error in algorithm study: {e}")
        return
    
    print("\nStep 2: FPGA Requirements Analysis")  
    print("Running fpga_analysis.py...")
    
    try:
        exec(open('fpga_analysis.py', encoding='utf-8').read())
        print("✓ FPGA analysis completed successfully")
    except Exception as e:
        print(f"✗ Error in FPGA analysis: {e}")
        return
        
    print(f"\n{'='*60}")
    print("ALL PYTHON TESTS COMPLETED!")
    print("\nResults available in:")
    print("- results/ folder: Images và analysis")
    print("- Console output: Performance metrics")
    print("\nReady for Verilog implementation!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()