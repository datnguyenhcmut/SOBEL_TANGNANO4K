"""
Test lane detector with stronger edges
"""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

def create_simple_lane_test():
    """Create very simple test case with clear vertical lines"""
    width, height = 640, 480
    
    # Black background
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Draw two white vertical lines as lanes
    left_x = 200
    right_x = 440
    
    # Make thick lines in ROI (Y=240 to 460)
    roi_top = 240
    roi_bottom = 460
    
    # Left lane (RED in output)
    img[roi_top:roi_bottom, left_x-5:left_x+5] = 255
    
    # Right lane (GREEN in output)
    img[roi_top:roi_bottom, right_x-5:right_x+5] = 255
    
    return img

def simulate_lane_detector(edges):
    """Exact implementation of lane_detector.v"""
    height, width = edges.shape
    roi_top = 240
    roi_bottom = 460
    middle_x = width // 2
    mid_y = (roi_top + roi_bottom) // 2
    
    # Accumulators
    left_acc_top = 0
    left_acc_bottom = 0
    left_x_sum_top = 0
    left_x_sum_bottom = 0
    
    right_acc_top = 0
    right_acc_bottom = 0
    right_x_sum_top = 0
    right_x_sum_bottom = 0
    
    # Process all pixels
    for y in range(height):
        for x in range(width):
            pixel_in = edges[y, x] > 0
            
            # Check ROI
            in_roi = (y >= roi_top) and (y <= roi_bottom)
            in_top_half = (y >= roi_top) and (y < mid_y)
            in_bottom_half = (y >= mid_y) and (y <= roi_bottom)
            
            if pixel_in and in_roi:
                # Left region
                if x < middle_x:
                    if in_top_half:
                        left_acc_top += 1
                        left_x_sum_top += x
                    elif in_bottom_half:
                        left_acc_bottom += 1
                        left_x_sum_bottom += x
                # Right region
                else:
                    if in_top_half:
                        right_acc_top += 1
                        right_x_sum_top += x
                    elif in_bottom_half:
                        right_acc_bottom += 1
                        right_x_sum_bottom += x
    
    # Calculate results
    left_valid = left_acc_top > 3
    right_valid = right_acc_top > 3
    
    result = {
        'left_valid': left_valid,
        'left_x_top': left_x_sum_top // left_acc_top if left_acc_top > 0 else 0,
        'left_x_bottom': left_x_sum_bottom // left_acc_bottom if left_acc_bottom > 0 else 0,
        'right_valid': right_valid,
        'right_x_top': right_x_sum_top // right_acc_top if right_acc_top > 0 else 0,
        'right_x_bottom': right_x_sum_bottom // right_acc_bottom if right_acc_bottom > 0 else 0,
        'left_acc_top': left_acc_top,
        'left_acc_bottom': left_acc_bottom,
        'right_acc_top': right_acc_top,
        'right_acc_bottom': right_acc_bottom
    }
    
    return result

def visualize_test(edges, result):
    """Visualize detection"""
    height, width = edges.shape
    roi_top = 240
    roi_bottom = 460
    
    # Create RGB output
    output = np.stack([edges, edges, edges], axis=2)
    
    # Draw ROI boundaries (blue)
    output[roi_top, :] = [0, 0, 255]
    output[roi_bottom, :] = [0, 0, 255]
    output[roi_top:roi_bottom, width//2] = [255, 255, 0]  # Yellow middle
    
    # Draw detected lanes
    if result['left_valid']:
        x = result['left_x_top']
        output[roi_top:roi_bottom, max(0,x-3):min(width,x+4)] = [255, 0, 0]  # RED
    
    if result['right_valid']:
        x = result['right_x_top']
        output[roi_top:roi_bottom, max(0,x-3):min(width,x+4)] = [0, 255, 0]  # GREEN
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    axes[0].imshow(edges, cmap='gray')
    axes[0].set_title('Input Edges')
    axes[0].axhline(y=roi_top, color='cyan', linestyle='--', linewidth=1)
    axes[0].axhline(y=roi_bottom, color='cyan', linestyle='--', linewidth=1)
    axes[0].axvline(x=width//2, color='yellow', linestyle='--', linewidth=1)
    
    axes[1].imshow(output)
    axes[1].set_title('Lane Detection Result')
    
    # Add text
    info = f"""Detection Results:

LEFT LANE:
  Valid: {result['left_valid']}
  X_top: {result['left_x_top']}
  X_bottom: {result['left_x_bottom']}
  Acc_top: {result['left_acc_top']}
  Acc_bottom: {result['left_acc_bottom']}

RIGHT LANE:
  Valid: {result['right_valid']}
  X_top: {result['right_x_top']}
  X_bottom: {result['right_x_bottom']}
  Acc_top: {result['right_acc_top']}
  Acc_bottom: {result['right_acc_bottom']}
"""
    
    plt.figtext(0.5, 0.01, info, ha='center', fontsize=10, family='monospace',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig('lane_detector_simple_test.png', dpi=150, bbox_inches='tight')
    print("Saved: lane_detector_simple_test.png")
    plt.show()

def main():
    print("Creating simple test image with vertical lines...")
    edges = create_simple_lane_test()
    edges_gray = edges[:, :, 0]  # Take one channel
    
    print("Running lane detector simulation...")
    result = simulate_lane_detector(edges_gray)
    
    print("\n" + "="*50)
    print("LANE DETECTION RESULTS:")
    print("="*50)
    print(f"Left lane:  Valid={result['left_valid']}, X={result['left_x_top']}, Count={result['left_acc_top']}")
    print(f"Right lane: Valid={result['right_valid']}, X={result['right_x_top']}, Count={result['right_acc_top']}")
    print("="*50)
    
    # Expected results
    print("\nExpected:")
    print(f"  Left lane at X ≈ 200 (actual: {result['left_x_top']})")
    print(f"  Right lane at X ≈ 440 (actual: {result['right_x_top']})")
    
    visualize_test(edges_gray, result)

if __name__ == "__main__":
    main()
