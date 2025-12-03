System Architecture
===================

Overall System Block Diagram
-----------------------------

The Tang Nano 4K Sobel edge detection system consists of the following major components:

**System Overview:**

.. raw:: html

   <div style="text-align: center; margin: 20px 0;">
   <img src="https://via.placeholder.com/800x600/E3F2FD/1976D2?text=System+Architecture+Diagram" 
        alt="System Architecture will be rendered from DOT file" 
        style="max-width: 100%; border: 2px solid #1976D2; border-radius: 8px;">
   </div>

.. note::
   To view the full system architecture diagram, render the DOT file:
   ``sphinx-docs/source/_static/diagrams/system_architecture.dot``
   
   Use online tool: https://dreampuf.github.io/GraphvizOnline/

System Components
-----------------

1. **Input Interfaces**
   
   * OV2640 Camera - RGB565 video input at 640×480@30fps
   * Key Button - Mode control for switching between camera/testpattern

2. **Clock Generation**
   
   * Gowin PLLVR - Generates 74.25 MHz pixel clock and serial clocks from 27 MHz input
   * Provides 24 MHz camera clock (XCLK)

3. **Video Processing Pipeline**
   
   .. code-block:: text
   
      Camera → RGB→Gray → Line Buffer → Gaussian Blur → Sobel Kernel → Edge Magnitude
   
   * **RGB to Gray Converter**: Converts RGB565 to 8-bit grayscale
   * **Line Buffer**: 3-line BRAM buffer (640×3 pixels) for sliding window
   * **Gaussian Blur**: 3×3 filter for noise reduction
   * **Sobel Kernel**: Computes horizontal (Gx) and vertical (Gy) gradients
   * **Edge Magnitude**: Calculates √(Gx² + Gy²) approximation

4. **Frame Buffer System**
   
   * Frame Buffer Controller - Manages read/write operations
   * HyperRAM - 8MB external memory for double buffering
   * Stores processed frames (640×480×2 bytes per frame)

5. **Output Interfaces**
   
   * **DVI/HDMI Transmitter**: TMDS serialization for 720p@60Hz output
   * **UART Interface**: 115200 baud for debug and control commands
   * **LED Indicators**: 6 status LEDs

Data Flow
---------

**Main Video Path:**

1. OV2640 camera captures RGB565 frames at 30 fps
2. RGB565 → Grayscale conversion (8-bit per pixel)
3. Line buffer accumulates 3 rows for 3×3 window extraction
4. Gaussian blur reduces noise in 3×3 windows
5. Sobel kernel computes gradients (Gx, Gy)
6. Edge magnitude calculator produces final edge map
7. Frame buffer stores processed frame in HyperRAM
8. HDMI transmitter outputs to display at 720p@60Hz

**Control Path:**

* Button input controls mode selection (camera vs test pattern)
* UART receives commands for Sobel enable/disable
* UART transmits debug data and frame statistics
* LED indicators show system status

Resource Utilization
--------------------

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Resource
     - Used
     - Available
     - Percentage
   * - Logic Elements (LUTs)
     - ~2,500
     - 4,608
     - 54%
   * - Flip-Flops
     - ~1,800
     - 4,608
     - 39%
   * - Block RAM (BSRAM)
     - 6
     - 10
     - 60%
   * - DSP Blocks
     - 0
     - 8
     - 0%
   * - PLLs
     - 1
     - 2
     - 50%

Timing Performance
------------------

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Clock Domain
     - Frequency
     - Slack
   * - System Clock
     - 27 MHz
     - +10.2 ns
   * - Pixel Clock
     - 74.25 MHz
     - +2.8 ns
   * - Serial Clock (TMDS)
     - 371.25 MHz
     - +0.5 ns

Pipeline Latency
----------------

Total latency from camera input to edge detection output:

.. list-table::
   :header-rows: 1
   :widths: 40 30 30

   * - Stage
     - Cycles
     - Time (@ 27 MHz)
   * - RGB to Gray
     - 1
     - 37 ns
   * - Line Buffer
     - 2 lines + 2
     - ~47.4 μs
   * - Gaussian Blur
     - 1
     - 37 ns
   * - Sobel Kernel
     - 1
     - 37 ns
   * - Edge Magnitude
     - 2
     - 74 ns
   * - **Total**
     - **~1282**
     - **~47.5 μs**

Memory Organization
-------------------

**BRAM Usage:**

* Line Buffer 0: 640×8 bits = 5,120 bits
* Line Buffer 1: 640×8 bits = 5,120 bits  
* Line Buffer 2: 640×8 bits = 5,120 bits
* Total: 15,360 bits = ~1.88 KB (uses 6 BSRAM blocks)

**HyperRAM Layout:**

.. code-block:: text

   0x000000 - 0x096000  Frame Buffer 0 (614,400 bytes)
   0x096000 - 0x12C000  Frame Buffer 1 (614,400 bytes)
   0x12C000 - 0x1C2000  Reserved (614,400 bytes)
   0x1C2000 - 0x800000  Unused (~6.2 MB)

External Interfaces
-------------------

**Camera Interface (DVP):**

* PIXDATA[7:0] - Parallel pixel data
* PIXCLK - Pixel clock input
* HREF - Horizontal reference
* VSYNC - Vertical sync
* I2C (SCL/SDA) - Configuration interface

**HDMI Interface:**

* tmds_clk_p/n - Differential clock pair
* tmds_data_p/n[2:0] - 3 differential data pairs

**UART Interface:**

* TX - Transmit data
* RX - Receive data
* Baud: 115200, 8N1

Power Consumption
-----------------

Estimated power consumption:

* Core logic: ~150 mW
* I/O: ~50 mW  
* BRAM: ~20 mW
* PLL: ~30 mW
* **Total**: ~250 mW @ 3.3V

Design Constraints
------------------

* Minimum camera frame rate: 15 fps
* Maximum processing latency: 2 lines
* HDMI output resolution: 720p (1280×720)
* HDMI refresh rate: 60 Hz
* Power budget: < 500 mW
