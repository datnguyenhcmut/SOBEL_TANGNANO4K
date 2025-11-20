#!/usr/bin/env python3
"""
Analyze RTL diagrams and generate interconnection documentation
Author: Nguyễn Văn Đạt
"""
import re
from pathlib import Path
from collections import defaultdict

def parse_verilog_module(verilog_file):
    """Extract module name, inputs, outputs from Verilog file"""
    with open(verilog_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find module declaration
    module_match = re.search(r'module\s+(\w+)\s*(?:#\([^)]*\))?\s*\((.*?)\);', content, re.DOTALL)
    if not module_match:
        return None
    
    module_name = module_match.group(1)
    ports_text = module_match.group(2)
    
    # Parse ports
    inputs = []
    outputs = []
    inouts = []
    
    # Split by comma and analyze each port
    ports = re.split(r',\s*(?![^[]*\])', ports_text)
    
    for port in ports:
        port = port.strip()
        if not port:
            continue
            
        # Match: input/output [width] name
        port_match = re.match(r'(input|output|inout)\s+(?:wire|reg)?\s*(?:\[([^\]]+)\])?\s*(\w+)', port)
        if port_match:
            direction = port_match.group(1)
            width = port_match.group(2) if port_match.group(2) else '0:0'
            name = port_match.group(3)
            
            port_info = {
                'name': name,
                'width': width,
                'direction': direction
            }
            
            if direction == 'input':
                inputs.append(port_info)
            elif direction == 'output':
                outputs.append(port_info)
            elif direction == 'inout':
                inouts.append(port_info)
    
    return {
        'name': module_name,
        'inputs': inputs,
        'outputs': outputs,
        'inouts': inouts
    }

def generate_connection_diagram(modules_info):
    """Generate ASCII art connection diagram"""
    diagram = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    TANG NANO 4K - SOBEL SYSTEM ARCHITECTURE              ║
║                         Author: Nguyễn Văn Đạt - 2025                    ║
╚══════════════════════════════════════════════════════════════════════════╝

                                 ┌─────────────┐
                                 │  sys_clk    │
                                 │  sys_resetn │
                                 └──────┬──────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
            ┌───────▼────────┐  ┌──────▼───────┐  ┌────────▼────────┐
            │   VIDEO_TOP    │  │  UART_TOP    │  │   System Ctrl   │
            │                │  │              │  │                 │
            │  ┌──────────┐  │  │  ┌────────┐ │  │                 │
            │  │ Camera   │  │  │  │ TX/RX  │ │  │  Button/LED     │
            │  │ OV2640   │  │  │  │        │ │  │  Control        │
            │  └─────┬────┘  │  │  └───┬────┘ │  │                 │
            │        │       │  │      │      │  │                 │
            │  ┌─────▼─────┐ │  │  ┌───▼────┐ │  │                 │
            │  │RGB→Gray   │ │  │  │Serial  │ │  │                 │
            │  │Converter  │ │  │  │Port    │ │  │                 │
            │  └─────┬─────┘ │  │  └────────┘ │  │                 │
            │        │       │  └──────────────┘  └─────────────────┘
            │  ┌─────▼──────────┐                         │
            │  │ Line Buffer    │◄────────────────────────┘
            │  │ (3-line BRAM)  │      Control Signals
            │  └─────┬──────────┘
            │        │
            │  ┌─────▼──────────┐
            │  │ Gaussian Blur  │
            │  │   3x3 Kernel   │
            │  └─────┬──────────┘
            │        │
            │  ┌─────▼──────────┐
            │  │ Sobel Kernel   │
            │  │   Gx, Gy       │
            │  └─────┬──────────┘
            │        │
            │  ┌─────▼──────────┐
            │  │ Edge Magnitude │
            │  │  sqrt(Gx²+Gy²) │
            │  └─────┬──────────┘
            │        │
            │  ┌─────▼──────────┐
            │  │ Frame Buffer   │
            │  │  (HyperRAM)    │
            │  └─────┬──────────┘
            │        │
            │  ┌─────▼──────────┐
            │  │  DVI/HDMI TX   │
            │  │                │
            └──┴────────────────┴──►  TMDS Output
                                     (tmds_clk_p/n)
                                     (tmds_data_p/n[2:0])

═══════════════════════════════════════════════════════════════════════════
                            SIGNAL FLOW SUMMARY
═══════════════════════════════════════════════════════════════════════════
1. Camera → RGB565 pixel stream (PIXCLK, HREF, VSYNC, PIXDATA[7:0])
2. RGB565 → Grayscale (8-bit intensity)
3. Line Buffer → 3x3 window extraction
4. Gaussian Blur → noise reduction
5. Sobel Kernel → gradient calculation (Gx, Gy)
6. Edge Magnitude → |gradient| = sqrt(Gx² + Gy²)
7. Frame Buffer → HyperRAM storage
8. HDMI TX → TMDS serialized output

UART: Parallel debug/control interface
  - Commands: Enable/disable Sobel, read statistics
  - Baud: 115200, 8N1
═══════════════════════════════════════════════════════════════════════════
"""
    return diagram

def generate_detailed_connections(modules_info):
    """Generate detailed port-to-port connection table"""
    doc = """
╔══════════════════════════════════════════════════════════════════════════╗
║                    DETAILED PORT CONNECTIONS                              ║
╚══════════════════════════════════════════════════════════════════════════╝

"""
    
    # Sobel Pipeline
    doc += """
┌─────────────────────────────────────────────────────────────────────────┐
│ SOBEL EDGE DETECTION PIPELINE                                           │
└─────────────────────────────────────────────────────────────────────────┘

1. RGB to Grayscale Converter (rgb_to_gray.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk (27 MHz)            │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ rgb565         │ [15:0]       │ camera pixel data           │
   │ gray           │ [7:0]        │ → line_buffer.pixel_in      │
   └────────────────┴──────────────┴─────────────────────────────┘

2. Line Buffer (line_buffer.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk                     │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ pixel_in       │ [7:0]        │ rgb_to_gray.gray            │
   │ href           │ 1            │ camera HREF                 │
   │ vsync          │ 1            │ camera VSYNC                │
   │ p11-p33        │ [7:0] x 9    │ → gaussian_blur.window      │
   │ valid          │ 1            │ → gaussian_blur.valid_in    │
   └────────────────┴──────────────┴─────────────────────────────┘

3. Gaussian Blur (gaussian_blur.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk                     │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ p11-p33        │ [7:0] x 9    │ line_buffer outputs         │
   │ valid_in       │ 1            │ line_buffer.valid           │
   │ blurred_p11-33 │ [7:0] x 9    │ → sobel_kernel.window       │
   │ valid_out      │ 1            │ → sobel_kernel.valid_in     │
   └────────────────┴──────────────┴─────────────────────────────┘

4. Sobel Kernel (sobel_kernel.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk                     │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ p11-p33        │ [7:0] x 9    │ gaussian_blur outputs       │
   │ valid_in       │ 1            │ gaussian_blur.valid_out     │
   │ gx             │ [10:0]       │ → edge_mag.gx               │
   │ gy             │ [10:0]       │ → edge_mag.gy               │
   │ valid_out      │ 1            │ → edge_mag.valid_in         │
   └────────────────┴──────────────┴─────────────────────────────┘

5. Edge Magnitude (edge_mag.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk                     │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ gx             │ [10:0]       │ sobel_kernel.gx             │
   │ gy             │ [10:0]       │ sobel_kernel.gy             │
   │ valid_in       │ 1            │ sobel_kernel.valid_out      │
   │ magnitude      │ [7:0]        │ → display logic             │
   │ valid_out      │ 1            │ → pixel_valid               │
   └────────────────┴──────────────┴─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│ UART INTERFACE                                                           │
└─────────────────────────────────────────────────────────────────────────┘

1. UART TX (uart_tx.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk (27 MHz)            │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ tx_data        │ [7:0]        │ control logic               │
   │ tx_valid       │ 1            │ control logic               │
   │ tx_ready       │ 1            │ → control logic             │
   │ tx_pin         │ 1            │ → Physical UART TX pin      │
   └────────────────┴──────────────┴─────────────────────────────┘

2. UART RX (uart_rx.v)
   ┌────────────────┬──────────────┬─────────────────────────────┐
   │ Port           │ Width        │ Connection                  │
   ├────────────────┼──────────────┼─────────────────────────────┤
   │ clk            │ 1            │ sys_clk                     │
   │ rst_n          │ 1            │ sys_resetn                  │
   │ rx_pin         │ 1            │ Physical UART RX pin        │
   │ rx_data        │ [7:0]        │ → command decoder           │
   │ rx_valid       │ 1            │ → command decoder           │
   └────────────────┴──────────────┴─────────────────────────────┘

"""
    return doc

def main():
    verilog_base = Path(__file__).parent.parent / 'verilog'
    output_file = Path(__file__).parent.parent / 'docs' / 'CONNECTIONS.txt'
    
    # List of modules to analyze
    module_files = [
        'sobel/rgb_to_gray.v',
        'sobel/line_buffer.v',
        'sobel/gaussian_blur.v',
        'sobel/sobel_kernel.v',
        'sobel/edge_mag.v',
        'sobel/bram.v',
        'uart/uart_tx.v',
        'uart/uart_rx.v',
        'uart/uart_top.v',
    ]
    
    print("Analyzing Verilog modules...")
    modules_info = {}
    
    for module_file in module_files:
        full_path = verilog_base / module_file
        if full_path.exists():
            info = parse_verilog_module(full_path)
            if info:
                modules_info[info['name']] = info
                print(f"✓ Parsed: {info['name']}")
    
    # Generate documentation
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(generate_connection_diagram(modules_info))
        f.write("\n\n")
        f.write(generate_detailed_connections(modules_info))
    
    print(f"\n✓ Generated connection documentation: {output_file}")
    
    # Also generate Graphviz DOT file
    generate_graphviz(modules_info, output_file.parent / 'connections.dot')

def generate_graphviz(modules_info, output_file):
    """Generate Graphviz DOT file for visualization"""
    dot = """digraph SobelSystem {
    rankdir=TB;
    node [shape=box, style="rounded,filled", fillcolor=lightblue];
    
    // Top level
    subgraph cluster_input {
        label="Input";
        style=filled;
        fillcolor=lightgray;
        camera [label="Camera\\nOV2640", fillcolor=lightgreen];
        uart_in [label="UART RX", fillcolor=lightyellow];
    }
    
    // Sobel pipeline
    subgraph cluster_sobel {
        label="Sobel Edge Detection Pipeline";
        style=filled;
        fillcolor="#e6f2ff";
        
        rgb2gray [label="RGB→Gray\\nConverter"];
        linebuf [label="Line Buffer\\n(3-line BRAM)"];
        gaussian [label="Gaussian\\nBlur 3x3"];
        sobel [label="Sobel\\nKernel"];
        magnitude [label="Edge\\nMagnitude"];
        
        rgb2gray -> linebuf [label="gray[7:0]"];
        linebuf -> gaussian [label="9x pixels"];
        gaussian -> sobel [label="blurred\\nwindow"];
        sobel -> magnitude [label="Gx, Gy"];
    }
    
    // Output
    subgraph cluster_output {
        label="Output";
        style=filled;
        fillcolor=lightgray;
        framebuf [label="Frame Buffer\\n(HyperRAM)", fillcolor=lightcyan];
        hdmi [label="HDMI\\nTransmitter", fillcolor=lightcyan];
        uart_out [label="UART TX", fillcolor=lightyellow];
    }
    
    // Connections
    camera -> rgb2gray [label="RGB565"];
    magnitude -> framebuf [label="edge[7:0]"];
    framebuf -> hdmi [label="video\\nstream"];
    
    uart_in -> linebuf [label="control", style=dashed];
    magnitude -> uart_out [label="stats", style=dashed];
    
    // Legend
    {
        rank=sink;
        legend [shape=none, label=<
            <table border="0" cellspacing="0">
            <tr><td align="left"><b>Legend:</b></td></tr>
            <tr><td align="left">Solid lines: Data flow</td></tr>
            <tr><td align="left">Dashed lines: Control signals</td></tr>
            </table>
        >];
    }
}
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(dot)
    
    print(f"✓ Generated Graphviz DOT: {output_file}")
    print(f"  To visualize: dot -Tpng {output_file} -o connections.png")

if __name__ == '__main__':
    main()