# Sobel Edge Detection Project - Tang Nano 4K

## Project Overview
Implementing Sobel edge detection algorithm on Tang Nano 4K FPGA board, adapted from DE10-Nano implementation.

## Target Platform
- **FPGA**: Tang Nano 4K (Gowin GW1NSR-LV4C)
- **Camera**: Compatible camera module (to be determined)
- **Output**: HDMI/VGA display

## Key Components Needed

### 1. Hardware Description Language Files
```
src/
├── top_module.v              # Top-level module
├── sobel_filter.v           # Sobel edge detection core
├── camera_interface.v       # Camera input interface  
├── grayscale_converter.v    # RGB to Grayscale conversion
├── line_buffer.v           # Line buffering for 3x3 window
├── fifo_buffer.v           # FIFO for clock domain crossing
├── hdmi_output.v           # HDMI output controller
└── clk_divider.v           # Clock generation and division
```

### 2. Constraints Files
```
constraints/
├── tang_nano_4k.cst       # Pin assignments for Tang Nano 4K
└── timing.sdc             # Timing constraints
```

### 3. Simulation Files
```
sim/
├── testbench.v            # Main testbench
├── sobel_tb.v            # Sobel filter testbench  
└── test_patterns/        # Test images/patterns
```

### 4. Documentation
```
docs/
├── architecture.md        # System architecture
├── algorithm.md          # Sobel algorithm details
├── tang_nano_4k_guide.md # Board-specific implementation
└── performance_analysis.md # Timing and resource analysis
```

## Sobel Algorithm Implementation

### Sobel Kernels
```
Gx = [-1  0  1]    Gy = [-1 -2 -1]
     [-2  0  2]         [ 0  0  0]
     [-1  0  1]         [ 1  2  1]
```

### Processing Pipeline
1. **Camera Input** → Raw RGB data
2. **RGB to Grayscale** → Luminosity formula: `Y = 0.299R + 0.587G + 0.114B`
3. **Line Buffer** → Store 3 lines for 3x3 window
4. **Sobel Filter** → Apply Gx and Gy kernels
5. **Edge Magnitude** → `|Gx| + |Gy|` or `sqrt(Gx² + Gy²)`
6. **Output** → HDMI/VGA display

### Clock Domains
- **Camera Clock**: Input pixel clock
- **Processing Clock**: Internal processing (may be different)  
- **Display Clock**: HDMI/VGA output clock

## Tang Nano 4K Specific Considerations

### Resources Available
- Logic Elements: ~4K
- Memory: Block RAM + Distributed RAM
- PLLs: For clock generation
- I/O Pins: Limited compared to DE10-Nano

### Pin Mapping (To be determined)
- Camera interface pins
- HDMI output pins  
- Control switches/LEDs
- Clock input

### Tools
- **IDE**: Gowin FPGA Designer
- **Simulation**: Built-in simulator or ModelSim
- **Programming**: Gowin Programmer

## Next Steps
1. Analyze Tang Nano 4K pinout and resources
2. Adapt DE10-Nano Verilog code for Gowin FPGA
3. Implement camera interface for available camera modules
4. Optimize design for Tang Nano 4K resource constraints
5. Test and verify functionality

## References
- DE10-Nano Sobel implementation: https://github.com/grant4001/Sobel_DE10
- Tang Nano 4K documentation
- Gowin FPGA design guidelines
- Sobel edge detection algorithm references