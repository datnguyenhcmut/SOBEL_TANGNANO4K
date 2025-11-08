# Test Sobel với real images và performance analysis
# Chuẩn bị cho FPGA implementation

import numpy as np
import cv2
import matplotlib.pyplot as plt
import time
from sobel_study import SobelEdgeDetector
import os

def analyze_fpga_requirements():
    """
    Analyze requirements cho FPGA implementation:
    - Memory usage
    - Processing time
    - Bit width requirements
    - Clock cycles estimation
    """
    print("=== FPGA Implementation Analysis ===\n")
    
    detector = SobelEdgeDetector()
    
    # Test với different image sizes (tương ứng với camera resolutions)
    test_sizes = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"), 
        (800, 600, "SVGA"),
        (1024, 768, "XGA")
    ]
    
    print("Image Size Analysis:")
    print("Size\t\tPixels\t\tMemory(KB)\tLine Buffers")
    print("-" * 55)
    
    for width, height, name in test_sizes:
        pixels = width * height
        memory_kb = pixels * 1 / 1024  # 8-bit grayscale
        line_buffer_kb = width * 3 * 1 / 1024  # 3 lines for 3x3 window
        
        print(f"{name}\t\t{pixels}\t\t{memory_kb:.1f}\t\t{line_buffer_kb:.2f}")
    
    print("\n" + "="*55)
    
    # Bit width analysis
    print("\nBit Width Requirements:")
    print("- Input pixel: 8 bits")
    print("- Sobel Gx/Gy: 8 + log2(8) = 11 bits (signed)")
    print("- Magnitude |Gx|+|Gy|: 12 bits") 
    print("- Output (saturated): 8 bits")
    
    # Timing analysis
    print("\nTiming Analysis (for VGA 640x480 @ 60fps):")
    pixels_per_second = 640 * 480 * 60
    print(f"- Pixel rate: {pixels_per_second:,} pixels/second")
    print(f"- Clock requirement: ≥ {pixels_per_second/1e6:.1f} MHz")
    print(f"- Processing cycles per pixel: 1-3 cycles")
    print(f"- Recommended clock: {pixels_per_second*3/1e6:.0f} MHz")

def test_with_camera_simulation():
    """
    Simulate camera input để test real-time processing
    """
    print("\n=== Camera Simulation Test ===")
    
    detector = SobelEdgeDetector()
    
    # Create synthetic "camera" frames
    frames = []
    for i in range(10):
        # Simulate moving object
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Moving rectangle (simulated object)
        x = (i * 30) % 250
        y = 50 + int(20 * np.sin(i * 0.5))
        
        frame[y:y+40, x:x+60] = [255, 255, 255]
        frame[y+10:y+30, x+10:x+50] = [128, 128, 128]
        
        frames.append(frame)
    
    # Process frames và measure performance
    processing_times = []
    
    print("Processing frames...")
    for i, frame in enumerate(frames):
        start_time = time.time()
        
        # FPGA-style processing
        result = detector.apply_sobel_fpga_style(frame)
        
        end_time = time.time()
        processing_time = (end_time - start_time) * 1000  # ms
        processing_times.append(processing_time)
        
        print(f"Frame {i}: {processing_time:.2f} ms")
        
        # Save some frames for inspection
        if i < 3:
            cv2.imwrite(f"results/frame_{i}_original.png", frame)
            cv2.imwrite(f"results/frame_{i}_sobel.png", result)
    
    avg_time = np.mean(processing_times)
    max_fps = 1000 / avg_time
    
    print(f"\nPerformance Summary:")
    print(f"- Average processing time: {avg_time:.2f} ms")
    print(f"- Theoretical max FPS: {max_fps:.1f}")
    print(f"- Target: 60 FPS (16.67 ms per frame)")
    print(f"- Status: {'✓ PASS' if avg_time < 16.67 else '✗ FAIL - Need optimization'}")

def generate_verilog_parameters():
    """
    Generate parameters cho Verilog implementation
    """
    print("\n=== Verilog Parameters Generation ===")
    
    # Image parameters
    img_width = 640
    img_height = 480
    pixel_bits = 8
    
    # Calculate derived parameters
    addr_width = int(np.ceil(np.log2(img_width)))
    counter_width = int(np.ceil(np.log2(max(img_width, img_height))))
    sobel_bits = pixel_bits + 3  # For Sobel calculation
    
    verilog_params = f"""
// Generated Parameters for Tang Nano 4K Sobel Implementation
// Date: {time.strftime('%Y-%m-%d %H:%M:%S')}

// Image dimensions
parameter IMG_WIDTH = {img_width};
parameter IMG_HEIGHT = {img_height};

// Data widths
parameter PIXEL_WIDTH = {pixel_bits};
parameter ADDR_WIDTH = {addr_width};
parameter COUNTER_WIDTH = {counter_width};
parameter SOBEL_WIDTH = {sobel_bits};

// Line buffer size
parameter LINE_BUFFER_SIZE = IMG_WIDTH;

// Sobel kernels (as parameters)
parameter signed [SOBEL_WIDTH-1:0] SOBEL_Gx [0:8] = {{
    -1,  0,  1,
    -2,  0,  2, 
    -1,  0,  1
}};

parameter signed [SOBEL_WIDTH-1:0] SOBEL_Gy [0:8] = {{
    -1, -2, -1,
     0,  0,  0,
     1,  2,  1  
}};

// Clock domains (estimates for Tang Nano 4K)
parameter CLK_CAMERA = 25_000_000;    // 25 MHz camera clock
parameter CLK_PROCESS = 75_000_000;   // 75 MHz processing clock  
parameter CLK_HDMI = 25_000_000;      // 25 MHz HDMI pixel clock (VGA)
"""
    
    # Save to file
    os.makedirs("results", exist_ok=True)
    with open("results/verilog_parameters.v", "w") as f:
        f.write(verilog_params)
    
    print("Verilog parameters saved to: results/verilog_parameters.v")
    print("Key findings:")
    print(f"- Line buffer width: {addr_width} bits")
    print(f"- Counter width: {counter_width} bits") 
    print(f"- Sobel calculation: {sobel_bits} bits")
    print(f"- Memory needed: {img_width * 3} bytes (3 line buffers)")

def main():
    """
    Main analysis function
    """
    # Create results directory
    os.makedirs("results", exist_ok=True)
    
    # Run all analyses
    analyze_fpga_requirements()
    test_with_camera_simulation()
    generate_verilog_parameters()
    
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE!")
    print("Next steps:")
    print("1. Review results/ folder")
    print("2. Optimize algorithm if needed")
    print("3. Start Verilog implementation")
    print("4. Tang Nano 4K constraint files")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()