# Sobel Integration Plan - Camera HDMI Base
# Sử dụng camera_hdmi project làm base cho Sobel edge detection

## 📋 **Current Architecture Analysis**

### **Data Flow hiện tại:**
```
Camera OV2640 → RGB/RAW processing → Video Frame Buffer → HDMI Output
     ↓                ↓                        ↓              ↓
  PIXCLK/HREF     RGB565 format         HyperRAM memory    TMDS output
```

### **Key Components đã có:**
1. **Camera Interface**: OV2640 controller + I2C config
2. **Clock Management**: PLLs cho camera, processing, HDMI
3. **Memory Controller**: HyperRAM interface với video frame buffer
4. **HDMI Output**: DVI TX với TMDS encoding
5. **Test Pattern**: Có thể switch giữa camera và test pattern

### **Integration Points cho Sobel:**
- **Input**: Sau camera data, trước Video Frame Buffer
- **Processing**: Real-time trong pixel clock domain
- **Output**: Modified data vào Video Frame Buffer

## 🎯 **Sobel Integration Strategy**

### **Step 1: Analyze Current Pixel Pipeline**
```verilog
// Current path (video_top.v lines ~200):
PIXDATA[9:0] → cam_data[15:0] → ch0_vfb_data_in → Video_Frame_Buffer
```

### **Step 2: Insert Sobel Processing Module**
```verilog
// New path:
PIXDATA[9:0] → RGB/Grayscale → Sobel Filter → Video_Frame_Buffer → HDMI
```

### **Step 3: Module Design Requirements**

#### **Sobel Processor Module:**
```verilog
module sobel_processor (
    input               clk,           // PIXCLK domain
    input               rst_n,
    input               href,          // Horizontal reference 
    input               vsync,         // Vertical sync
    input      [15:0]   pixel_in,      // RGB565 input
    input               sobel_enable,  // Enable/bypass switch
    
    output              pixel_valid,   // Output valid
    output     [15:0]   pixel_out      // Processed output
);
```

#### **Features cần implement:**
1. **RGB565 → Grayscale conversion**
2. **3x3 Line buffer** (sử dụng Block RAM)
3. **Sobel kernels** (Gx, Gy)
4. **Edge magnitude** calculation
5. **Bypass mode** (switch giữa original và Sobel)

### **Step 4: Memory Requirements**
- **Line Buffers**: 3 lines × 640 pixels × 8 bits = 1920 bytes
- **Tang Nano 4K**: ~72Kb Block RAM → Đủ cho line buffers
- **Existing HyperRAM**: Giữ nguyên cho frame buffering

### **Step 5: Clock Domain Considerations**
- **PIXCLK**: Camera pixel clock (~25MHz cho VGA)
- **Processing**: Cùng domain với PIXCLK để avoid FIFO
- **HDMI**: Đã handle bởi Video Frame Buffer

### **Step 6: Control Interface**
- **Sobel Enable**: Sử dụng key input hoặc thêm switch
- **Threshold**: Fixed hoặc configurable
- **Mode**: Original/Sobel/Side-by-side

## 📁 **Implementation Plan**

### **Phase 1: Create Sobel Module**
```
src/sobel/
├── sobel_processor.v     # Top-level Sobel processor
├── rgb_to_gray.v        # RGB565 → Grayscale conversion
├── line_buffer.v        # 3-line circular buffer
├── sobel_kernel.v       # Sobel convolution engine
└── edge_magnitude.v     # Final magnitude calculation
```

### **Phase 2: Integrate with video_top.v**
1. **Add Sobel instance** between camera và Video Frame Buffer
2. **Wire control signals**
3. **Update clock domains** if needed
4. **Add bypass logic**

### **Phase 3: Constraints & Timing**
1. **Update dk_video.cst** cho any new I/O
2. **Timing constraints** trong dk_video.sdc
3. **Resource utilization** analysis

### **Phase 4: Testing & Validation**
1. **Simulation** với testbench
2. **Hardware testing** trên Tang Nano 4K
3. **Performance optimization**

## 🔧 **Technical Specifications**

### **Input Format**: RGB565 (từ cam_data)
```verilog
// RGB565 breakdown:
wire [4:0] red   = pixel_in[15:11];
wire [5:0] green = pixel_in[10:5]; 
wire [4:0] blue  = pixel_in[4:0];
```

### **Grayscale Conversion** (FPGA-optimized):
```verilog
// Approximation: Y = (R*77 + G*151 + B*28) >> 8
// Or simpler: Y = (R + G + B) / 3
```

### **Sobel Kernels** (từ Python analysis):
```verilog
Gx = [-1  0  1]    Gy = [-1 -2 -1]
     [-2  0  2]         [ 0  0  0]
     [-1  0  1]         [ 1  2  1]
```

### **Output Format**: RGB565 edge magnitude
```verilog
// Edge → grayscale → duplicate to RGB channels
assign pixel_out = {edge[7:3], edge[7:2], edge[7:3]};
```

## 🚀 **Next Steps**

1. **Create base Sobel modules** (Phase 1)
2. **Test individual modules** 
3. **Integrate với video_top.v** (Phase 2)
4. **Hardware validation**

**Ready to start Phase 1?**