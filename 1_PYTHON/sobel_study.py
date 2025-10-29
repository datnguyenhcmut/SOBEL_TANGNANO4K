# Sobel Edge Detection - Python Implementation
# Mục đích: Hiểu thuật toán trước khi implement trên FPGA
# Tác giả: [Tên bạn]
# Ngày: October 2025

"""
Sobel Edge Detection Algorithm Study

1. Đọc và hiểu thuật toán Sobel
2. Implement trên Python với numpy/opencv
3. Test với various images
4. Analyze performance và optimize
5. Prepare cho FPGA implementation

Sobel Operator:
- Dùng để detect edges trong image
- Sử dụng 2 convolution kernels 3x3
- Tính gradient theo hướng X và Y
- Combine để có edge magnitude
"""

import numpy as np
import cv2
import matplotlib.pyplot as plt
from typing import Tuple, Optional
import os

class SobelEdgeDetector:
    """
    Sobel Edge Detection Implementation
    
    Mục đích: Hiểu rõ thuật toán trước khi chuyển sang hardware
    """
    
    def __init__(self):
        # Sobel kernels
        self.sobel_x = np.array([[-1, 0, 1],
                                [-2, 0, 2], 
                                [-1, 0, 1]], dtype=np.float32)
        
        self.sobel_y = np.array([[-1, -2, -1],
                                [ 0,  0,  0],
                                [ 1,  2,  1]], dtype=np.float32)
    
    def rgb_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert RGB to Grayscale using luminosity method
        Formula: Y = 0.299*R + 0.587*G + 0.114*B
        
        Trong FPGA sẽ dùng approximation để tránh floating point:
        Y ≈ (R + G + B) / 3  hoặc
        Y ≈ (R*77 + G*151 + B*28) >> 8  (fixed point)
        """
        if len(image.shape) == 3:
            # Luminosity method (chuẩn)
            gray = 0.299 * image[:,:,0] + 0.587 * image[:,:,1] + 0.114 * image[:,:,2]
            return gray.astype(np.uint8)
        else:
            return image
    
    def rgb_to_grayscale_fpga_approx(self, image: np.ndarray) -> np.ndarray:
        """
        FPGA-friendly grayscale conversion (no floating point)
        Sử dụng bit shifts: Y = (R*77 + G*151 + B*28) >> 8
        """
        if len(image.shape) == 3:
            r = image[:,:,0].astype(np.uint16)
            g = image[:,:,1].astype(np.uint16) 
            b = image[:,:,2].astype(np.uint16)
            
            # Fixed point approximation
            gray = (r * 77 + g * 151 + b * 28) >> 8
            return gray.astype(np.uint8)
        else:
            return image
    
    def apply_sobel_manual(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Manual Sobel implementation (giống như sẽ làm trong FPGA)
        
        Returns:
            gx: Gradient X direction
            gy: Gradient Y direction  
            magnitude: Edge magnitude
        """
        gray = self.rgb_to_grayscale(image)
        
        # Padding for convolution
        padded = np.pad(gray, ((1, 1), (1, 1)), mode='edge')
        
        gx = np.zeros_like(gray, dtype=np.float32)
        gy = np.zeros_like(gray, dtype=np.float32)
        
        # Manual convolution (giống logic trong FPGA)
        for i in range(1, padded.shape[0] - 1):
            for j in range(1, padded.shape[1] - 1):
                # Extract 3x3 window
                window = padded[i-1:i+2, j-1:j+2]
                
                # Sobel X convolution
                gx[i-1, j-1] = np.sum(window * self.sobel_x)
                
                # Sobel Y convolution  
                gy[i-1, j-1] = np.sum(window * self.sobel_y)
        
        # Edge magnitude
        magnitude = np.sqrt(gx**2 + gy**2)
        
        # Normalize to 0-255
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)
        
        return gx, gy, magnitude
    
    def apply_sobel_fpga_style(self, image: np.ndarray) -> np.ndarray:
        """
        FPGA-style implementation:
        - No floating point
        - Approximation: |Gx| + |Gy| instead of sqrt(Gx² + Gy²)
        - Integer arithmetic only
        """
        gray = self.rgb_to_grayscale_fpga_approx(image)
        
        # Padding
        padded = np.pad(gray, ((1, 1), (1, 1)), mode='edge').astype(np.int16)
        
        magnitude = np.zeros_like(gray, dtype=np.uint16)
        
        # Manual convolution với integer arithmetic
        for i in range(1, padded.shape[0] - 1):
            for j in range(1, padded.shape[1] - 1):
                # 3x3 window
                w = padded[i-1:i+2, j-1:j+2]
                
                # Sobel X (integer)
                gx = (-w[0,0] + w[0,2] - 2*w[1,0] + 2*w[1,2] - w[2,0] + w[2,2])
                
                # Sobel Y (integer)
                gy = (-w[0,0] - 2*w[0,1] - w[0,2] + w[2,0] + 2*w[2,1] + w[2,2])
                
                # Magnitude approximation: |Gx| + |Gy|
                magnitude[i-1, j-1] = abs(gx) + abs(gy)
        
        # Saturation to 255
        magnitude = np.clip(magnitude, 0, 255).astype(np.uint8)
        
        return magnitude
    
    def compare_methods(self, image: np.ndarray):
        """
        So sánh các methods để validate FPGA approach
        """
        # OpenCV Sobel (reference)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        sobelx_cv = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobely_cv = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        sobel_cv = np.sqrt(sobelx_cv**2 + sobely_cv**2)
        sobel_cv = np.clip(sobel_cv, 0, 255).astype(np.uint8)
        
        # Manual implementation
        gx, gy, sobel_manual = self.apply_sobel_manual(image)
        
        # FPGA-style implementation  
        sobel_fpga = self.apply_sobel_fpga_style(image)
        
        return {
            'opencv': sobel_cv,
            'manual': sobel_manual, 
            'fpga_style': sobel_fpga,
            'original': gray
        }

