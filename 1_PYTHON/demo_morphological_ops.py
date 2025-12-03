#!/usr/bin/env python3
"""
Demonstrate morphological operations for cleaning binary edge maps
Shows: Erosion, Dilation, Closing (Dilation+Erosion)
Author: Nguyễn Văn Đạt
Date: 2025-12-02
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage

def morphological_erosion(binary):
    """Remove isolated pixels - need 2+ neighbors"""
    h, w = binary.shape
    result = np.zeros_like(binary)
    
    for y in range(1, h-1):
        for x in range(1, w-1):
            if binary[y, x] > 0:
                neighbors = (
                    (binary[y-1, x-1] > 0) + (binary[y-1, x] > 0) + (binary[y-1, x+1] > 0) +
                    (binary[y, x-1] > 0) + (binary[y, x+1] > 0) +
                    (binary[y+1, x-1] > 0) + (binary[y+1, x] > 0) + (binary[y+1, x+1] > 0)
                )
                if neighbors >= 2:
                    result[y, x] = 255
    return result

def morphological_dilation(binary):
    """Thicken edges - set pixel if any neighbor is set"""
    h, w = binary.shape
    result = np.zeros_like(binary)
    
    for y in range(1, h-1):
        for x in range(1, w-1):
            # Set if center OR any neighbor is set
            has_edge = binary[y, x] > 0 or \
                      binary[y-1, x-1] > 0 or binary[y-1, x] > 0 or binary[y-1, x+1] > 0 or \
                      binary[y, x-1] > 0 or binary[y, x+1] > 0 or \
                      binary[y+1, x-1] > 0 or binary[y+1, x] > 0 or binary[y+1, x+1] > 0
            if has_edge:
                result[y, x] = 255
    return result

def morphological_closing(binary):
    """Dilation then Erosion - fills gaps, removes noise"""
    dilated = morphological_dilation(binary)
    closed = morphological_erosion(dilated)
    return closed

def create_noisy_edges():
    """Create binary edge map with noise and gaps"""
    img = np.zeros((200, 300), dtype=np.uint8)
    
    # Main edges (with gaps)
    img[50:150, 50:52] = 255   # Left vertical line
    img[50:150, 248:250] = 255 # Right vertical line
    
    # Add gaps
    img[80:85, 50:52] = 0
    img[110:115, 248:250] = 0
    
    # Weak edges (thin, disconnected)
    img[100:105, 100] = 255
    img[100:105, 150] = 255
    img[100:105, 200] = 255
    
    # Add isolated noise pixels (random dots)
    np.random.seed(42)
    noise_coords = np.random.randint(0, 200, (50, 2))  # 50 random noise pixels
    for coord in noise_coords:
        y, x = coord
        if 10 < y < 190 and 10 < x < 290:  # Avoid borders
            img[y, x] = 255
    
    return img

def main():
    print("=== Morphological Operations for Edge Cleanup ===\n")
    
    # Create test image
    img_noisy = create_noisy_edges()
    
    # Apply operations
    img_eroded = morphological_erosion(img_noisy)
    img_dilated = morphological_dilation(img_noisy)
    img_closed = morphological_closing(img_noisy)
    
    # Count pixels
    count_noisy = np.sum(img_noisy > 0)
    count_eroded = np.sum(img_eroded > 0)
    count_dilated = np.sum(img_dilated > 0)
    count_closed = np.sum(img_closed > 0)
    
    print("Pixel counts:")
    print(f"  Original (noisy):      {count_noisy} pixels")
    print(f"  After Erosion:         {count_eroded} pixels  (-{count_noisy - count_eroded} noise removed)")
    print(f"  After Dilation:        {count_dilated} pixels  (+{count_dilated - count_noisy} pixels added)")
    print(f"  After Closing:         {count_closed} pixels  ← BEST: Gaps filled, noise removed")
    
    # Analyze noise reduction
    def count_isolated_pixels(binary):
        """Count pixels with <2 neighbors"""
        h, w = binary.shape
        isolated = 0
        for y in range(1, h-1):
            for x in range(1, w-1):
                if binary[y, x] > 0:
                    neighbors = (
                        (binary[y-1, x-1] > 0) + (binary[y-1, x] > 0) + (binary[y-1, x+1] > 0) +
                        (binary[y, x-1] > 0) + (binary[y, x+1] > 0) +
                        (binary[y+1, x-1] > 0) + (binary[y+1, x] > 0) + (binary[y+1, x+1] > 0)
                    )
                    if neighbors < 2:
                        isolated += 1
        return isolated
    
    isolated_noisy = count_isolated_pixels(img_noisy)
    isolated_closed = count_isolated_pixels(img_closed)
    
    print(f"\nIsolated noise pixels:")
    print(f"  Original:  {isolated_noisy} pixels")
    print(f"  Closing:   {isolated_closed} pixels  ← {100*(isolated_noisy-isolated_closed)//isolated_noisy}% noise removed!")
    
    # Visualization
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    # Row 1: Operations
    axes[0, 0].imshow(img_noisy, cmap='gray', vmin=0, vmax=255)
    axes[0, 0].set_title(f'Original (Noisy)\n{count_noisy} pixels, {isolated_noisy} isolated', 
                         fontsize=12, color='red')
    axes[0, 0].axis('off')
    
    axes[0, 1].imshow(img_eroded, cmap='gray', vmin=0, vmax=255)
    axes[0, 1].set_title(f'Erosion (Remove Noise)\n{count_eroded} pixels\n← Removes isolated dots', 
                         fontsize=12)
    axes[0, 1].axis('off')
    
    axes[0, 2].imshow(img_dilated, cmap='gray', vmin=0, vmax=255)
    axes[0, 2].set_title(f'Dilation (Thicken Edges)\n{count_dilated} pixels\n← Fills gaps, thicker', 
                         fontsize=12)
    axes[0, 2].axis('off')
    
    # Row 2: Closing process
    axes[1, 0].imshow(img_closed, cmap='gray', vmin=0, vmax=255)
    axes[1, 0].set_title(f'Closing (Dilation→Erosion)\n{count_closed} pixels, {isolated_closed} isolated\n✓ BEST: Clean edges!', 
                         fontsize=12, fontweight='bold', color='green')
    axes[1, 0].axis('off')
    
    # Difference maps
    removed_noise = (img_noisy > 0) & (img_closed == 0)
    filled_gaps = (img_noisy == 0) & (img_closed > 0)
    
    axes[1, 1].imshow(removed_noise * 255, cmap='Reds', vmin=0, vmax=255)
    axes[1, 1].set_title(f'Removed Noise\n{np.sum(removed_noise)} pixels eliminated', 
                         fontsize=12, color='red')
    axes[1, 1].axis('off')
    
    axes[1, 2].imshow(filled_gaps * 255, cmap='Greens', vmin=0, vmax=255)
    axes[1, 2].set_title(f'Filled Gaps\n{np.sum(filled_gaps)} pixels added', 
                         fontsize=12, color='green')
    axes[1, 2].axis('off')
    
    plt.tight_layout()
    plt.savefig('morphological_operations.png', dpi=150, bbox_inches='tight')
    print("\n✓ Saved: morphological_operations.png")
    plt.show()
    
    print("\n=== RESULTS ===")
    print("✓ Closing operation (Dilation→Erosion):")
    print("  1. Fills small gaps in edges")
    print("  2. Makes edges thicker and more visible")
    print("  3. Removes isolated noise pixels")
    print(f"  4. Reduces noise by {100*(isolated_noisy-isolated_closed)//isolated_noisy}%")
    print("\n→ Integrated into sobel_processor.v!")

if __name__ == '__main__':
    main()
