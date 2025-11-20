# ModelSim compilation and simulation script for Sobel processor
# Usage: vsim -do run_modelsim.do

# Create work library
vlib work

# Compile Verilog source files
vlog -sv +incdir+../verilog/sobel \
    ../verilog/sobel/bram.v \
    ../verilog/sobel/rgb_to_gray.v \
    ../verilog/sobel/line_buffer.v \
    ../verilog/sobel/gaussian_blur.v \
    ../verilog/sobel/sobel_kernel.v \
    ../verilog/sobel/edge_mag.v \
    ../verilog/sobel/sobel_processor.v \
    tb_sobel_processor.v

# Run simulation
vsim -voptargs=+acc work.tb_sobel_processor

# Add signals to wave window
add wave -radix hex /tb_sobel_processor/*
add wave -radix hex /tb_sobel_processor/dut/*

# Run simulation
run -all

# Save waveform
write wave sobel_wave.wlf
