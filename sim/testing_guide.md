# Sobel Module Testing Guide

## Issue với iverilog

iverilog không hỗ trợ đầy đủ SystemVerilog, đặc biệt là unpacked array ports:
```verilog
output wire [PIXEL_WIDTH-1:0] window_out [0:8]  // Lỗi với iverilog
```

Lỗi này xuất hiện trong `line_buffer.v` line 16.

## Giải pháp: Sử dụng Gowin EDA Simulator

Tang Nano 4K sử dụng Gowin FPGA nên tốt nhất là test với công cụ của Gowin:

### Bước 1: Tạo Project Simulation trong Gowin EDA

1. Mở **Gowin FPGA Designer**
2. File → New → FPGA Design Project
3. Chọn device: **GW1NSR-LV4C** (Tang Nano 4K)
4. Đặt tên project: `sobel_test`

### Bước 2: Add Files

Add tất cả Sobel modules:
- `verilog/sobel/rgb_to_gray.v`
- `verilog/sobel/line_buffer.v`
- `verilog/sobel/sobel_kernel.v`
- `verilog/sobel/edge_magnitude.v`
- `verilog/sobel/sobel_processor.v`
- `sim/tb_sobel_processor.v`

### Bước 3: Run Simulation

1. Tools → Simulation → Run Behavioral Simulation
2. Hoặc click icon "Behavioral Simulation" trên toolbar
3. Xem waveform trong Gowin simulator window

### Bước 4: Analyze Waveforms

Check các signals:
- `pixel_in` - Input RGB565 data
- `pixel_out` - Output edge detected result
- `pixel_valid` - Output valid signal
- `sobel_enable` - Enable/bypass control

## Alternative: Refactor cho iverilog

Nếu muốn dùng iverilog, cần refactor `line_buffer.v`:

**Thay đổi output từ:**
```verilog
output wire [PIXEL_WIDTH-1:0] window_out [0:8]
```

**Thành packed array:**
```verilog
output wire [PIXEL_WIDTH*9-1:0] window_out_flat  // 72 bits cho 9 pixels
```

Sau đó trong `sobel_kernel.v` unpack lại:
```verilog
wire [7:0] window [0:8];
assign window[0] = window_in[7:0];
assign window[1] = window_in[15:8];
// ... tiếp tục cho 9 pixels
```

## Recommendation

**→ Sử dụng Gowin EDA Simulator** vì:
1. Native support cho Tang Nano 4K
2. Hỗ trợ đầy đủ SystemVerilog syntax
3. Sẽ dùng công cụ này cho synthesis sau này anyway
4. Không cần refactor code

## Next Steps

1. Test với Gowin EDA Simulator
2. Verify Sobel output với vertical edge pattern
3. Check bypass mode functionality
4. Nếu test OK → Integration với `video_top.v`
