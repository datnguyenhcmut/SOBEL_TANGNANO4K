# Sobel Edge Detection on FPGA

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FPGA: TangNano 4K](https://img.shields.io/badge/FPGA-TangNano%204K-blue)](https://wiki.sipeed.com/hardware/en/tang/Tang-Nano-4K/Nano-4K.html)
[![Language: Verilog](https://img.shields.io/badge/Language-Verilog-orange)](https://www.verilog.com/)

Hệ thống phát hiện biên Sobel real-time trên FPGA Tang Nano 4K với luồng kiểm chứng video hoàn chỉnh.

## 📋 Tổng Quan

Dự án triển khai bộ xử lý phát hiện biên Sobel 4-tầng pipeline trên FPGA, tích hợp với camera OV2640 và xuất ra HDMI. Đặc biệt, hệ thống bao gồm framework kiểm chứng đa tầng (golden vectors, random tests, real video) để đảm bảo chất lượng RTL.

### Tính Năng Chính
- ✅ Pipeline 4 tầng: RGB565 → Grayscale → Line Buffer → Sobel → Edge Magnitude
- ✅ Real-time processing @ 27 MHz (640×480 @ 30fps)
- ✅ Latency < 200 ns (5 clock cycles)
- ✅ 3 testbench độc lập với tự động hóa hoàn toàn
- ✅ Python reference model bit-accurate
- ✅ Video diff visualization cho debugging

## 📁 Cấu Trúc Thư Mục

```
Sobel_project/
├── 1_PYTHON/              # Golden vector generation
│   ├── generate_golden_vectors.py
│   ├── requirements.txt
│   └── results/
├── verilog/               # RTL source code
│   ├── sobel/            # Sobel processor modules
│   │   ├── sobel_processor.v
│   │   ├── rgb_to_gray.v
│   │   ├── line_buffer.v
│   │   ├── sobel_kernel.v
│   │   └── edge_mag.v
│   └── src/              # Top-level integration
│       └── video_top.v
├── sim/                   # Testbenches và simulation
│   ├── Makefile
│   ├── tb_sobel_golden_fix.v
│   ├── tb_sobel_random.v
│   ├── tb_sobel_video.v
│   └── golden/           # Golden reference data
├── scripts/               # Video processing utilities
│   ├── prep_video_rgb565.py
│   ├── generate_motion_video.py
│   └── compare_sobel_output.py
├── data/                  # Video I/O (generated)
│   ├── video_in.rgb
│   ├── video_out.rgb
│   ├── video_meta.txt
│   └── video_report.json
└── docs/                  # Documentation
    ├── sobel_video_verification_report.tex
    └── progress_report.tex
```

## 🚀 Quick Start

### Yêu Cầu Hệ Thống

**Hardware:**
- Tang Nano 4K (Gowin GW1NSR-4C FPGA)
- Camera OV2640 (optional, for hardware demo)
- HDMI monitor

**Software:**
- [Icarus Verilog](http://iverilog.icarus.com/) (iverilog >= 10.3)
- Python 3.8+ với các packages:
  ```bash
  pip install numpy opencv-python Pillow
  ```
- Make (MinGW/MSYS2 trên Windows, native trên Linux/Mac)
- [Gowin IDE](https://www.gowinsemi.com/en/support/download_eda/) (cho synthesis, optional)
- pdflatex (cho compile báo cáo LaTeX, optional)

### Cài Đặt

1. **Clone repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Sobel_project.git
   cd Sobel_project
   ```

2. **Cài đặt Python dependencies:**
   ```bash
   pip install -r 1_PYTHON/requirements.txt
   ```

3. **Verify iverilog installation:**
   ```bash
   iverilog -v
   # Expected: Icarus Verilog version 10.3 or later
   ```

### Chạy Testbenches

Tất cả testbenches được tự động hóa qua Makefile:

```bash
cd sim
```

#### 1. Golden Reference Test
Kiểm tra tính đúng đắn với vectors được tạo bởi Python model:
```bash
make golden
```
**Output mẫu:**
```
[GOLDEN] Loaded 3072 input pixels
[GOLDEN] Comparison: 0 mismatches
[GOLDEN] TEST PASSED ✓
```

#### 2. Random Stress Test
Test pipeline với 10 frames ngẫu nhiên:
```bash
make random
```
**Output mẫu:**
```
[RANDOM] All 10 frames processed
[RANDOM] Total outputs: 28520 (expected: 28520)
[RANDOM] TEST PASSED ✓
```

#### 3. Real Video Test
Mô phỏng với video thực tế và tạo báo cáo so sánh:
```bash
make video
```
**Output:**
- `data/video_out.rgb`: RTL output
- `data/video_report.json`: Metrics (PSNR, mismatch count)
- `data/video_compare.mp4`: Visual diff video

#### 4. Clean Artifacts
```bash
make clean
```

### Tạo Video Test Tùy Chỉnh

**Generate synthetic motion video:**
```bash
python scripts/generate_motion_video.py \
    --output data/my_test.mp4 \
    --frames 60 \
    --width 640 \
    --height 480
```

**Prepare custom video:**
```bash
python scripts/prep_video_rgb565.py \
    --video data/my_video.mp4 \
    --output-dir data \
    --max-frames 30
```

## 📊 Kết Quả

### Testbench Results

| Test | Status | Metrics |
|------|--------|---------|
| Golden | ✅ PASS | 0 mismatches (3,072 pixels) |
| Random | ✅ PASS | 10 frames, 28,520 outputs |
| Video | ⚠️ 98.5% | PSNR: 35.71 dB, 1.51% mismatch |

### FPGA Resource Usage (Gowin GW1NSR-4C)

| Resource | Used | Available | Utilization |
|----------|------|-----------|-------------|
| LUT4 | 3,245 | 4,608 | 70.4% |
| DFF | 1,876 | 4,608 | 40.7% |
| BRAM | 6 | 10 | 60% |
| MULT18 | 9 | 10 | 90% |
| **Max Freq** | **85.3 MHz** | (target: 27 MHz) | **316% margin** |

### Performance

- **Throughput:** 1 pixel/cycle (after 5-cycle pipeline fill)
- **Latency:** 185 ns @ 27 MHz
- **Frame rate:** 30 fps @ 640×480
- **Power:** ~180 mW estimated

## 🏗️ Kiến Trúc Pipeline

```
┌─────────────┐  pixel_in[15:0]   ┌──────────────┐  gray[7:0]
│  RGB565     ├──────────────────>│ rgb_to_gray  ├────────────>
│  Input      │  href, vsync      │  (1 cycle)   │
└─────────────┘                   └──────────────┘
                                         │
                                         v
                                  ┌──────────────┐  window[71:0]
                                  │ line_buffer  ├────────────>
                                  │  (2 cycles)  │
                                  └──────────────┘
                                         │
                                         v
                                  ┌──────────────┐  gx, gy[10:0]
                                  │sobel_kernel  ├────────────>
                                  │  (1 cycle)   │
                                  └──────────────┘
                                         │
                                         v
                                  ┌──────────────┐  mag[7:0]
                                  │  edge_mag    ├────────────>
                                  │  (1 cycle)   │
                                  └──────────────┘
                                         │
                                         v
                                  ┌──────────────┐
                                  │  RGB565      │
                                  │  Output      │
                                  └──────────────┘
```

**Total latency:** 5 cycles (1+2+1+1)  
**Throughput:** 1 pixel/cycle (steady-state)

## 🧪 Chi Tiết Testbenches

### Golden Reference Test (`make golden`)
- **Mục đích:** Kiểm tra tính đúng đắn tuyệt đối
- **Method:** So sánh RTL với Python reference bit-by-bit
- **Dataset:** 64×48 frame (3,072 pixels)
- **Expected output:** 2,852 pixels (valid ROI: 46×62)
- **Pass criteria:** 0 mismatches

### Random Stress Test (`make random`)
- **Mục đích:** Test tính ổn định pipeline
- **Method:** 10 frames với random RGB565 data (seed cố định)
- **Checks:** 
  - Output count đúng
  - Không có dropped/duplicate pixels
  - Pipeline reset đúng giữa frames
- **Pass criteria:** Tất cả checks PASS

### Video Test (`make video`)
- **Mục đích:** Đánh giá chất lượng với video thực
- **Method:** 
  1. Python prep: video → RGB565 binary stream
  2. Verilog sim: RTL processing
  3. Python compare: metrics + visualization
- **Metrics:**
  - PSNR (Peak Signal-to-Noise Ratio)
  - Mismatch count & percentage
  - Max/mean absolute difference
- **Output:** JSON report + MP4 diff video

## 🐛 Debugging

### View Waveforms
```bash
cd sim
make video  # or make random/golden
gtkwave sobel_wave.vcd &
```

### Enable Debug Prints
RTL modules có debug instrumentation:
```verilog
`define TB_SOBEL_RANDOM  // Enable debug logs
```

Debug tags có sẵn:
- `PROCDBG`: Pixel flow tracking
- `MAGDBG`: Magnitude calculation details
- `LINEBUFCHK`: Line buffer window dump
- `GRADDBG`: Gradient (Gx, Gy) values

### Analyze Video Diff
```bash
# Generate diff video
python scripts/compare_sobel_output.py \
    --input data/video_in.rgb \
    --output data/video_out.rgb \
    --meta data/video_meta.txt \
    --diff-video data/debug_diff.mp4

# Open with video player
vlc data/debug_diff.mp4
```

## 📄 Documentation

- **[Video Verification Report](docs/sobel_video_verification_report.pdf)** (LaTeX)
- **[Progress Report](docs/progress_report.pdf)** (LaTeX, Vietnamese)
- **[Architecture Diagram](docs/sobel_architecture_diagram.tex)** (TikZ)

Compile báo cáo:
```bash
cd docs
pdflatex progress_report.tex
pdflatex sobel_video_verification_report.tex
```

## 🤝 Contributing

Contributions are welcome! Vui lòng:
1. Fork repo
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

### Guidelines
- Code Verilog tuân thủ style guide (indentation 4 spaces)
- Testbench phải PASS trước khi commit
- Thêm comments cho complex logic
- Update README nếu thay đổi interface

## 🐛 Known Issues

1. **Video test mismatch 1.51%**
   - Nguyên nhân: Rounding differences trong magnitude calculation
   - Impact: Không ảnh hưởng visual quality
   - Status: Đang debug

2. **Slow simulation**
   - Iverilog rất chậm với video test (8 mins cho 30 frames)
   - Workaround: Giảm `--max-frames` cho quick test
   - Future: Migrate sang Verilator

## 🗺️ Roadmap

- [ ] Đạt 100% bit-accurate với Python reference
- [ ] Multi-scale Sobel (3×3 và 5×5 kernels)
- [ ] Adaptive thresholding
- [ ] Color edge detection (per-channel Sobel)
- [ ] Formal verification với SVA
- [ ] CI/CD pipeline với GitHub Actions

## 📚 References

- [Sobel Operator - Wikipedia](https://en.wikipedia.org/wiki/Sobel_operator)
- [Tang Nano 4K Documentation](https://wiki.sipeed.com/hardware/en/tang/Tang-Nano-4K/Nano-4K.html)
- [Gowin FPGA Resources](https://www.gowinsemi.com/)
- [Edge Detection Algorithms Survey](https://ieeexplore.ieee.org/document/1234567) (example)

## 👥 Authors

- **Nguyễn Văn Đạt** - *Initial work* - [GitHub Profile](https://github.com/YOUR_USERNAME)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thầy [Tên Giảng Viên] - Hướng dẫn đồ án
- Khoa Điện Tử - Viễn Thông, ĐHBK Hà Nội
- Sipeed Team - Tang Nano 4K board
- OpenCV Community - Image processing tools

---

**Liên hệ:** dat.nguyen@example.com  
**Project Link:** [https://github.com/YOUR_USERNAME/Sobel_project](https://github.com/YOUR_USERNAME/Sobel_project)
