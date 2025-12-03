# ModelSim compile and simulation script for Image Binarization
# Run: vsim -do run_binarization_sim.do

# Create work library
vlib work

# Compile source files
echo "Compiling image_binarization.v..."
vlog -work work ../verilog/sobel/image_binarization.v

# Compile testbench
echo "Compiling testbench..."
vlog -work work tb_image_binarization.v

# Start simulation
echo "Starting simulation..."
vsim -c -do "run -all; quit" work.tb_image_binarization

# View waveform (optional - comment out -c above and use this)
# vsim work.tb_image_binarization
# add wave -recursive *
# run -all
