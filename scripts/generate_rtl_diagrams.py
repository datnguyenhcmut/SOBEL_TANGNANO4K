#!/usr/bin/env python3
"""
Generate RTL block diagrams from Verilog files using Symbolator
"""
import os
import sys
import subprocess
from pathlib import Path

def generate_diagram(verilog_file, output_dir):
    """Generate SVG diagram for a Verilog module"""
    input_path = Path(verilog_file)
    output_dir_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    # Run symbolator (output is directory, not file)
    cmd = [
        'python', '-m', 'symbolator',
        '-i', str(input_path),
        '-o', str(output_dir_path),
        '--title', input_path.stem
    ]
    
    print(f"Generating diagram for {input_path.name}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Created diagram in: {output_dir_path}")
            return True
        else:
            print(f"✗ Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"✗ Exception: {e}")
        return False

def main():
    # Define RTL modules to diagram
    rtl_base = Path(__file__).parent.parent / 'rtl'
    output_base = Path(__file__).parent.parent / 'document' / 'rtl_diagrams'
    
    # List of important modules to diagram
    modules = [
        # Top level
        'top/edge_detection_top.v',
        
        # Image processing
        'image_processing/edge_stream_path.v',
        'image_processing/sobel_3x3_gray.v',
        'image_processing/scharr_3x3_gray.v',
        'image_processing/window3x3_stream.v',
        'image_processing/rgb2gray8.v',
        'image_processing/median3x3_stream.v',
        
        # Memory
        'memory/frame_buffer.v',
        'memory/sdram_controller.v',
        'memory/async_fifo.v',
        
        # VGA
        'vga/vga_controller.v',
        'vga/vga_adapter.v',
        
        # Control
        'control/test_pattern_gen.v',
        
        # Utils
        'utils/synchronizer.v',
        'utils/debouncer.v',
    ]
    
    print("=" * 60)
    print("RTL Diagram Generator")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for module_path in modules:
        verilog_file = rtl_base / module_path
        if verilog_file.exists():
            total_count += 1
            if generate_diagram(verilog_file, output_base):
                success_count += 1
        else:
            print(f"⚠ File not found: {verilog_file}")
    
    print("=" * 60)
    print(f"Completed: {success_count}/{total_count} diagrams generated")
    print(f"Output directory: {output_base}")
    print("=" * 60)

if __name__ == '__main__':
    main()
