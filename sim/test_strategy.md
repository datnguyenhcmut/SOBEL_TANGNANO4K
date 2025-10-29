# Sobel Module Testing Strategy
# Test individual modules trước khi integrate

## Modules cần test:

### 1. RGB to Grayscale ✅
- **File**: `src/sobel/rgb_to_gray.v`  
- **Status**: Complete implementation
- **Test**: RGB565 input → 8-bit grayscale output
- **Test cases**: 
  - Pure colors (R=31, G=0, B=0)
  - Grayscale values
  - Mixed colors

### 2. Line Buffer ✅  
- **File**: `src/sobel/line_buffer.v`
- **Status**: Complete implementation
- **Test**: 3-line circular buffer + 3x3 window extraction
- **Test cases**:
  - Sequential pixel input
  - Window boundary conditions
  - Frame sync behavior

### 3. Sobel Kernel ✅
- **File**: `src/sobel/sobel_kernel.v` 
- **Status**: Complete implementation
- **Test**: 3x3 convolution với Gx/Gy kernels
- **Test cases**:
  - Known edge patterns
  - Gradients validation
  - Signed arithmetic

### 4. Edge Magnitude 📝
- **File**: `src/sobel/edge_magnitude.v`
- **Status**: Need completion
- **Test**: |Gx| + |Gy| calculation
- **Test cases**: 
  - Various Gx/Gy combinations
  - Saturation behavior

### 5. Top Processor 📝
- **File**: `src/sobel/sobel_processor.v`
- **Status**: Need completion  
- **Test**: Full pipeline integration
- **Test cases**:
  - End-to-end processing
  - Timing verification

## Test Approach:

### Phase A: Individual Module Tests (Current)
```
RGB → Gray ✓
Line Buffer ✓  
Sobel Kernel ✓
Edge Magnitude (next)
```

### Phase B: Integration Tests
```
Gray → Line Buffer → Kernel → Magnitude
Full pipeline validation
```

### Phase C: System Integration
```
Camera Interface → Sobel Pipeline → Video Output
Real-world testing
```

## Quick Validation Method:

Thay vì tạo full testbenches, tôi sẽ tạo một **simple validation script** để check:

1. **Syntax errors** (compilation)
2. **Basic functionality** (simple stimulus)  
3. **Resource utilization** (synthesis report)

Ready for next step?