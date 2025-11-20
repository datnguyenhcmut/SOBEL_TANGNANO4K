//==============================================================================
// Module: rgb_to_gray
// Description: Chuyá»ƒn Ä‘á»•i RGB565 sang áº£nh xÃ¡m (Grayscale) 8-bit
//              Module nÃ y há»— trá»£ 2 phÆ°Æ¡ng phÃ¡p:
//              - Simple averaging: (R+G+B)/4 - nhanh, Ã­t resource
//              - Weighted averaging: 0.299R + 0.587G + 0.114B - chÃ­nh xÃ¡c hÆ¡n
//              ÄÆ°á»£c tá»‘i Æ°u hÃ³a cho FPGA Tang Nano 4K
// 
// Author: nguyen van dat
// Date: 2025
// Target: Tang Nano 4K (Gowin GW1NSR-LV4C)
//
// Parameters:
//   - USE_WEIGHTED: 0 = simple avg, 1 = weighted avg (ITU-R BT.601)
//
// Pipeline: 1 clock cycle latency
//==============================================================================

module rgb_to_gray (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        pixel_valid,
    input  wire [15:0] rgb565_in,     // RGB565: {R[4:0], G[5:0], B[4:0]}
    
    output reg         gray_valid,
    output reg  [7:0]  gray_out
);

    // Extract RGB components tá»« RGB565
    wire [7:0] red   = {rgb565_in[15:11], rgb565_in[15:13]};  // 5â†’8 bit expansion
    wire [7:0] green = {rgb565_in[10:5], rgb565_in[10:9]};   // 6â†’8 bit expansion  
    wire [7:0] blue  = {rgb565_in[4:0], rgb565_in[4:2]};     // 5â†’8 bit expansion
    
    // Method 1: Simple averaging (fastest)
    wire [9:0] simple_avg = red + green + blue;
    wire [7:0] gray_simple = simple_avg[9:2];  // Divide by 4 (close to /3)
    
    // Method 2: Weighted averaging (more accurate)
    // Y = 0.299*R + 0.587*G + 0.114*B
    // Approximated as: Y = (77*R + 151*G + 28*B) >> 8
    wire [15:0] red_weighted   = red * 77;    // 8bit Ã— 77 = 14bit max
    wire [15:0] green_weighted = green * 151; // 8bit Ã— 151 = 15bit max  
    wire [15:0] blue_weighted  = blue * 28;   // 8bit Ã— 28 = 13bit max
    wire [17:0] weighted_sum   = red_weighted + green_weighted + blue_weighted;
    wire [7:0]  gray_weighted  = weighted_sum[15:8];  // >> 8
    
    // Selection parameter - change nÃ y Ä‘á»ƒ switch methods
    parameter USE_WEIGHTED = 1;  // 0: simple, 1: weighted
    
    wire [7:0] gray_result = USE_WEIGHTED ? gray_weighted : gray_simple;
    
    // Pipeline register
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            gray_valid <= 1'b0;
            gray_out <= 8'd0;
        end else begin
            gray_valid <= pixel_valid;
            gray_out <= gray_result;
        end
    end

endmodule