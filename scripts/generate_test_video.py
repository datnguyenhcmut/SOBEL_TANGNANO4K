"""
Generate simple test video for Tang Nano 4K Binarization Testing
Creates a 640x480 video with various test patterns to verify edge detection

Requirements:
    pip install opencv-python numpy

Usage:
    python generate_test_video.py
    
Output:
    test_video_simple.mp4 - Simple test patterns
"""

import cv2
import numpy as np

# Video parameters
WIDTH = 640
HEIGHT = 480
FPS = 30
DURATION = 10  # seconds

# Create video writer
fourcc = cv2.VideoCC('mp4v')
out = cv2.VideoWriter('../data/test_video_simple.mp4', fourcc, FPS, (WIDTH, HEIGHT))

print("Generating test video for Tang Nano 4K...")
print(f"Resolution: {WIDTH}x{HEIGHT}")
print(f"Duration: {DURATION}s @ {FPS} fps")

total_frames = FPS * DURATION

for frame_num in range(total_frames):
    # Create blank frame
    frame = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    
    # Time in seconds
    t = frame_num / FPS
    
    # =========================================================================
    # SECTION 1: Blank screen (0-1s) - Test NO edges
    # =========================================================================
    if t < 1.0:
        frame[:] = (200, 200, 200)  # Light gray
        cv2.putText(frame, "TEST 1: BLANK", (200, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, "Expected: ~0% edges", (180, 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    # =========================================================================
    # SECTION 2: Simple rectangle (1-3s) - Test clear edges
    # =========================================================================
    elif t < 3.0:
        frame[:] = (200, 200, 200)  # Background
        # Draw rectangle
        cv2.rectangle(frame, (150, 100), (490, 380), (50, 50, 50), -1)
        cv2.putText(frame, "TEST 2: RECTANGLE", (170, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, "Expected: 4 clear edges", (160, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    # =========================================================================
    # SECTION 3: Moving circle (3-5s) - Test dynamic edges
    # =========================================================================
    elif t < 5.0:
        frame[:] = (220, 220, 220)
        # Moving circle
        x = int(150 + (t - 3.0) * 100)
        y = 240
        cv2.circle(frame, (x, y), 60, (30, 30, 30), -1)
        cv2.putText(frame, "TEST 3: MOVING CIRCLE", (150, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, "Expected: Circular edge following", (120, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    # =========================================================================
    # SECTION 4: Multiple objects (5-7s) - Test multiple edges
    # =========================================================================
    elif t < 7.0:
        frame[:] = (210, 210, 210)
        # Multiple rectangles
        cv2.rectangle(frame, (50, 50), (200, 200), (40, 40, 40), -1)
        cv2.rectangle(frame, (250, 100), (400, 250), (60, 60, 60), -1)
        cv2.rectangle(frame, (450, 50), (600, 200), (80, 80, 80), -1)
        cv2.rectangle(frame, (150, 280), (490, 430), (100, 100, 100), -1)
        cv2.putText(frame, "TEST 4: MULTIPLE OBJECTS", (130, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, "Expected: ~15-20% edges", (160, 465), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    # =========================================================================
    # SECTION 5: Gradient (7-8s) - Test weak edges
    # =========================================================================
    elif t < 8.0:
        # Horizontal gradient
        for x in range(WIDTH):
            color = int(255 * x / WIDTH)
            frame[:, x] = (color, color, color)
        cv2.putText(frame, "TEST 5: GRADIENT", (180, 240), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 3)
        cv2.putText(frame, "Expected: Weak/no edges", (160, 280), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    
    # =========================================================================
    # SECTION 6: High contrast (8-9s) - Test strong edges
    # =========================================================================
    elif t < 9.0:
        frame[:] = (255, 255, 255)  # White background
        # Black rectangles (high contrast)
        cv2.rectangle(frame, (100, 80), (250, 200), (0, 0, 0), -1)
        cv2.rectangle(frame, (300, 150), (540, 400), (0, 0, 0), -1)
        cv2.putText(frame, "TEST 6: HIGH CONTRAST", (140, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.putText(frame, "Expected: Strong edges (LED1=ON)", (100, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 1)
    
    # =========================================================================
    # SECTION 7: Text test (9-10s) - Test complex edges
    # =========================================================================
    else:
        frame[:] = (200, 200, 200)
        cv2.putText(frame, "TANG NANO 4K", (120, 150), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.putText(frame, "SOBEL TEST", (150, 250), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)
        cv2.putText(frame, "TEST 7: TEXT EDGES", (160, 350), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (50, 50, 50), 2)
        cv2.putText(frame, "Expected: Character outlines", (140, 450), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 1)
    
    # Write frame
    out.write(frame)
    
    # Progress
    if frame_num % 30 == 0:
        print(f"Progress: {frame_num}/{total_frames} frames ({t:.1f}s)")

# Release video
out.release()

print("\n✓ Video generated successfully!")
print("File: ../data/test_video_simple.mp4")
print("\nTest sequence:")
print("  0-1s: Blank screen (expect ~0% edges)")
print("  1-3s: Rectangle (expect 4 clear edges)")
print("  3-5s: Moving circle (expect circular edge)")
print("  5-7s: Multiple objects (expect 15-20% edges)")
print("  7-8s: Gradient (expect weak edges)")
print("  8-9s: High contrast (expect strong edges, LED1=ON)")
print("  9-10s: Text (expect character outlines)")
print("\nHow to use:")
print("1. Play video on PC monitor")
print("2. Point Tang Nano 4K camera at screen")
print("3. Observe VGA output")
print("4. Compare with expected results")
