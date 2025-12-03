"""
Generate test data and golden reference for Verilog testbench
Creates binary files that can be read by SystemVerilog
"""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import struct
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def rgb888_to_rgb565(r, g, b):
    """Convert RGB888 to RGB565 format"""
    r5 = (r >> 3) & 0x1F
    g6 = (g >> 2) & 0x3F
    b5 = (b >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5

def load_test_image(filename, target_size=(640, 480)):
    """Load and resize test image"""
    img = Image.open(filename).convert('RGB')
    img = img.resize(target_size, Image.Resampling.LANCZOS)
    return np.array(img)

def create_simple_test_image(width=640, height=480):
    """Create synthetic test image with known edges"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Background gradient
    for y in range(height):
        intensity = int(100 + 50 * y / height)
        img[y, :] = [intensity, intensity, intensity]
    
    # Vertical edge (left side)
    img[:, 200:210] = 255
    
    # Horizontal edge (middle)
    img[240:250, :] = 255
    
    # Diagonal edge
    for i in range(min(width, height)):
        if i < width and i < height:
            img[i, i] = 255
    
    # Rectangle (license plate simulation)
    img[300:350, 250:400] = [200, 200, 200]
    img[300:302, 250:400] = 255  # Top edge
    img[348:350, 250:400] = 255  # Bottom edge
    img[300:350, 250:252] = 255  # Left edge
    img[300:350, 398:400] = 255  # Right edge
    
    return img

def rgb_to_gray(rgb):
    """Convert RGB to grayscale (same as Verilog)"""
    # Verilog uses: gray = (R*77 + G*150 + B*29) >> 8
    r = rgb[:,:,0].astype(np.int32)
    g = rgb[:,:,1].astype(np.int32)
    b = rgb[:,:,2].astype(np.int32)
    gray = (r * 77 + g * 150 + b * 29) >> 8
    return gray.astype(np.uint8)

def bilateral_filter_python(img, sigma_spatial=2, sigma_range=20):
    """Bilateral filter matching Verilog implementation"""
    from scipy import ndimage
    height, width = img.shape
    output = np.zeros_like(img)
    
    # Simple 3x3 bilateral for speed
    for y in range(1, height-1):
        for x in range(1, width-1):
            center = img[y, x]
            total_weight = 0
            weighted_sum = 0
            
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    neighbor = img[y+dy, x+dx]
                    intensity_diff = abs(int(neighbor) - int(center))
                    
                    if intensity_diff < sigma_range:
                        weight = 1.0 / (1 + (dx*dx + dy*dy) + intensity_diff)
                        weighted_sum += neighbor * weight
                        total_weight += weight
            
            output[y, x] = int(weighted_sum / total_weight) if total_weight > 0 else center
    
    # Copy borders
    output[0, :] = img[0, :]
    output[-1, :] = img[-1, :]
    output[:, 0] = img[:, 0]
    output[:, -1] = img[:, -1]
    
    return output

def sobel_filter_python(img):
    """Sobel edge detection matching Verilog"""
    from scipy import ndimage
    
    # Sobel kernels
    sobel_x = ndimage.sobel(img, axis=1)
    sobel_y = ndimage.sobel(img, axis=0)
    
    # Magnitude
    magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)
    
    return magnitude

def apply_thresholds(magnitude, high_threshold=115, low_threshold=65):
    """Apply hysteresis thresholding (Canny-style)"""
    height, width = magnitude.shape
    output = np.zeros_like(magnitude, dtype=np.uint8)
    
    # Strong edges
    strong = magnitude >= high_threshold
    # Weak edges
    weak = (magnitude >= low_threshold) & (magnitude < high_threshold)
    
    output[strong] = 255
    
    # Connect weak edges to strong edges
    from scipy import ndimage
    labeled, num_features = ndimage.label(weak)
    for i in range(1, num_features + 1):
        region = labeled == i
        # Check if region touches strong edge
        dilated = ndimage.binary_dilation(region)
        if np.any(dilated & strong):
            output[region] = 255
    
    return output

def noise_rejection_filter(binary_img):
    """Apply noise rejection filter (matching Verilog)"""
    height, width = binary_img.shape
    output = np.zeros_like(binary_img)
    
    for y in range(2, height):
        for x in range(1, width-1):
            if binary_img[y, x] > 0:
                # Check horizontal neighbors
                has_horizontal = (binary_img[y, x-1] > 0) or (binary_img[y, x+1] > 0)
                # Check vertical neighbors (previous rows)
                has_vertical = (binary_img[y-1, x] > 0) or (binary_img[y-2, x] > 0)
                
                if has_horizontal or has_vertical:
                    output[y, x] = 255
    
    return output

def generate_golden_reference(rgb_img):
    """Complete pipeline matching Verilog"""
    print("Generating golden reference...")
    
    # Step 1: RGB to Gray
    print("  1. RGB to Grayscale...")
    gray = rgb_to_gray(rgb_img)
    
    # Step 2: Bilateral filter
    print("  2. Bilateral filter...")
    bilateral = bilateral_filter_python(gray, sigma_range=20)
    
    # Step 3: Sobel edge detection
    print("  3. Sobel edge detection...")
    edges = sobel_filter_python(bilateral)
    
    # Step 4: Thresholding
    print("  4. Hysteresis thresholding...")
    binary = apply_thresholds(edges, high_threshold=95, low_threshold=55)
    
    # Step 5: Noise rejection
    print("  5. Noise rejection filter...")
    final = noise_rejection_filter(binary)
    
    return {
        'gray': gray,
        'bilateral': bilateral,
        'edges': edges,
        'binary': binary,
        'final': final
    }

def save_binary_file(data, filename):
    """Save numpy array as binary file"""
    with open(filename, 'wb') as f:
        f.write(data.tobytes())
    print(f"Saved: {filename}")

def save_rgb565_image(rgb_img, filename):
    """Save RGB image as RGB565 binary"""
    height, width, _ = rgb_img.shape
    with open(filename, 'wb') as f:
        for y in range(height):
            for x in range(width):
                r, g, b = rgb_img[y, x]
                rgb565 = rgb888_to_rgb565(r, g, b)
                f.write(struct.pack('<H', rgb565))  # Little endian 16-bit
    print(f"Saved: {filename} (RGB565)")

def visualize_pipeline(rgb_img, results):
    """Visualize all pipeline stages"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    axes[0, 0].imshow(rgb_img)
    axes[0, 0].set_title('Input RGB')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(results['gray'], cmap='gray')
    axes[0, 1].set_title('Grayscale')
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(results['bilateral'], cmap='gray')
    axes[0, 2].set_title('Bilateral Filtered')
    axes[0, 2].axis('off')
    
    axes[1, 0].imshow(results['edges'], cmap='gray')
    axes[1, 0].set_title('Sobel Edges')
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(results['binary'], cmap='gray')
    axes[1, 1].set_title('Hysteresis Threshold')
    axes[1, 1].axis('off')
    
    axes[1, 2].imshow(results['final'], cmap='gray')
    axes[1, 2].set_title('Final Output (After Noise Rejection)')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig('../sim/data/pipeline_stages.png', dpi=150, bbox_inches='tight')
    print("Saved: ../sim/data/pipeline_stages.png")
    plt.show()

def main():
    print("="*70)
    print("Sobel Pipeline Test Data Generator")
    print("="*70)
    
    # Create output directory
    os.makedirs('../sim/data', exist_ok=True)
    
    # Option 1: Use synthetic test image
    print("\nCreating synthetic test image...")
    rgb_img = create_simple_test_image()
    
    # Option 2: Load real image (uncomment to use)
    # print("\nLoading test image...")
    # rgb_img = load_test_image('test_road.jpg')
    
    print(f"Image size: {rgb_img.shape}")
    
    # Generate golden reference
    results = generate_golden_reference(rgb_img)
    
    # Save input as RGB565
    print("\nSaving test data...")
    save_rgb565_image(rgb_img, '../sim/data/input_rgb565.bin')
    
    # Save golden reference
    save_binary_file(results['final'], '../sim/data/expected_output.bin')
    
    # Save intermediate stages for debugging
    save_binary_file(results['gray'], '../sim/data/debug_gray.bin')
    save_binary_file(results['edges'], '../sim/data/debug_edges.bin')
    save_binary_file(results['binary'], '../sim/data/debug_binary.bin')
    
    # Visualize
    print("\nVisualizing pipeline stages...")
    visualize_pipeline(rgb_img, results)
    
    # Statistics
    print("\n" + "="*70)
    print("STATISTICS:")
    print("="*70)
    print(f"Total pixels:      {rgb_img.shape[0] * rgb_img.shape[1]}")
    print(f"Edge pixels:       {np.sum(results['final'] > 0)} ({100*np.sum(results['final'] > 0)/(rgb_img.shape[0]*rgb_img.shape[1]):.2f}%)")
    print(f"Min edge value:    {np.min(results['edges'])}")
    print(f"Max edge value:    {np.max(results['edges'])}")
    print(f"Mean edge value:   {np.mean(results['edges']):.2f}")
    print("="*70)
    
    print("\nTest data generation complete!")
    print("\nTo run Verilog testbench:")
    print("  cd ../sim")
    print("  iverilog -g2012 -o sim_complete tb_sobel_complete_pipeline.sv ../verilog/sobel/*.v")
    print("  vvp sim_complete")

if __name__ == "__main__":
    main()
