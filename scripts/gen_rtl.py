#!/usr/bin/env python3
"""
Generate RTL block diagrams from Verilog files using Symbolator
Author: Nguyễn Văn Đạt
Target: Tang Nano 4K Sobel Edge Detection Project
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
    verilog_base = Path(__file__).parent.parent / 'verilog'
    output_base = Path(__file__).parent.parent / 'docs' / 'rtl_diagrams'
    
    # List of modules from your project
    modules = [
        # Top level
        ('src/video_top.v', 'Video Top Module'),
        ('src/system_top.v', 'System Top with UART'),
        
        # Sobel edge detection pipeline
        ('sobel/sobel_processor.v', 'Sobel Processor Pipeline'),
        ('sobel/rgb_to_gray.v', 'RGB565 to Grayscale Converter'),
        ('sobel/line_buffer.v', 'Line Buffer for 3x3 Window'),
        ('sobel/gaussian_blur.v', 'Gaussian Blur Filter'),
        ('sobel/sobel_kernel.v', 'Sobel Kernel (Gx, Gy)'),
        ('sobel/edge_mag.v', 'Edge Magnitude Calculator'),
        ('sobel/bram.v', 'Block RAM Wrapper'),
        
        # UART communication
        ('uart/uart_tx.v', 'UART Transmitter'),
        ('uart/uart_rx.v', 'UART Receiver'),
        ('uart/uart_top.v', 'UART Top Wrapper'),
        
        # Video pipeline (if exists)
        ('src/DVI_TX_Top.v', 'DVI/HDMI Transmitter Top'),
        ('src/Video_Frame_Buffer_Top.v', 'Frame Buffer Controller'),
        ('src/HyperRAM_Memory_Interface_Top.v', 'HyperRAM Interface'),
    ]
    
    print("=" * 70)
    print("RTL Diagram Generator - Tang Nano 4K Sobel Project")
    print("=" * 70)
    
    success_count = 0
    total_count = 0
    
    for module_path, description in modules:
        verilog_file = verilog_base / module_path
        if verilog_file.exists():
            total_count += 1
            print(f"\n{description}:")
            if generate_diagram(verilog_file, output_base / verilog_file.parent.name):
                success_count += 1
        else:
            print(f"⚠ File not found: {verilog_file}")
    
    print("\n" + "=" * 70)
    print(f"Completed: {success_count}/{total_count} diagrams generated")
    print(f"Output directory: {output_base}")
    print("=" * 70)
    
    # Generate index HTML
    generate_index_html(output_base, modules, verilog_base)

def generate_index_html(output_dir, modules, verilog_base):
    """Generate an index.html to view all diagrams"""
    html_file = output_dir / 'index.html'
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RTL Diagrams - Tang Nano 4K Sobel Project</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .module-section {
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .diagram-container {
            text-align: center;
            margin: 20px 0;
        }
        .diagram-container img {
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 10px;
            background: white;
        }
        .module-info {
            color: #666;
            font-style: italic;
            margin-bottom: 10px;
        }
        .author {
            text-align: right;
            color: #888;
            margin-top: 40px;
            font-size: 0.9em;
        }
    </style>
</head>
<body>
    <h1>RTL Block Diagrams - Tang Nano 4K Sobel Edge Detection</h1>
    <p class="module-info">Author: Nguyễn Văn Đạt | Generated: 2025</p>
"""
    
    current_category = None
    for module_path, description in modules:
        verilog_file = verilog_base / module_path
        if not verilog_file.exists():
            continue
            
        category = verilog_file.parent.name
        if category != current_category:
            if current_category is not None:
                html_content += "    </div>\n"
            html_content += f'    <h2>{category.upper()} Modules</h2>\n'
            html_content += '    <div class="module-section">\n'
            current_category = category
        
        svg_path = f"{category}/{verilog_file.stem}.svg"
        html_content += f"""
        <div class="diagram-container">
            <h3>{description}</h3>
            <p class="module-info">File: {module_path}</p>
            <img src="{svg_path}" alt="{description}">
        </div>
"""
    
    if current_category is not None:
        html_content += "    </div>\n"
    
    html_content += """
    <div class="author">
        <p>Tang Nano 4K FPGA Edge Detection Project</p>
        <p>© 2025 Nguyễn Văn Đạt</p>
    </div>
</body>
</html>
"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✓ Generated index.html: {html_file}")

if __name__ == '__main__':
    main()