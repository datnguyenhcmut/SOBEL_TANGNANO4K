RTL Modules Documentation
=========================

Sobel Edge Detection Pipeline
------------------------------

sobel_processor
~~~~~~~~~~~~~~~

Top-level Sobel edge detection processor integrating all pipeline stages.

**RTL Diagram:**

.. image:: _static/diagrams/sobel_processor-sobel_processor.svg
   :width: 100%
   :align: center
   :alt: Sobel Processor RTL Diagram

**Description:**

The ``sobel_processor`` module implements a complete edge detection pipeline:

1. RGB565 to Grayscale conversion
2. 3-line buffer for sliding window
3. Gaussian blur (noise reduction)
4. Sobel kernel (gradient computation)
5. Edge magnitude calculation

**Parameters:**

- ``IMG_WIDTH``: Image width (default: 640)
- ``IMG_HEIGHT``: Image height (default: 480)
- ``PIXEL_WIDTH``: Pixel bit width (default: 8)

**Ports:**

.. list-table::
   :header-rows: 1
   :widths: 20 10 10 60

   * - Port
     - Direction
     - Width
     - Description
   * - ``clk``
     - Input
     - 1
     - System clock
   * - ``rst_n``
     - Input
     - 1
     - Active-low reset
   * - ``pixel_in``
     - Input
     - 16
     - RGB565 pixel input
   * - ``href``
     - Input
     - 1
     - Horizontal reference (line valid)
   * - ``vsync``
     - Input
     - 1
     - Vertical sync (frame start)
   * - ``sobel_enable``
     - Input
     - 1
     - Enable edge detection
   * - ``pixel_out``
     - Output
     - 16
     - RGB565 output (edges or passthrough)
   * - ``pixel_valid``
     - Output
     - 1
     - Output pixel valid signal

rgb_to_gray
~~~~~~~~~~~

Converts RGB565 pixel format to 8-bit grayscale.

**RTL Diagram:**

.. image:: _static/diagrams/rgb_to_gray-rgb_to_gray.svg
   :width: 80%
   :align: center
   :alt: RGB to Gray RTL Diagram

**Conversion Formula:**

.. math::

   Gray = 0.299 \times R + 0.587 \times G + 0.114 \times B

Implemented using fixed-point approximation:

.. math::

   Gray = (77R + 150G + 29B) >> 8

line_buffer
~~~~~~~~~~~

Stores 3 image lines using BRAM to create a 3×3 sliding window.

**RTL Diagram:**

.. image:: _static/diagrams/line_buffer-line_buffer.svg
   :width: 100%
   :align: center
   :alt: Line Buffer RTL Diagram

**Features:**

- Triple line buffer using BRAM instances
- Outputs 9 pixels in 3×3 arrangement
- Circular buffer implementation
- 2-cycle read latency compensation

gaussian_blur
~~~~~~~~~~~~~

3×3 Gaussian blur filter for noise reduction before edge detection.

**RTL Diagram:**

.. image:: _static/diagrams/gaussian_blur-gaussian_blur.svg
   :width: 90%
   :align: center
   :alt: Gaussian Blur RTL Diagram

**Kernel:**

.. math::

   G = \frac{1}{16}
   \begin{bmatrix}
   1 & 2 & 1 \\
   2 & 4 & 2 \\
   1 & 2 & 1
   \end{bmatrix}

**Latency:** 1 clock cycle

sobel_kernel
~~~~~~~~~~~~

Computes horizontal (Gx) and vertical (Gy) gradients using Sobel operator.

**RTL Diagram:**

.. image:: _static/diagrams/sobel_kernel-sobel_kernel.svg
   :width: 90%
   :align: center
   :alt: Sobel Kernel RTL Diagram

**Sobel Kernels:**

.. math::

   G_x = \begin{bmatrix}
   -1 & 0 & 1 \\
   -2 & 0 & 2 \\
   -1 & 0 & 1
   \end{bmatrix}
   \quad
   G_y = \begin{bmatrix}
   -1 & -2 & -1 \\
   0 & 0 & 0 \\
   1 & 2 & 1
   \end{bmatrix}

**Output:**

- ``gx[10:0]``: Horizontal gradient (signed 11-bit)
- ``gy[10:0]``: Vertical gradient (signed 11-bit)

**Latency:** 1 clock cycle

edge_mag
~~~~~~~~

Calculates edge magnitude from gradients.

**RTL Diagram:**

.. image:: _static/diagrams/edge_mag-edge_mag.svg
   :width: 85%
   :align: center
   :alt: Edge Magnitude RTL Diagram

**Formula:**

.. math::

   |G| = \sqrt{G_x^2 + G_y^2} \approx |G_x| + |G_y|

Uses Manhattan distance approximation for FPGA efficiency.

**Scaling:** Output is scaled by dividing by 2 (right shift 1 bit) for optimal edge visibility.

**Latency:** 2 clock cycles

bram
~~~~

Block RAM wrapper for Gowin FPGA.

**Module Diagram:**

.. # hdl-diagram:: ../../verilog/sobel/bram.v
   :type: netlistsvg
   :module: bram

**Configuration:**

- Simple Dual-Port mode
- Port A: Write-only
- Port B: Read-only
- Read latency: 2 cycles (pipelined)

**Synthesis Attributes:**

.. code-block:: verilog

   (* ram_style = "block", syn_ramstyle = "block_ram" *)

UART Interface
--------------

uart_tx
~~~~~~~

UART transmitter module.

**Specifications:**

- Baud rate: 115200 (configurable)
- Data bits: 8
- Stop bits: 1
- Parity: None

uart_rx
~~~~~~~

UART receiver module with double-register synchronization.

**Features:**

- Start bit detection
- Mid-bit sampling
- Frame error detection
