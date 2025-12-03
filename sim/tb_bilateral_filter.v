//==============================================================================
// Testbench: tb_bilateral_filter
// Description: Test edge-preserving bilateral filter vs Gaussian
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
//==============================================================================

`timescale 1ns / 1ps

module tb_bilateral_filter;

    parameter PIXEL_WIDTH = 8;
    parameter CLK_PERIOD = 10;

    reg clk, rst_n;
    reg window_valid;
    reg [PIXEL_WIDTH*9-1:0] window_flat;
    
    wire bilateral_valid;
    wire [PIXEL_WIDTH*9-1:0] window_bilateral;
    wire gaussian_valid;
    wire [PIXEL_WIDTH*9-1:0] window_gaussian;

    // DUT: Bilateral filter
    bilateral_filter #(.PIXEL_WIDTH(PIXEL_WIDTH), .SIGMA_RANGE(30)) dut_bilateral (
        .clk(clk), .rst_n(rst_n), .window_valid(window_valid),
        .window_flat(window_flat), .filter_valid(bilateral_valid), .window_filtered(window_bilateral)
    );
    
    // Reference: Gaussian filter
    gaussian_blur #(.PIXEL_WIDTH(PIXEL_WIDTH)) dut_gaussian (
        .clk(clk), .rst_n(rst_n), .window_valid(window_valid),
        .window_flat(window_flat), .blur_valid(gaussian_valid), .window_blurred(window_gaussian)
    );

    // Clock generation
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // Test scenarios
    initial begin
        $display("=== Bilateral Filter vs Gaussian Blur Test ===");
        rst_n = 0; window_valid = 0; window_flat = 0;
        #(CLK_PERIOD*2);
        rst_n = 1;
        #(CLK_PERIOD);

        // Test Case 1: Uniform region (no edges) - Both should smooth similarly
        $display("\n--- Test 1: Uniform region (100,100,100...) ---");
        window_flat = {8'd100, 8'd100, 8'd100, 8'd100, 8'd100, 8'd100, 8'd100, 8'd100, 8'd100};
        window_valid = 1;
        #(CLK_PERIOD);
        window_valid = 0;
        #(CLK_PERIOD*2);
        $display("Input center: 100");
        $display("Bilateral output: %d", window_bilateral[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);
        $display("Gaussian output:  %d", window_gaussian[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);

        // Test Case 2: Noisy uniform region - Both should reduce noise
        $display("\n--- Test 2: Noisy uniform (100±5) ---");
        window_flat = {8'd105, 8'd98, 8'd102, 8'd97, 8'd100, 8'd103, 8'd99, 8'd101, 8'd96};
        window_valid = 1;
        #(CLK_PERIOD);
        window_valid = 0;
        #(CLK_PERIOD*2);
        $display("Input center: 100");
        $display("Bilateral output: %d (should smooth noise)", window_bilateral[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);
        $display("Gaussian output:  %d (should smooth noise)", window_gaussian[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);

        // Test Case 3: SHARP EDGE (50 vs 200) - Bilateral should preserve, Gaussian blurs
        $display("\n--- Test 3: Sharp edge (background=50, edge=200) ---");
        window_flat = {8'd50, 8'd50, 8'd50, 8'd50, 8'd200, 8'd200, 8'd50, 8'd200, 8'd200};
        window_valid = 1;
        #(CLK_PERIOD);
        window_valid = 0;
        #(CLK_PERIOD*2);
        $display("Input center: 200 (edge pixel)");
        $display("Bilateral output: %d (should stay close to 200 - EDGE PRESERVED)", window_bilateral[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);
        $display("Gaussian output:  %d (should blur toward ~125 - EDGE BLURRED)", window_gaussian[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);
        
        // Test Case 4: Edge with noise
        $display("\n--- Test 4: Noisy edge (50±3 vs 200±3) ---");
        window_flat = {8'd48, 8'd52, 8'd51, 8'd49, 8'd198, 8'd202, 8'd53, 8'd197, 8'd201};
        window_valid = 1;
        #(CLK_PERIOD);
        window_valid = 0;
        #(CLK_PERIOD*2);
        $display("Input center: 198 (noisy edge)");
        $display("Bilateral output: %d (should preserve edge ~200, ignore far pixels)", window_bilateral[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);
        $display("Gaussian output:  %d (should blur everything)", window_gaussian[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);

        // Test Case 5: Weak edge (100 vs 130) - within SIGMA_RANGE
        $display("\n--- Test 5: Weak edge (100 vs 130) - within threshold ---");
        window_flat = {8'd100, 8'd100, 8'd100, 8'd100, 8'd130, 8'd130, 8'd100, 8'd130, 8'd130};
        window_valid = 1;
        #(CLK_PERIOD);
        window_valid = 0;
        #(CLK_PERIOD*2);
        $display("Input center: 130");
        $display("Bilateral output: %d (should smooth slightly)", window_bilateral[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);
        $display("Gaussian output:  %d (should smooth more)", window_gaussian[PIXEL_WIDTH*4 +: PIXEL_WIDTH]);

        #(CLK_PERIOD*5);
        $display("\n=== Test Complete ===");
        $display("Summary:");
        $display("- Bilateral should PRESERVE sharp edges (Test 3,4)");
        $display("- Bilateral should SMOOTH noise in uniform regions (Test 2)");
        $display("- Gaussian blurs everything equally");
        $finish;
    end

endmodule