def test_sobel_algorithm():
    """
    Test function để validate implementation
    """
    print("=== Sobel Edge Detection Algorithm Study ===")
    print("Mục đích: Hiểu thuật toán trước khi implement FPGA\n")
    
    # Tạo test detector
    detector = SobelEdgeDetector()
    
    # Test với synthetic image
    print("1. Testing với synthetic image...")
    test_img = create_test_image()
    
    results = detector.compare_methods(test_img)
    
    # Analyze results
    print("2. Analyzing results...")
    for method, result in results.items():
        if method != 'original':
            print(f"   {method}: shape={result.shape}, dtype={result.dtype}, range=[{result.min()}, {result.max()}]")
    
    # Save results for visualization
    save_results(results)
    
    print("3. Results saved to 'results/' folder")
    print("4. Next step: Analyze performance và optimize cho FPGA")

def create_test_image(size: Tuple[int, int] = (256, 256)) -> np.ndarray:
    """
    Tạo test image với edges rõ ràng để test algorithm
    """
    img = np.zeros((*size, 3), dtype=np.uint8)
    
    # Vertical edge
    img[:, size[1]//4:size[1]//2] = [255, 255, 255]
    
    # Horizontal edge  
    img[size[0]//4:size[0]//2, :] = [128, 128, 128]
    
    # Diagonal pattern
    for i in range(size[0]//2, 3*size[0]//4):
        for j in range(size[1]//2, 3*size[1]//4):
            if (i + j) % 40 < 20:
                img[i, j] = [200, 150, 100]
    
    return img

def save_results(results: dict):
    """
    Save results for analysis
    """
    os.makedirs("results", exist_ok=True)
    
    for method, img in results.items():
        filename = f"results/{method}_result.png"
        if method == 'original':
            cv2.imwrite(filename, img)
        else:
            cv2.imwrite(filename, img)
        print(f"   Saved: {filename}")

if __name__ == "__main__":
    test_sobel_algorithm()