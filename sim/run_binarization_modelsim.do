# ModelSim DO script for Image Binarization testbench
# Usage: vsim -c -do "do run_binarization_modelsim.do; quit -f"

# Create work library
vlib work

# Compile source files
echo "Compiling image_binarization.v..."
vlog -work work ../verilog/sobel/image_binarization.v

echo "Compiling tb_image_binarization.v..."
vlog -work work tb_image_binarization.v

# Load testbench
vsim -t ps work.tb_image_binarization

# Add waves
add wave -divider "Clock & Reset"
add wave -radix binary /tb_image_binarization/clk
add wave -radix binary /tb_image_binarization/rst_n

add wave -divider "Input Signals"
add wave -radix unsigned /tb_image_binarization/edge_magnitude
add wave -radix binary /tb_image_binarization/edge_valid
add wave -radix unsigned /tb_image_binarization/threshold
add wave -radix binary /tb_image_binarization/threshold_mode

add wave -divider "Output Signals"
add wave -radix binary /tb_image_binarization/binary_pixel
add wave -radix binary /tb_image_binarization/binary_valid
add wave -radix binary /tb_image_binarization/strong_edge
add wave -radix binary /tb_image_binarization/weak_edge

add wave -divider "Internal Signals (DUT)"
add wave -radix binary /tb_image_binarization/dut/fixed_threshold_result
add wave -radix binary /tb_image_binarization/dut/is_strong_edge
add wave -radix binary /tb_image_binarization/dut/is_weak_edge
add wave -radix unsigned /tb_image_binarization/dut/local_mean
add wave -radix unsigned /tb_image_binarization/dut/adaptive_threshold

# Run simulation
echo "Running simulation..."
run -all

# Show results
echo "=== Simulation completed ==="
echo "Check transcript for test results"

# Exit (commented out for GUI mode)
# quit -f
