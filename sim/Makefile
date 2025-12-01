# Makefile for Sobel Testing (iverilog compatible)

IVERILOG = iverilog
VVP = vvp
GTKWAVE = gtkwave

VERILOG_DIR = ../verilog/sobel
SRC_FILES = $(VERILOG_DIR)/bram.v \
			$(VERILOG_DIR)/rgb_to_gray.v \
			$(VERILOG_DIR)/line_buffer.v \
			$(VERILOG_DIR)/gaussian_blur.v \
			$(VERILOG_DIR)/sobel_kernel.v \
			$(VERILOG_DIR)/edge_mag.v \
			$(VERILOG_DIR)/image_binarization.v \
			$(VERILOG_DIR)/sobel_processor.v

TB_FILE = tb_sobel_processor.v
SIM_OUT = sim_sobel.vvp
VCD_OUT = sobel_wave.vcd

VIDEO_TB = tb_sobel_video.v
VIDEO_SIM = sim_video.vvp
DATA_DIR = ../data
VIDEO_IN_RGB = $(DATA_DIR)/video_in.rgb
VIDEO_META = $(DATA_DIR)/video_meta.txt
VIDEO_OUT_RGB = $(DATA_DIR)/video_out.rgb
VIDEO_REPORT = $(DATA_DIR)/video_report.json
VIDEO_DIFF = $(DATA_DIR)/video_compare.mp4

.PHONY: all compile run clean view help random golden video binarization

all: compile run

compile:
	@echo "=== Compiling Sobel (iverilog) ==="
	$(IVERILOG) -g2012 -Wall -s tb_sobel_processor -o $(SIM_OUT) $(SRC_FILES) $(TB_FILE)
	@echo "Compile successful!"

run: compile
	@echo "=== Running Simulation ==="
	$(VVP) $(SIM_OUT)

# Randomized self-checking testbench
random:
	@echo "=== Compiling tb_sobel_random ==="
	$(IVERILOG) -g2012 -Wall -s tb_sobel_random -o sim_random.vvp $(SRC_FILES) tb_sobel_random.v
	@echo "=== Running tb_sobel_random ==="
	$(VVP) sim_random.vvp

# Golden-vector check (expects mem files under sim/golden)
golden:
	@echo "=== Compiling tb_sobel_golden_fix ==="
	$(IVERILOG) -g2012 -Wall -s tb_sobel_golden_fix -o sim_golden.vvp -f golden_files.txt
	@echo "=== Running tb_sobel_golden_fix ==="
	$(VVP) sim_golden.vvp

# Binarization test (standalone module test)
binarization:
	@echo "=== Compiling tb_image_binarization ==="
	$(IVERILOG) -g2005 -Wall -s tb_image_binarization -o sim_binarization.vvp $(VERILOG_DIR)/image_binarization.v tb_image_binarization.v
	@echo "=== Running tb_image_binarization ==="
	$(VVP) sim_binarization.vvp
	@echo "=== Binarization test completed ==="

video:
	@echo "=== Preparing video stimulus ==="
	python ../scripts/prep_video_rgb565.py --output-dir $(DATA_DIR)
	@echo "=== Compiling tb_sobel_video ==="
	$(IVERILOG) -g2012 -Wall -s tb_sobel_video -o $(VIDEO_SIM) $(SRC_FILES) $(VIDEO_TB)
	@echo "=== Running tb_sobel_video ==="
	$(VVP) $(VIDEO_SIM)
	@echo "=== Comparing video output ==="
	python ../scripts/compare_sobel_output.py --input $(VIDEO_IN_RGB) --output $(VIDEO_OUT_RGB) --meta $(VIDEO_META) --report $(VIDEO_REPORT) --diff-video $(VIDEO_DIFF)

# ModelSim targets
msim:
	@echo "=== ModelSim: Basic testbench ==="
	vsim -c -do "do run_modelsim.do; quit -f"

msim-random:
	@echo "=== ModelSim: Random testbench ==="
	vsim -c -do "do run_random_modelsim.do; quit -f"

msim-golden:
	@echo "=== ModelSim: Golden testbench ==="
	vsim -c -do "do run_golden_modelsim.do; quit -f"

msim-binarization:
	@echo "=== ModelSim: Binarization test ==="
	vsim -c -do "do run_binarization_modelsim.do; quit -f"

msim-gui:
	@echo "=== ModelSim GUI ==="
	vsim -gui -do run_modelsim.do

msim-gui-bin:
	@echo "=== ModelSim GUI: Binarization ==="
	vsim -gui -do run_binarization_modelsim.do

clean:
	powershell -NoLogo -NoProfile -Command "Remove-Item -Force -ErrorAction SilentlyContinue '$(SIM_OUT)','sim_random.vvp','sim_golden.vvp','$(VCD_OUT)','$(VIDEO_SIM)','$(VIDEO_IN_RGB)','$(VIDEO_META)','$(VIDEO_OUT_RGB)','$(VIDEO_REPORT)','$(VIDEO_DIFF)','work','*.wlf','transcript'"

view:
	$(GTKWAVE) $(VCD_OUT) &

help:
	@echo "Sobel Test Makefile"
	@echo "=== Icarus Verilog ==="
	@echo "make              - compile and run"
	@echo "make compile      - compile only"
	@echo "make run          - run simulation"
	@echo "make random       - random test"
	@echo "make golden       - golden test"
	@echo "make binarization - binarization test (NEW)"
	@echo "make video        - video test"
	@echo ""
	@echo "=== ModelSim ==="
	@echo "make msim                - ModelSim basic test (batch)"
	@echo "make msim-random         - ModelSim random test (batch)"
	@echo "make msim-golden         - ModelSim golden test (batch)"
	@echo "make msim-binarization   - ModelSim binarization test (batch)"
	@echo "make msim-gui            - ModelSim GUI mode"
	@echo "make msim-gui-bin        - ModelSim GUI binarization test"
	@echo ""
	@echo "=== Utilities ==="
	@echo "make clean   - clean up"
	@echo "make view    - view waveform"
