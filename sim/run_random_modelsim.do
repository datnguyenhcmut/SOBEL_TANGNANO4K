# ModelSim script for tb_sobel_random testbench
vlib work

vlog -sv +incdir+../verilog/sobel \
    ../verilog/sobel/bram.v \
    ../verilog/sobel/rgb_to_gray.v \
    ../verilog/sobel/line_buffer.v \
    ../verilog/sobel/gaussian_blur.v \
    ../verilog/sobel/sobel_kernel.v \
    ../verilog/sobel/edge_mag.v \
    ../verilog/sobel/sobel_processor.v \
    tb_sobel_random.v

vsim -voptargs=+acc work.tb_sobel_random

add wave -radix hex /tb_sobel_random/*
add wave -radix hex /tb_sobel_random/dut/*

run -all
