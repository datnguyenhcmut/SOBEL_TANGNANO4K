// Testbench for Hough Transform - ModelSim compatible
// Tests vertical, horizontal, and diagonal line detection
`timescale 1ns/1ps

module tb_hough_modelsim;

    // Parameters matching hough_transform.v
    parameter IMG_WIDTH = 640;
    parameter IMG_HEIGHT = 480;
    parameter RHO_RESOLUTION = 4;
    parameter THETA_STEPS = 45;
    parameter ACCUMULATOR_BITS = 12;
    parameter MIN_VOTES = 100;
    
    // Calculate max rho
    parameter MAX_RHO = $rtoi($sqrt(IMG_WIDTH*IMG_WIDTH + IMG_HEIGHT*IMG_HEIGHT));
    parameter RHO_BINS = MAX_RHO / RHO_RESOLUTION;

    // Testbench signals
    reg clk;
    reg rst_n;
    reg pixel_in;
    reg pixel_valid;
    reg [9:0] pixel_x;
    reg [9:0] pixel_y;
    reg frame_start;
    
    wire line_valid;
    wire [15:0] line_rho;
    wire [7:0] line_theta;
    wire [ACCUMULATOR_BITS-1:0] line_votes;

    // Test image memory
    reg [IMG_WIDTH-1:0] test_image [0:IMG_HEIGHT-1];
    
    // DUT instantiation
    hough_transform #(
        .IMG_WIDTH(IMG_WIDTH),
        .IMG_HEIGHT(IMG_HEIGHT),
        .RHO_RESOLUTION(RHO_RESOLUTION),
        .THETA_STEPS(THETA_STEPS),
        .ACCUMULATOR_BITS(ACCUMULATOR_BITS),
        .MIN_VOTES(MIN_VOTES)
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

    // Clock generation: 27MHz (37ns period)
    initial begin
        clk = 0;
        forever #18.5 clk = ~clk;
    end

    // Test counter
    integer test_num;
    
    // Tasks for drawing test patterns
    task clear_image;
        integer i, j;
        begin
            for (i = 0; i < IMG_HEIGHT; i = i + 1) begin
                test_image[i] = {IMG_WIDTH{1'b0}};
            end
        end
    endtask

    task draw_vertical_line;
        input [9:0] x_pos;
        integer y;
        begin
            for (y = 0; y < IMG_HEIGHT; y = y + 1) begin
                test_image[y][x_pos] = 1'b1;
            end
            $display("  Drew vertical line at X=%0d", x_pos);
        end
    endtask

    task draw_horizontal_line;
        input [9:0] y_pos;
        integer x;
        begin
            for (x = 0; x < IMG_WIDTH; x = x + 1) begin
                test_image[y_pos][x] = 1'b1;
            end
            $display("  Drew horizontal line at Y=%0d", y_pos);
        end
    endtask

    task draw_diagonal_line;
        integer x, y;
        begin
            // 45 degree line from (100,100) to (540,540)
            for (x = 100; x < 540; x = x + 1) begin
                y = x;
                if (y < IMG_HEIGHT && x < IMG_WIDTH) begin
                    test_image[y][x] = 1'b1;
                end
            end
            $display("  Drew 45-degree diagonal line");
        end
    endtask

    // Task to send frame to DUT
    task send_frame;
        integer x, y;
        begin
            // Frame start pulse
            frame_start = 1;
            @(posedge clk);
            frame_start = 0;
            @(posedge clk);
            
            // Send all edge pixels
            for (y = 0; y < IMG_HEIGHT; y = y + 1) begin
                for (x = 0; x < IMG_WIDTH; x = x + 1) begin
                    if (test_image[y][x]) begin
                        pixel_valid = 1;
                        pixel_in = 1;
                        pixel_x = x;
                        pixel_y = y;
                        @(posedge clk);
                    end
                end
            end
            
            pixel_valid = 0;
            pixel_in = 0;
            @(posedge clk);
        end
    endtask

    // Monitor output
    always @(posedge clk) begin
        if (line_valid) begin
            $display("[%0t ns] Line detected: Rho=%0d, Theta=%0d degrees, Votes=%0d", 
                     $time, line_rho, line_theta, line_votes);
        end
    end

    // Main test sequence
    initial begin
        $display("========================================");
        $display("Hough Transform ModelSim Testbench");
        $display("========================================");
        
        // Initialize signals
        rst_n = 0;
        pixel_valid = 0;
        pixel_in = 0;
        pixel_x = 0;
        pixel_y = 0;
        frame_start = 0;
        test_num = 0;
        
        // Reset pulse
        repeat(5) @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);

        //====================================
        // Test 1: Vertical Line at X=200
        //====================================
        test_num = 1;
        $display("\n[Test %0d] Vertical line at X=200", test_num);
        $display("Expected: Theta ~= 0-2 degrees, Rho ~= 200");
        clear_image();
        draw_vertical_line(200);
        send_frame();
        
        // Wait for processing
        repeat(30000) @(posedge clk);
        
        //====================================
        // Test 2: Horizontal Line at Y=240
        //====================================
        test_num = 2;
        $display("\n[Test %0d] Horizontal line at Y=240", test_num);
        $display("Expected: Theta ~= 90 degrees, Rho ~= 240");
        clear_image();
        draw_horizontal_line(240);
        send_frame();
        
        // Wait for processing
        repeat(30000) @(posedge clk);
        
        //====================================
        // Test 3: Diagonal Line (45 degrees)
        //====================================
        test_num = 3;
        $display("\n[Test %0d] Diagonal line at 45 degrees", test_num);
        $display("Expected: Theta ~= 44-46 degrees, Rho ~= 0-50");
        clear_image();
        draw_diagonal_line();
        send_frame();
        
        // Wait for processing
        repeat(50000) @(posedge clk);
        
        $display("\n========================================");
        $display("All tests completed!");
        $display("========================================");
        $finish;
    end

    // Timeout watchdog
    initial begin
        #200000000; // 200ms timeout
        $display("\nERROR: Simulation timeout!");
        $finish;
    end

endmodule
