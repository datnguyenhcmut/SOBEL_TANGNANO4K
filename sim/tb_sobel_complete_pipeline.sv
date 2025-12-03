//==============================================================================
// Testbench: tb_sobel_complete_pipeline
// Description: Complete testbench for Sobel edge detection pipeline
//              Tests: RGB->Gray->Bilateral->Sobel->Shadow->Binary->Noise
//              Compares with Python golden reference
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
//==============================================================================

`timescale 1ns/1ps

module tb_sobel_complete_pipeline;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter IMG_WIDTH = 640;
    parameter IMG_HEIGHT = 480;
    parameter PIXEL_WIDTH = 8;
    parameter CLK_PERIOD = 37;  // 27MHz clock
    
    //==========================================================================
    // Signals
    //==========================================================================
    reg clk;
    reg rst_n;
    
    // Input RGB565
    reg [15:0] pixel_in;
    reg href;
    reg vsync;
    
    // Sobel processor outputs
    wire [15:0] pixel_out;
    wire pixel_valid;
    wire binary_pixel;
    wire binary_valid;
    wire strong_edge;
    wire weak_edge;
    
    // Control
    reg sobel_enable;
    reg [7:0] edge_threshold;
    reg [1:0] threshold_mode;
    
    //==========================================================================
    // Memory for input/output
    //==========================================================================
    reg [15:0] input_image [0:IMG_WIDTH*IMG_HEIGHT-1];
    reg [7:0] expected_output [0:IMG_WIDTH*IMG_HEIGHT-1];
    reg [7:0] actual_output [0:IMG_WIDTH*IMG_HEIGHT-1];
    
    integer pixel_count;
    integer error_count;
    integer frame_count;
    
    //==========================================================================
    // File handles
    //==========================================================================
    integer input_file, expected_file, output_file, log_file;
    
    //==========================================================================
    // DUT: Sobel Processor
    //==========================================================================
    sobel_processor #(
        .IMG_WIDTH(IMG_WIDTH),
        .IMG_HEIGHT(IMG_HEIGHT),
        .PIXEL_WIDTH(PIXEL_WIDTH),
        .USE_BILATERAL(1)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .href(href),
        .vsync(vsync),
        .pixel_in(pixel_in),
        .sobel_enable(sobel_enable),
        .edge_threshold(edge_threshold),
        .threshold_mode(threshold_mode),
        .pixel_valid(pixel_valid),
        .pixel_out(pixel_out),
        .binary_pixel(binary_pixel),
        .binary_valid(binary_valid),
        .strong_edge(strong_edge),
        .weak_edge(weak_edge)
    );
    
    //==========================================================================
    // Clock generation
    //==========================================================================
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    //==========================================================================
    // Load test images
    //==========================================================================
    task load_input_image;
        input string filename;
        integer status;
        integer i;
        reg [15:0] pixel;
        begin
            input_file = $fopen(filename, "rb");
            if (input_file == 0) begin
                $display("ERROR: Cannot open input file: %s", filename);
                $finish;
            end
            
            for (i = 0; i < IMG_WIDTH * IMG_HEIGHT; i = i + 1) begin
                status = $fread(pixel, input_file);
                if (status != 2) begin
                    $display("ERROR: Failed to read pixel %0d", i);
                    $finish;
                end
                input_image[i] = pixel;
            end
            
            $fclose(input_file);
            $display("Loaded input image: %s (%0d pixels)", filename, i);
        end
    endtask
    
    task load_expected_output;
        input string filename;
        integer status;
        integer i;
        reg [7:0] pixel;
        begin
            expected_file = $fopen(filename, "rb");
            if (expected_file == 0) begin
                $display("WARNING: Cannot open expected output file: %s", filename);
                // Continue without golden reference
                return;
            end
            
            for (i = 0; i < IMG_WIDTH * IMG_HEIGHT; i = i + 1) begin
                status = $fread(pixel, expected_file);
                if (status != 1) begin
                    $display("ERROR: Failed to read expected pixel %0d", i);
                    $finish;
                end
                expected_output[i] = pixel;
            end
            
            $fclose(expected_file);
            $display("Loaded expected output: %s", filename);
        end
    endtask
    
    //==========================================================================
    // Save output image
    //==========================================================================
    task save_output_image;
        input string filename;
        integer i;
        begin
            output_file = $fopen(filename, "wb");
            if (output_file == 0) begin
                $display("ERROR: Cannot create output file: %s", filename);
                $finish;
            end
            
            for (i = 0; i < IMG_WIDTH * IMG_HEIGHT; i = i + 1) begin
                $fwrite(output_file, "%c", actual_output[i]);
            end
            
            $fclose(output_file);
            $display("Saved output image: %s", filename);
        end
    endtask
    
    //==========================================================================
    // Compare with golden reference
    //==========================================================================
    task compare_outputs;
        integer i;
        integer diff;
        integer max_diff;
        integer total_diff;
        real avg_diff;
        real psnr;
        real mse;
        begin
            error_count = 0;
            max_diff = 0;
            total_diff = 0;
            
            for (i = 0; i < IMG_WIDTH * IMG_HEIGHT; i = i + 1) begin
                diff = actual_output[i] - expected_output[i];
                if (diff < 0) diff = -diff;
                
                if (diff > 0) begin
                    error_count = error_count + 1;
                    total_diff = total_diff + diff;
                    if (diff > max_diff) max_diff = diff;
                end
            end
            
            avg_diff = real'(total_diff) / real'(IMG_WIDTH * IMG_HEIGHT);
            mse = real'(total_diff * total_diff) / real'(IMG_WIDTH * IMG_HEIGHT);
            psnr = (mse > 0) ? (10.0 * $log10(255.0 * 255.0 / mse)) : 999.9;
            
            $display("");
            $display("====================================================");
            $display("COMPARISON RESULTS:");
            $display("====================================================");
            $display("Total pixels:        %0d", IMG_WIDTH * IMG_HEIGHT);
            $display("Different pixels:    %0d (%.2f%%)", error_count, 
                     100.0 * real'(error_count) / real'(IMG_WIDTH * IMG_HEIGHT));
            $display("Max difference:      %0d", max_diff);
            $display("Average difference:  %.2f", avg_diff);
            $display("PSNR:               %.2f dB", psnr);
            $display("====================================================");
            
            if (psnr > 30.0) begin
                $display("RESULT: PASS - Excellent match (PSNR > 30dB)");
            end else if (psnr > 20.0) begin
                $display("RESULT: ACCEPTABLE - Good match (PSNR > 20dB)");
            end else begin
                $display("RESULT: FAIL - Poor match (PSNR < 20dB)");
            end
            $display("====================================================");
            $display("");
        end
    endtask
    
    //==========================================================================
    // Generate video timing signals
    //==========================================================================
    task send_frame;
        integer row, col, idx;
        begin
            frame_count = frame_count + 1;
            $display("Sending frame %0d...", frame_count);
            
            // VSYNC pulse (active low)
            vsync = 0;
            href = 0;
            repeat(10) @(posedge clk);
            vsync = 1;
            
            // Send all rows
            for (row = 0; row < IMG_HEIGHT; row = row + 1) begin
                // HREF active (line valid)
                href = 1;
                
                // Send all columns
                for (col = 0; col < IMG_WIDTH; col = col + 1) begin
                    idx = row * IMG_WIDTH + col;
                    pixel_in = input_image[idx];
                    @(posedge clk);
                end
                
                // HREF inactive (horizontal blanking)
                href = 0;
                repeat(5) @(posedge clk);
            end
            
            // End of frame
            href = 0;
            repeat(10) @(posedge clk);
            
            $display("Frame %0d sent", frame_count);
        end
    endtask
    
    //==========================================================================
    // Capture output
    //==========================================================================
    always @(posedge clk) begin
        if (binary_valid && pixel_count < IMG_WIDTH * IMG_HEIGHT) begin
            actual_output[pixel_count] = binary_pixel ? 8'd255 : 8'd0;
            pixel_count = pixel_count + 1;
            
            if (pixel_count % 10000 == 0) begin
                $display("Captured %0d pixels...", pixel_count);
            end
        end
    end
    
    //==========================================================================
    // Main test sequence
    //==========================================================================
    initial begin
        // Initialize
        $display("====================================================");
        $display("Sobel Edge Detection Pipeline Testbench");
        $display("====================================================");
        $display("Image size: %0dx%0d", IMG_WIDTH, IMG_HEIGHT);
        $display("Clock period: %0dns (%.2fMHz)", CLK_PERIOD, 1000.0/CLK_PERIOD);
        $display("====================================================");
        
        // Reset
        rst_n = 0;
        href = 0;
        vsync = 1;
        pixel_in = 16'h0000;
        sobel_enable = 1;
        edge_threshold = 8'd70;
        threshold_mode = 2'b10;  // Hysteresis
        pixel_count = 0;
        error_count = 0;
        frame_count = 0;
        
        repeat(10) @(posedge clk);
        rst_n = 1;
        repeat(10) @(posedge clk);
        
        // Load test data
        $display("\nLoading test images...");
        load_input_image("../sim/data/input_rgb565.bin");
        load_expected_output("../sim/data/expected_output.bin");
        
        // Send frame
        $display("\nStarting pipeline test...");
        send_frame();
        
        // Wait for pipeline to finish
        $display("\nWaiting for pipeline to complete...");
        repeat(1000) @(posedge clk);
        
        // Save results
        $display("\nSaving output...");
        save_output_image("../sim/data/verilog_output.bin");
        
        // Compare with golden reference
        if (expected_output[0] !== 8'hxx) begin
            $display("\nComparing with Python golden reference...");
            compare_outputs();
        end else begin
            $display("\nNo golden reference available, skipping comparison");
        end
        
        // Finish
        $display("\n====================================================");
        $display("TEST COMPLETE");
        $display("====================================================");
        $finish;
    end
    
    //==========================================================================
    // Timeout watchdog
    //==========================================================================
    initial begin
        #(CLK_PERIOD * 1000000);  // 1M cycles timeout
        $display("ERROR: Timeout - test did not complete");
        $finish;
    end
    
    //==========================================================================
    // Dump waveforms
    //==========================================================================
    initial begin
        $dumpfile("tb_sobel_complete.vcd");
        $dumpvars(0, tb_sobel_complete_pipeline);
    end

endmodule
