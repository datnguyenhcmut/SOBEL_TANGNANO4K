`timescale 1ns/1ps

// Golden-vector testbench: feeds precomputed frame and compares against expected outputs
module tb_sobel_golden_fix;
    // Parameters (must match generator script)
    localparam CLK_PERIOD = 40; // 25 MHz
    localparam IMG_WIDTH  = 64;
    localparam IMG_HEIGHT = 48;
    localparam EXPECTED_COUNT = (IMG_HEIGHT-2)*(IMG_WIDTH-1);

    // DUT I/O
    reg clk, rst_n, href, vsync;
    reg [15:0] pixel_in;
    reg sobel_enable;
    wire pixel_valid;
    wire [15:0] pixel_out;

    // Memories
    reg [15:0] in_mem [0:IMG_WIDTH*IMG_HEIGHT-1];
    reg [15:0] exp_mem [0:EXPECTED_COUNT-1];
    integer in_idx;
    integer exp_idx;
    integer mismatches;
    integer x, y;

    // DUT
    sobel_processor #(.IMG_WIDTH(IMG_WIDTH), .IMG_HEIGHT(IMG_HEIGHT), .PIXEL_WIDTH(8)) dut (
        .clk(clk), .rst_n(rst_n), .href(href), .vsync(vsync),
        .pixel_in(pixel_in), .sobel_enable(sobel_enable),
        .pixel_valid(pixel_valid), .pixel_out(pixel_out)
    );

    // Clock
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // Stimulus
    initial begin
        $dumpfile("sobel_wave.vcd");
        $dumpvars(0, tb_sobel_golden_fix);
        $display("=== tb_sobel_golden_fix: Golden-vector check ===");

        // Load vectors
        $readmemh("golden/input_rgb565.mem", in_mem);
        $readmemh("golden/expected_output.mem", exp_mem);

        // Init
        rst_n = 0; href = 0; vsync = 0; pixel_in = 16'h0; sobel_enable = 1;
        in_idx = 0; exp_idx = 0; mismatches = 0;
        #(CLK_PERIOD*10); rst_n = 1; #(CLK_PERIOD*5);

        // Frame start pulse (vsync not used internally, but keep for completeness)
        vsync = 1; #(CLK_PERIOD*2); vsync = 0;

        // Stream the frame line by line
        for (y = 0; y < IMG_HEIGHT; y = y + 1) begin
            href = 1;
            for (x = 0; x < IMG_WIDTH; x = x + 1) begin
                pixel_in = in_mem[in_idx];
                in_idx = in_idx + 1;
                #CLK_PERIOD;
            end
            href = 0;
            #(CLK_PERIOD*2);
        end

        // Drain
        #(CLK_PERIOD*200);

        // Result
        if (mismatches == 0 && exp_idx == EXPECTED_COUNT) begin
            $display("PASS: Golden-vector check matched all %0d outputs.", EXPECTED_COUNT);
        end else begin
            $display("FAIL: mismatches=%0d, consumed=%0d / %0d expected.", mismatches, exp_idx, EXPECTED_COUNT);
        end
        #(CLK_PERIOD*20);
        $finish;
    end

    // Compare at pixel_valid
    always @(posedge clk) begin
        if (rst_n && pixel_valid) begin
            if (exp_idx < EXPECTED_COUNT) begin
                if (pixel_out !== exp_mem[exp_idx]) begin
                    $display("[MISMATCH t=%0t] got=%h exp=%h (idx=%0d)", $time, pixel_out, exp_mem[exp_idx], exp_idx);
                    mismatches = mismatches + 1;
                end
                exp_idx = exp_idx + 1;
            end else begin
                $display("[WARN] More outputs than expected at t=%0t: got %h", $time, pixel_out);
                mismatches = mismatches + 1;
            end
        end
    end

endmodule
