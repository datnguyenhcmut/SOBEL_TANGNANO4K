"""
Test Hough Transform implementation
Validates the voting and peak detection logic
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

def create_test_line_image(width=640, height=480, angle_deg=45, offset=0):
    """Create binary image with a single line"""
    img = np.zeros((height, width), dtype=np.uint8)
    
    # Convert angle to radians
    angle_rad = np.radians(angle_deg)
    
    # Draw line with given angle through center
    center_x, center_y = width // 2, height // 2
    
    for y in range(height):
        for x in range(width):
            # Calculate distance from line
            # Line equation: x*cos(θ) + y*sin(θ) = ρ
            rho_expected = center_x * np.cos(angle_rad) + center_y * np.sin(angle_rad) + offset
            rho_actual = x * np.cos(angle_rad) + y * np.sin(angle_rad)
            
            if abs(rho_actual - rho_expected) < 2:
                img[y, x] = 255
    
    return img

def hough_transform_python(edges, rho_resolution=2, theta_steps=90):
    """Python implementation matching hough_transform.v logic"""
    height, width = edges.shape
    
    # Compute lookup tables (Q8.8 fixed point, theta in 2° steps)
    cos_lut = []
    sin_lut = []
    for i in range(theta_steps):
        angle_deg = i * 2  # 0°, 2°, 4°, ..., 178°
        angle_rad = np.radians(angle_deg)
        cos_lut.append(int(np.cos(angle_rad) * 256))
        sin_lut.append(int(np.sin(angle_rad) * 256))
    
    # Calculate accumulator size
    max_rho = (width + height) // rho_resolution
    accumulator = np.zeros((max_rho, theta_steps), dtype=np.int32)
    
    # Voting phase
    edge_pixels = np.argwhere(edges > 0)
    print(f"Processing {len(edge_pixels)} edge pixels...")
    
    for pixel_y, pixel_x in edge_pixels:
        # Vote for all theta angles
        for theta_idx in range(theta_steps):
            # Calculate ρ = x·cos(θ) + y·sin(θ) using fixed point
            rho_temp = (pixel_x * cos_lut[theta_idx] + pixel_y * sin_lut[theta_idx]) >> 8
            
            # Convert to bin index
            if rho_temp >= 0:
                rho_bin = rho_temp // rho_resolution
            else:
                rho_bin = (max_rho // 2) - ((-rho_temp) // rho_resolution)
            
            # Increment vote
            if 0 <= rho_bin < max_rho:
                accumulator[rho_bin, theta_idx] += 1
    
    return accumulator, cos_lut, sin_lut

def find_peak(accumulator, min_votes=50):
    """Find maximum peak in accumulator"""
    max_votes = np.max(accumulator)
    max_pos = np.unravel_index(np.argmax(accumulator), accumulator.shape)
    
    if max_votes >= min_votes:
        rho_bin, theta_idx = max_pos
        return {
            'valid': True,
            'rho_bin': rho_bin,
            'theta_idx': theta_idx,
            'votes': max_votes,
            'theta_deg': theta_idx * 2
        }
    else:
        return {'valid': False}

def visualize_hough(edges, accumulator, peak_result, rho_resolution=2):
    """Visualize Hough transform results"""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    # Original edges
    axes[0].imshow(edges, cmap='gray')
    axes[0].set_title('Input Edge Image')
    axes[0].axis('off')
    
    # Hough space (accumulator)
    axes[1].imshow(accumulator, cmap='hot', aspect='auto')
    axes[1].set_title('Hough Space (Accumulator)')
    axes[1].set_xlabel('Theta Index (0-89, step 2°)')
    axes[1].set_ylabel('Rho Bin')
    
    # Mark peak
    if peak_result['valid']:
        axes[1].plot(peak_result['theta_idx'], peak_result['rho_bin'], 
                    'cx', markersize=15, markeredgewidth=3)
        axes[1].text(peak_result['theta_idx'], peak_result['rho_bin'] - 10,
                    f"Peak: {peak_result['votes']} votes", 
                    color='cyan', fontsize=10, ha='center')
    
    # Detected line overlay
    axes[2].imshow(edges, cmap='gray')
    if peak_result['valid']:
        # Draw detected line
        theta_deg = peak_result['theta_deg']
        theta_rad = np.radians(theta_deg)
        rho = peak_result['rho_bin'] * rho_resolution
        
        # Draw line using parametric form
        height, width = edges.shape
        if abs(np.sin(theta_rad)) > 0.001:
            x = np.arange(width)
            y = (rho - x * np.cos(theta_rad)) / np.sin(theta_rad)
            valid = (y >= 0) & (y < height)
            axes[2].plot(x[valid], y[valid], 'r-', linewidth=3, label='Detected Line')
        else:
            # Vertical line
            x = rho / np.cos(theta_rad) if abs(np.cos(theta_rad)) > 0.001 else width // 2
            axes[2].axvline(x=x, color='r', linewidth=3, label='Detected Line')
        
        axes[2].set_title(f'Detection: θ={theta_deg}°, ρ={rho}, votes={peak_result["votes"]}')
        axes[2].legend()
    else:
        axes[2].set_title('No line detected')
    axes[2].axis('off')
    
    plt.tight_layout()
    plt.savefig('hough_transform_test.png', dpi=150, bbox_inches='tight')
    print("Saved: hough_transform_test.png")
    plt.show()

def test_hough_multiple_angles():
    """Test with multiple line angles"""
    test_angles = [0, 30, 45, 60, 90, 120, 150]
    
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    axes = axes.flatten()
    
    for idx, angle in enumerate(test_angles):
        print(f"\n{'='*50}")
        print(f"Testing angle: {angle}°")
        print('='*50)
        
        # Create test image
        edges = create_test_line_image(angle_deg=angle)
        
        # Run Hough transform
        accumulator, _, _ = hough_transform_python(edges)
        
        # Find peak
        peak = find_peak(accumulator, min_votes=30)
        
        # Visualize
        axes[idx].imshow(edges, cmap='gray')
        axes[idx].set_title(f'Input: {angle}°\nDetected: {peak["theta_deg"]}°' if peak['valid'] else f'Input: {angle}°\nNot detected')
        axes[idx].axis('off')
        
        print(f"Expected: {angle}°")
        print(f"Detected: {peak['theta_deg']}°" if peak['valid'] else "Not detected")
        print(f"Votes: {peak.get('votes', 0)}")
    
    axes[-1].axis('off')
    
    plt.tight_layout()
    plt.savefig('hough_multiple_angles_test.png', dpi=150, bbox_inches='tight')
    print("\n\nSaved: hough_multiple_angles_test.png")
    plt.show()

def main():
    print("="*70)
    print("HOUGH TRANSFORM VALIDATION TEST")
    print("="*70)
    
    # Test 1: Single line at 45°
    print("\nTest 1: Line at 45 degrees")
    print("-"*70)
    edges = create_test_line_image(angle_deg=45)
    
    print("Running Hough Transform...")
    accumulator, cos_lut, sin_lut = hough_transform_python(edges)
    
    print(f"Accumulator shape: {accumulator.shape}")
    print(f"Max votes: {np.max(accumulator)}")
    
    print("\nFinding peaks...")
    peak = find_peak(accumulator, min_votes=50)
    
    if peak['valid']:
        print(f"✓ Line detected!")
        print(f"  Theta: {peak['theta_deg']}° (index {peak['theta_idx']})")
        print(f"  Rho bin: {peak['rho_bin']}")
        print(f"  Votes: {peak['votes']}")
    else:
        print("✗ No line detected")
    
    visualize_hough(edges, accumulator, peak)
    
    # Test 2: Multiple angles
    print("\n" + "="*70)
    print("Test 2: Multiple angles")
    print("="*70)
    test_hough_multiple_angles()

if __name__ == "__main__":
    main()
