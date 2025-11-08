`timescale 1ns / 1ps

module tb_sobel_processor;
    parameter CLK_PERIOD = 40;
    reg clk, rst_n, href, vsync;
    reg [15:0] pixel_in;
    reg sobel_enable;
    wire pixel_valid;
    wire [15:0] pixel_out;
    integer i, j;
    
    initial begin
        clk = 0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    sobel_processor #(.IMG_WIDTH(640), .IMG_HEIGHT(480), .PIXEL_WIDTH(8)) dut (
        .clk(clk), .rst_n(rst_n), .href(href), .vsync(vsync),
        .pixel_in(pixel_in), .sobel_enable(sobel_enable),
        .pixel_valid(pixel_valid), .pixel_out(pixel_out)
    );
    
    initial begin
        $dumpfile("sobel_wave.vcd");
        $dumpvars(0, tb_sobel_processor);
        $display("=== Sobel Processor Test ===");
        
        rst_n = 0; href = 0; vsync = 0; pixel_in = 0; sobel_enable = 1;
        #(CLK_PERIOD*10);
        rst_n = 1;
        #(CLK_PERIOD*5);
        
        $display("[TEST 1] Vertical Edge Pattern");
        vsync = 1; #(CLK_PERIOD*2); vsync = 0;
        
        for (i = 0; i < 5; i = i + 1) begin
            for (j = 0; j < 20; j = j + 1) begin
                href = 1;
                pixel_in = (j < 10) ? 16'h0000 : 16'hFFFF;
                #CLK_PERIOD;
            end
            href = 0;
            #(CLK_PERIOD*2);
        end
        
        $display("Waiting for Sobel output...");
        #(CLK_PERIOD*200);
        
        $display("[TEST 2] Bypass Mode");
        sobel_enable = 0;
        href = 1;
        pixel_in = 16'hA5A5;
        #(CLK_PERIOD*5);
        
        if (pixel_out == 16'hA5A5)
            $display("PASS: Bypass mode works");
        else
            $display("FAIL: Bypass expected A5A5, got %h", pixel_out);
        
        $display("=== Test Complete ===");
        #(CLK_PERIOD*50);
        $finish;
    end
    
    always @(posedge clk) begin
        if (pixel_valid)
            $display("[%0t] Valid output: %h", $time, pixel_out);
    end
    
endmodule
