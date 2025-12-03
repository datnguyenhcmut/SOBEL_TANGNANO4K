//==============================================================================
// Testbench: tb_hough_transform
// Description: Standalone testbench for Hough Transform validation
//              Tests line detection accuracy with known test patterns
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
//==============================================================================

`timescale 1ns/1ps

module tb_hough_transform;

    //==========================================================================
    // Parameters
    //==========================================================================
    parameter IMG_WIDTH = 640;
    parameter IMG_HEIGHT = 480;
    parameter CLK_PERIOD = 37;  // 27MHz
    
    //==========================================================================
    // Signals
    //==========================================================================
    reg clk;
    reg rst_n;
    
    // Input
    reg pixel_in;
    reg pixel_valid;
    reg [9:0] pixel_x;
    reg [9:0] pixel_y;
    reg frame_start;
    
    // Output
    wire line_valid;
    wire [15:0] line_rho;
    wire [7:0] line_theta;
    wire [11:0] line_votes;
    
    //==========================================================================
    // DUT: Hough Transform
    //==========================================================================
    hough_transform #(
        .IMG_WIDTH(IMG_WIDTH),
        .IMG_HEIGHT(IMG_HEIGHT),
        .RHO_RESOLUTION(4),
        .THETA_STEPS(45),
        .ACCUMULATOR_BITS(12),
        .MIN_VOTES(50)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .pixel_in(pixel_in),
        .pixel_valid(pixel_valid),
        .pixel_x(pixel_x),
        .pixel_y(pixel_y),
        .frame_start(frame_start),
        .line_valid(line_valid),
        .line_rho(line_rho),
        .line_theta(line_theta),
        .line_votes(line_votes)
    );
    
    //==========================================================================
    // Clock generation
    //==========================================================================
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    //==========================================================================
    // Task: Draw line in test image
    //==========================================================================
    reg [0:IMG_WIDTH*IMG_HEIGHT-1] test_image;
    
    task draw_vertical_line;
        input integer x_pos;
        integer y;
        begin
            for (y = 0; y < IMG_HEIGHT; y = y + 1) begin
                test_image[y * IMG_WIDTH + x_pos] = 1'b1;
            end
        end
    endtask
    
    task draw_horizontal_line;
        input integer y_pos;
        integer x;
        begin
            for (x = 0; x < IMG_WIDTH; x = x + 1) begin
                test_image[y_pos * IMG_WIDTH + x] = 1'b1;
            end
        end
    endtask
    
    task draw_diagonal_line;
        integer i;
        begin
            for (i = 0; i < IMG_WIDTH && i < IMG_HEIGHT; i = i + 1) begin
                test_image[i * IMG_WIDTH + i] = 1'b1;
            end
        end
    endtask
    
    task clear_image;
        integer i;
        begin
            for (i = 0; i < IMG_WIDTH * IMG_HEIGHT; i = i + 1) begin
                test_image[i] = 1'b0;
            end
        end
    endtask
    
    //==========================================================================
    // Task: Send frame to DUT
    //==========================================================================
    task send_frame;
        integer x, y, idx;
        begin
            // Frame start pulse
            frame_start = 1;
            @(posedge clk);
            frame_start = 0;
            
            // Wait for clearing to complete
            repeat(30000) @(posedge clk);
            
            // Send all pixels
            for (y = 0; y < IMG_HEIGHT; y = y + 1) begin
                for (x = 0; x < IMG_WIDTH; x = x + 1) begin
                    idx = y * IMG_WIDTH + x;
                    pixel_valid = 1'b1;
                    pixel_x = x;
                    pixel_y = y;
                    pixel_in = test_image[idx];
                    @(posedge clk);
                end
            end
            
            pixel_valid = 1'b0;
            
            // Wait for peak detection
            repeat(30000) @(posedge clk);
        end
    endtask
    
    //==========================================================================
    // Monitor outputs
    //==========================================================================
    always @(posedge clk) begin
        if (line_valid) begin
            $display("");
            $display("LINE DETECTED:");
            $display("  Rho:   %0d pixels", line_rho);
            $display("  Theta: %0d (angle = %0d degrees)", line_theta, line_theta * 4);
            $display("  Votes: %0d", line_votes);
            $display("");
        end
    end
    
    //==========================================================================
    // Test cases
    //==========================================================================
    integer test_num;
    
    initial begin
        $display("====================================================");
        $display("Hough Transform Validation Testbench");
        $display("====================================================");
        $display("Image: %0dx%0d", IMG_WIDTH, IMG_HEIGHT);
        $display("====================================================");
        
        // Initialize
        rst_n = 0;
        pixel_in = 0;
        pixel_valid = 0;
        pixel_x = 0;
        pixel_y = 0;
        frame_start = 0;
        test_num = 0;
        
        repeat(10) @(posedge clk);
        rst_n = 1;
        repeat(10) @(posedge clk);
        
        //----------------------------------------------------------------------
        // Test 1: Vertical line at X=200
        //----------------------------------------------------------------------
        test_num = 1;
        $display("\n[TEST %0d] Vertical line at X=200", test_num);
        $display("Expected: Theta ≈ 0° (or 180°), Rho ≈ 200");
        $display("----------------------------------------------------");
        clear_image();
        draw_vertical_line(200);
        send_frame();
        
        if (line_valid) begin
            if (line_votes > 400) begin
                $display("✓ PASS: Strong detection (%0d votes)", line_votes);
            end else begin
                $display("✗ FAIL: Weak detection (%0d votes)", line_votes);
            end
        end else begin
            $display("✗ FAIL: No line detected");
        end
        
        //----------------------------------------------------------------------
        // Test 2: Horizontal line at Y=240
        //----------------------------------------------------------------------
        test_num = 2;
        $display("\n[TEST %0d] Horizontal line at Y=240", test_num);
        $display("Expected: Theta ≈ 90°, Rho ≈ 240");
        $display("----------------------------------------------------");
        clear_image();
        draw_horizontal_line(240);
        send_frame();
        
        if (line_valid) begin
            if (line_votes > 600) begin
                $display("✓ PASS: Strong detection (%0d votes)", line_votes);
            end else begin
                $display("✗ FAIL: Weak detection (%0d votes)", line_votes);
            end
        end else begin
            $display("✗ FAIL: No line detected");
        end
        
        //----------------------------------------------------------------------
        // Test 3: Diagonal line (45°)
        //----------------------------------------------------------------------
        test_num = 3;
        $display("\n[TEST %0d] Diagonal line (45°)", test_num);
        $display("Expected: Theta ≈ 44°-48°");
        $display("----------------------------------------------------");
        clear_image();
        draw_diagonal_line();
        send_frame();
        
        if (line_valid) begin
            if (line_votes > 400) begin
                $display("✓ PASS: Strong detection (%0d votes)", line_votes);
            end else begin
                $display("✗ FAIL: Weak detection (%0d votes)", line_votes);
            end
        end else begin
            $display("✗ FAIL: No line detected");
        end
        
        //----------------------------------------------------------------------
        // Summary
        //----------------------------------------------------------------------
        $display("\n====================================================");
        $display("TESTS COMPLETE");
        $display("====================================================");
        
        $finish;
    end
    
    //==========================================================================
    // Timeout
    //==========================================================================
    initial begin
        #(CLK_PERIOD * 10000000);  // 10M cycles
        $display("ERROR: Timeout");
        $finish;
    end
    
    //==========================================================================
    // Waveform dump
    //==========================================================================
    initial begin
        $dumpfile("tb_hough.vcd");
        $dumpvars(0, tb_hough_transform);
    end

endmodule
