"""
Test lane detector logic with simulated road images
Creates test images and shows expected lane detection results
"""

import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

def create_road_image(width=640, height=480):
    """Create synthetic road image with lane markings"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Gray road surface
    img[height//2:, :] = [80, 80, 80]  # Road
    img[:height//2, :] = [135, 206, 235]  # Sky
    
    # Add some texture/noise to road
    noise = np.random.randint(-20, 20, (height//2, width, 3))
    img[height//2:, :] = np.clip(img[height//2:, :] + noise, 0, 255)
    
    return img

def draw_lane_lines(img, left_x_bot=200, right_x_bot=440, vanishing_y=240):
    """Draw lane lines on image"""
    height, width = img.shape[:2]
    
    # Vanishing point (center top of ROI)
    vanish_x = width // 2
    
    # Left lane line (yellow)
    pts_left = [
        (left_x_bot, height - 20),      # Bottom
        (vanish_x - 30, vanishing_y)    # Top (near vanishing point)
    ]
    
    # Right lane line (white)
    pts_right = [
        (right_x_bot, height - 20),     # Bottom
        (vanish_x + 30, vanishing_y)    # Top (near vanishing point)
    ]
    
    # Draw on PIL image for better line drawing
    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    
    # Left lane (yellow, dashed)
    draw.line(pts_left, fill=(255, 255, 0), width=8)
    
    # Right lane (white, solid)
    draw.line(pts_right, fill=(255, 255, 255), width=8)
    
    return np.array(pil_img)

def rgb_to_gray(img):
    """Convert RGB to grayscale"""
    return np.dot(img[...,:3], [0.299, 0.587, 0.114]).astype(np.uint8)

def simple_edge_detect(gray):
    """Simple edge detection (Sobel-like)"""
    from scipy import ndimage
    
    # Sobel operators
    sobel_x = ndimage.sobel(gray, axis=1)
    sobel_y = ndimage.sobel(gray, axis=0)
    
    # Magnitude
    magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
    
    # Threshold
    threshold = 30
    edges = (magnitude > threshold).astype(np.uint8) * 255
    
    return edges

def detect_lanes(edges, roi_top=240, roi_bottom=460):
    """Simulate lane_detector.v logic"""
    height, width = edges.shape
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
    
    # Accumulate edge pixels
    for y in range(roi_top, roi_bottom):
        for x in range(width):
            if edges[y, x] > 0:  # Edge pixel
                # Left region
                if x < middle_x:
                    if y < mid_y:  # Top half
                        left_acc_top += 1
                        left_x_sum_top += x
                    else:  # Bottom half
                        left_acc_bottom += 1
                        left_x_sum_bottom += x
                # Right region
                else:
                    if y < mid_y:
                        right_acc_top += 1
                        right_x_sum_top += x
                    else:
                        right_acc_bottom += 1
                        right_x_sum_bottom += x
    
    # Calculate lane positions
    left_valid = left_acc_top > 3
    right_valid = right_acc_top > 3
    
    if left_valid:
        left_x_top = left_x_sum_top // left_acc_top if left_acc_top > 0 else 0
        left_x_bottom = left_x_sum_bottom // left_acc_bottom if left_acc_bottom > 0 else 0
    else:
        left_x_top = 0
        left_x_bottom = 0
    
    if right_valid:
        right_x_top = right_x_sum_top // right_acc_top if right_acc_top > 0 else 0
        right_x_bottom = right_x_sum_bottom // right_acc_bottom if right_acc_bottom > 0 else 0
    else:
        right_x_top = 0
        right_x_bottom = 0
    
    return {
        'left_valid': left_valid,
        'left_x_top': left_x_top,
        'left_x_bottom': left_x_bottom,
        'right_valid': right_valid,
        'right_x_top': right_x_top,
        'right_x_bottom': right_x_bottom,
        'left_count': left_acc_top + left_acc_bottom,
        'right_count': right_acc_top + right_acc_bottom
    }

def visualize_results(original, edges, detection_result, roi_top=240, roi_bottom=460):
    """Visualize lane detection results"""
    height, width = original.shape[:2]
    
    # Create output image
    output = original.copy()
    
    # Draw ROI boundaries (blue)
    output[roi_top, :] = [0, 0, 255]
    output[roi_bottom, :] = [0, 0, 255]
    output[roi_top:roi_bottom, width//2] = [255, 255, 0]  # Yellow middle
    
    # Draw detected lanes
    if detection_result['left_valid']:
        x_top = detection_result['left_x_top']
        # Draw vertical line at detected X (RED)
        if 0 <= x_top < width:
            output[roi_top:roi_bottom, max(0, x_top-3):min(width, x_top+4)] = [255, 0, 0]
    
    if detection_result['right_valid']:
        x_top = detection_result['right_x_top']
        # Draw vertical line at detected X (GREEN)
        if 0 <= x_top < width:
            output[roi_top:roi_bottom, max(0, x_top-3):min(width, x_top+4)] = [0, 255, 0]
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Original with lane lines
    axes[0, 0].imshow(original)
    axes[0, 0].set_title('Original Road Image')
    axes[0, 0].axis('off')
    
    # Gray + edges
    axes[0, 1].imshow(edges, cmap='gray')
    axes[0, 1].set_title('Edge Detection')
    axes[0, 1].axhline(y=roi_top, color='blue', linestyle='--', linewidth=1)
    axes[0, 1].axhline(y=roi_bottom, color='blue', linestyle='--', linewidth=1)
    axes[0, 1].axvline(x=width//2, color='yellow', linestyle='--', linewidth=1)
    axes[0, 1].axis('off')
    
    # Detection result
    axes[1, 0].imshow(output)
    axes[1, 0].set_title('Lane Detection Result')
    axes[1, 0].axis('off')
    
    # Statistics
    stats_text = f"""Lane Detection Statistics:
    
Left Lane:
  Valid: {detection_result['left_valid']}
  X_top: {detection_result['left_x_top']}
  X_bottom: {detection_result['left_x_bottom']}
  Edge count: {detection_result['left_count']}

Right Lane:
  Valid: {detection_result['right_valid']}
  X_top: {detection_result['right_x_top']}
  X_bottom: {detection_result['right_x_bottom']}
  Edge count: {detection_result['right_count']}

ROI: Y={roi_top} to Y={roi_bottom}
Middle: X={width//2}
"""
    
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
                    verticalalignment='center')
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig('lane_detector_test.png', dpi=150, bbox_inches='tight')
    print(f"Saved: lane_detector_test.png")
    plt.show()

def main():
    print("Creating synthetic road image...")
    
    # Create road image
    road_img = create_road_image()
    
    # Add lane lines
    road_with_lanes = draw_lane_lines(road_img)
    
    # Convert to grayscale
    gray = rgb_to_gray(road_with_lanes)
    
    # Edge detection
    edges = simple_edge_detect(gray)
    
    print("Running lane detection algorithm...")
    # Detect lanes
    result = detect_lanes(edges)
    
    print("\nDetection Results:")
    print(f"  Left lane valid: {result['left_valid']}")
    print(f"  Left X: {result['left_x_top']}")
    print(f"  Right lane valid: {result['right_valid']}")
    print(f"  Right X: {result['right_x_top']}")
    
    # Visualize
    print("\nVisualizing results...")
    visualize_results(road_with_lanes, edges, result)

if __name__ == "__main__":
    main()
