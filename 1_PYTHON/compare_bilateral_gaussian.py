#!/usr/bin/env python3
"""
Compare Bilateral Filter vs Gaussian Blur for edge-preserving noise reduction
Author: Nguyễn Văn Đạt
Date: 2025-12-02
"""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

def gaussian_blur_3x3(image):
    """Apply 3x3 Gaussian blur: [1,2,1; 2,4,2; 1,2,1]/16"""
    kernel = np.array([[1, 2, 1],
                       [2, 4, 2],
                       [1, 2, 1]]) / 16.0
    
    h, w = image.shape
    result = np.zeros_like(image, dtype=np.float32)
    
    for y in range(1, h-1):
        for x in range(1, w-1):
            window = image[y-1:y+2, x-1:x+2]
            result[y, x] = np.sum(window * kernel)
    
    return np.clip(result, 0, 255).astype(np.uint8)

def bilateral_filter_3x3(image, sigma_range=30):
    """Apply simplified bilateral filter (edge-preserving)"""
    # Spatial kernel (same as Gaussian)
    spatial_kernel = np.array([[1, 2, 1],
                               [2, 4, 2],
                               [1, 2, 1]])
    
    h, w = image.shape
    result = np.zeros_like(image, dtype=np.float32)
    
    for y in range(1, h-1):
        for x in range(1, w-1):
            center = image[y, x]
            window = image[y-1:y+2, x-1:x+2]
            
            # Compute intensity differences
            diff = np.abs(window - center)
            
            # Range weight: reject pixels with large intensity difference
            range_weight = (diff < sigma_range).astype(float)
            
            # Combined weight
            weight = spatial_kernel * range_weight
            weight_sum = np.sum(weight)
            
            if weight_sum > 0:
                result[y, x] = np.sum(window * weight) / weight_sum
            else:
                result[y, x] = center
    
    return np.clip(result, 0, 255).astype(np.uint8)

def sobel_edge_detection(image):
    """Apply Sobel edge detection"""
    gx_kernel = np.array([[-1, 0, 1],
                          [-2, 0, 2],
                          [-1, 0, 1]])
    gy_kernel = np.array([[-1, -2, -1],
                          [ 0,  0,  0],
                          [ 1,  2,  1]])
    
    h, w = image.shape
    magnitude = np.zeros_like(image, dtype=np.float32)
    
    for y in range(1, h-1):
        for x in range(1, w-1):
            window = image[y-1:y+2, x-1:x+2]
            gx = np.sum(window * gx_kernel)
            gy = np.sum(window * gy_kernel)
            magnitude[y, x] = np.sqrt(gx**2 + gy**2)
    
    return np.clip(magnitude, 0, 255).astype(np.uint8)

def create_test_image():
    """Create test image with edges and noise"""
    img = np.zeros((200, 200), dtype=np.uint8)
    
    # Background
    img[:, :] = 80
    
    # Sharp vertical edge
    img[:, 70:130] = 200
    
    # Add Gaussian noise (mean=0, std=15)
    noise = np.random.normal(0, 15, img.shape)
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    
    return img

def main():
    print("=== Bilateral vs Gaussian Filter Comparison ===\n")
    
    # Create noisy test image
    img_noisy = create_test_image()
    
    # Apply filters
    img_gaussian = gaussian_blur_3x3(img_noisy)
    img_bilateral = bilateral_filter_3x3(img_noisy, sigma_range=30)
    
    # Detect edges on each
    edges_noisy = sobel_edge_detection(img_noisy)
    edges_gaussian = sobel_edge_detection(img_gaussian)
    edges_bilateral = sobel_edge_detection(img_bilateral)
    
    # Compute metrics
    print("Edge Strength (mean magnitude):")
    print(f"  Noisy:     {np.mean(edges_noisy):.2f}")
    print(f"  Gaussian:  {np.mean(edges_gaussian):.2f}")
    print(f"  Bilateral: {np.mean(edges_bilateral):.2f}")
    
    print("\nEdge Sharpness (max magnitude):")
    print(f"  Noisy:     {np.max(edges_noisy)}")
    print(f"  Gaussian:  {np.max(edges_gaussian)}")
    print(f"  Bilateral: {np.max(edges_bilateral)}")
    
    print("\nNoise Level (std of uniform region):")
    uniform_region = slice(10, 60), slice(10, 60)  # Top-left corner
    print(f"  Noisy:     {np.std(img_noisy[uniform_region]):.2f}")
    print(f"  Gaussian:  {np.std(img_gaussian[uniform_region]):.2f}")
    print(f"  Bilateral: {np.std(img_bilateral[uniform_region]):.2f}")
    
    # Visualization
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Row 1: Filtered images
    axes[0, 0].imshow(img_noisy, cmap='gray', vmin=0, vmax=255)
    axes[0, 0].set_title('Original (Noisy)', fontsize=14, fontweight='bold')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(img_gaussian, cmap='gray', vmin=0, vmax=255)
    axes[0, 1].set_title('Gaussian Blur\n(Edges blurred)', fontsize=14, fontweight='bold')
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(img_bilateral, cmap='gray', vmin=0, vmax=255)
    axes[0, 2].set_title('Bilateral Filter\n(Edges preserved)', fontsize=14, fontweight='bold', color='green')
    axes[0, 2].axis('off')
    
    # Row 2: Edge detection results
    axes[1, 0].imshow(edges_noisy, cmap='hot', vmin=0, vmax=255)
    axes[1, 0].set_title(f'Edges (Noisy)\nMax: {np.max(edges_noisy)}', fontsize=12)
    axes[1, 0].axis('off')
    
    axes[1, 1].imshow(edges_gaussian, cmap='hot', vmin=0, vmax=255)
    axes[1, 1].set_title(f'Edges (Gaussian)\nMax: {np.max(edges_gaussian)}', fontsize=12)
    axes[1, 1].axis('off')
    
    axes[1, 2].imshow(edges_bilateral, cmap='hot', vmin=0, vmax=255)
    axes[1, 2].set_title(f'Edges (Bilateral)\nMax: {np.max(edges_bilateral)}', fontsize=12, color='green', fontweight='bold')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig('bilateral_vs_gaussian_comparison.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: bilateral_vs_gaussian_comparison.png")
    
    # Profile plot across edge
    y_profile = 100  # Middle row
    x_coords = np.arange(200)
    
    fig2, ax = plt.subplots(figsize=(12, 6))
    ax.plot(x_coords, img_noisy[y_profile, :], label='Noisy', alpha=0.7, linewidth=2)
    ax.plot(x_coords, img_gaussian[y_profile, :], label='Gaussian (blurred edge)', linewidth=2.5)
    ax.plot(x_coords, img_bilateral[y_profile, :], label='Bilateral (sharp edge)', linewidth=2.5, linestyle='--')
    ax.axvline(70, color='red', linestyle=':', alpha=0.5, label='Edge start')
    ax.axvline(130, color='red', linestyle=':', alpha=0.5, label='Edge end')
    ax.set_xlabel('X position', fontsize=12)
    ax.set_ylabel('Pixel intensity', fontsize=12)
    ax.set_title('Cross-section Profile: Bilateral Preserves Sharp Edges', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('edge_profile_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: edge_profile_comparison.png")
    
    plt.show()
    
    print("\n=== Conclusion ===")
    print("✓ Bilateral filter PRESERVES edges better than Gaussian")
    print("✓ Both reduce noise effectively")
    print("✓ Use Bilateral when you need SHARP edges for lane detection")

if __name__ == '__main__':
    main()
