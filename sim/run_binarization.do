# ModelSim simulation script for image_binarization
# Run from sim/ folder: vsim -do run_binarization.do

# Create work library
vlib work

# Compile design files
vlog -work work ../verilog/sobel/image_binarization.v
vlog -work work tb_image_binarization.v

# Start simulation
vsim -voptargs=+acc work.tb_image_binarization

# Add waves
add wave -position insertpoint sim:/tb_image_binarization/*
add wave -position insertpoint sim:/tb_image_binarization/dut/*

# Run simulation
run -all

# Quit
quit -f
