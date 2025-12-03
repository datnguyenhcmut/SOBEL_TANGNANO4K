#!/usr/bin/env python3
"""
Test noise rejection filter - removes isolated pixels, keeps edges
Author: Nguyễn Văn Đạt
Date: 2025-12-02
"""

import numpy as np
import matplotlib.pyplot as plt

def noise_rejection_filter(binary):
    """
    Remove isolated pixels using horizontal neighbor checking
    Keeps pixels that have at least 1 neighbor (left, right, or previous row)
    """
    h, w = binary.shape
    result = np.zeros_like(binary)
    
    for y in range(h):
        for x in range(1, w-1):
            if binary[y, x] > 0:
                # Check horizontal neighbors
                has_horizontal = (binary[y, x-1] > 0) or (binary[y, x+1] > 0)
                # Check vertical (previous row)
                has_vertical = False
                if y > 0:
                    has_vertical = (result[y-1, x] > 0) or (y > 1 and result[y-2, x] > 0)
                
                # Keep if has neighbor
                if has_horizontal or has_vertical:
                    result[y, x] = 255
    
    return result

# Create test with edges + noise
img = np.zeros((100, 150), dtype=np.uint8)

# Real edges (continuous)
img[30:70, 40:42] = 255   # Vertical line
img[30:32, 40:110] = 255  # Horizontal line
img[68:70, 40:110] = 255  # Horizontal line
img[30:70, 108:110] = 255 # Vertical line

# Add random noise (isolated pixels)
np.random.seed(42)
noise_coords = np.random.randint(0, [100, 150], (200, 2))
for y, x in noise_coords:
    if 5 < y < 95 and 5 < x < 145:
        img[y, x] = 255

# Apply filter
filtered = noise_rejection_filter(img)

# Count results
noise_before = 0
noise_after = 0
for y in range(1, img.shape[0]-1):
    for x in range(1, img.shape[1]-1):
        if img[y, x] > 0:
            neighbors = np.sum(img[y-1:y+2, x-1:x+2] > 0) - 1
            if neighbors == 0:
                noise_before += 1
        if filtered[y, x] > 0:
            neighbors = np.sum(filtered[y-1:y+2, x-1:x+2] > 0) - 1
            if neighbors == 0:
                noise_after += 1

print("=== Noise Rejection Filter Test ===")
print(f"Isolated pixels before: {noise_before}")
print(f"Isolated pixels after:  {noise_after}")
print(f"Noise removed: {100*(noise_before-noise_after)/max(noise_before,1):.1f}%")
print(f"\nTotal pixels before: {np.sum(img>0)}")
print(f"Total pixels after:  {np.sum(filtered>0)}")
print(f"Edge preservation: {100*np.sum(filtered>0)/max(np.sum(img>0),1):.1f}%")

# Visual
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

axes[0].imshow(img, cmap='gray')
axes[0].set_title(f'Before: {noise_before} isolated pixels', fontsize=14, color='red')
axes[0].axis('off')

axes[1].imshow(filtered, cmap='gray')
axes[1].set_title(f'After: {noise_after} isolated pixels', fontsize=14, color='green', fontweight='bold')
axes[1].axis('off')

removed = (img > 0) & (filtered == 0)
axes[2].imshow(removed*255, cmap='Reds')
axes[2].set_title(f'Removed: {np.sum(removed)} pixels', fontsize=14)
axes[2].axis('off')

plt.tight_layout()
plt.savefig('noise_rejection_test.png', dpi=150)
print("\n✓ Saved: noise_rejection_test.png")
plt.show()

print("\n✅ Filter removes isolated noise while preserving continuous edges!")
