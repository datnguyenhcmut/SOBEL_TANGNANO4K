.. Tang Nano 4K Sobel documentation master file
   Author: Nguyễn Văn Đạt
   Created: November 2025

Tang Nano 4K Sobel Edge Detection
===================================

**Real-time Edge Detection on FPGA**

**Author:** Nguyễn Văn Đạt

**Target:** Tang Nano 4K (Gowin GW1NSR-LV4C)

Overview
--------

This project implements a complete real-time Sobel edge detection system on the Tang Nano 4K FPGA board.

**Pipeline Architecture:**

.. code-block:: text

   Camera OV2640 → RGB→Gray → Line Buffer → Gaussian Blur → Sobel Kernel 
                                                ↓
                  HDMI Output ← Frame Buffer ← Edge Magnitude

**Key Features:**

* Real-time 640×480 video processing at 60 FPS
* Gaussian blur preprocessing for noise reduction
* Optimized edge magnitude scaling for visibility
* HDMI output with frame buffering
* UART debug interface

**Resource Usage:**

* LUTs: ~2,500 / 4,608 (54%)
* BRAM: 6 / 10 blocks (60%)
* Clock: 27 MHz system, 74.25 MHz HDMI

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Documentation:

   modules
   architecture
   simulation
   build

Quick Start
-----------

1. **Clone Repository:**

   .. code-block:: bash

      git clone https://github.com/datnguyenhcmut/SOBEL_TANGNANO4K.git
      cd SOBEL_TANGNANO4K

2. **Build with Gowin EDA:**

   - Open ``verilog/camera_hdmi.gprj``
   - Synthesize and Place & Route
   - Program FPGA

3. **Run Simulation:**

   .. code-block:: bash

      cd sim
      make msim-gui

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

