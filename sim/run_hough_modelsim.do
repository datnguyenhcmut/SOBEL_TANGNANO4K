# ModelSim script for Hough Transform testing
# Usage: vsim -do run_hough_modelsim.do

# Clean previous compilation
if {[file exists work]} {
    vdel -all
}

# Create work library
vlib work

# Compile Verilog files
echo "Compiling Hough Transform module..."
vlog -sv ../verilog/sobel/hough_transform.v

echo "Compiling testbench..."
vlog -sv tb_hough_modelsim.v

# Start simulation
echo "Starting simulation..."
vsim -t ps work.tb_hough_modelsim -voptargs=+acc

# Add waves
echo "Adding waveforms..."
add wave -divider "Clock & Reset"
add wave -radix binary sim:/tb_hough_modelsim/clk
add wave -radix binary sim:/tb_hough_modelsim/rst_n

add wave -divider "Input Signals"
add wave -radix unsigned sim:/tb_hough_modelsim/test_num
add wave -radix binary sim:/tb_hough_modelsim/frame_start
add wave -radix binary sim:/tb_hough_modelsim/edge_valid
add wave -radix unsigned sim:/tb_hough_modelsim/edge_x
add wave -radix unsigned sim:/tb_hough_modelsim/edge_y

add wave -divider "DUT State"
add wave -radix ascii sim:/tb_hough_modelsim/dut/state
add wave -radix unsigned sim:/tb_hough_modelsim/dut/vote_count
add wave -radix unsigned sim:/tb_hough_modelsim/dut/clear_addr
add wave -radix binary sim:/tb_hough_modelsim/dut/processing_done

add wave -divider "Voting Process"
add wave -radix unsigned sim:/tb_hough_modelsim/dut/theta_idx
add wave -radix decimal sim:/tb_hough_modelsim/dut/rho_calc
add wave -radix unsigned sim:/tb_hough_modelsim/dut/rho_bin
add wave -radix unsigned sim:/tb_hough_modelsim/dut/accum_addr

add wave -divider "Peak Detection"
add wave -radix unsigned sim:/tb_hough_modelsim/dut/search_addr
add wave -radix unsigned sim:/tb_hough_modelsim/dut/max_votes
add wave -radix unsigned sim:/tb_hough_modelsim/dut/max_addr

add wave -divider "Output Signals"
add wave -radix binary sim:/tb_hough_modelsim/line_valid
add wave -radix unsigned sim:/tb_hough_modelsim/line_rho
add wave -radix unsigned sim:/tb_hough_modelsim/line_theta
add wave -radix unsigned sim:/tb_hough_modelsim/line_votes

# Run simulation
echo "Running simulation..."
run -all

# Zoom to fit
wave zoom full

echo "Simulation complete. Check transcript and waveform."
