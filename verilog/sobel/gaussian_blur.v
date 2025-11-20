//==============================================================================
// Module: gaussian_blur
// Description: Gaussian blur 3x3 Ä‘á»ƒ giáº£m noise trÆ°á»›c khi Sobel
//              Kernel: [1 2 1; 2 4 2; 1 2 1] / 16
// Author: Nguyá»…n VÄƒn Äáº¡t
// Date: 2025
// Target: Tang Nano 4K
//==============================================================================

module gaussian_blur #(
    parameter PIXEL_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire window_valid,
    input  wire [PIXEL_WIDTH*9-1:0] window_flat,
    
    output reg blur_valid,
    output reg [PIXEL_WIDTH*9-1:0] window_blurred
);

    // Extract 3x3 window
    wire [PIXEL_WIDTH-1:0] p00 = window_flat[PIXEL_WIDTH*0 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p01 = window_flat[PIXEL_WIDTH*1 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p02 = window_flat[PIXEL_WIDTH*2 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p10 = window_flat[PIXEL_WIDTH*3 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p11 = window_flat[PIXEL_WIDTH*4 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p12 = window_flat[PIXEL_WIDTH*5 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p20 = window_flat[PIXEL_WIDTH*6 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p21 = window_flat[PIXEL_WIDTH*7 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p22 = window_flat[PIXEL_WIDTH*8 +: PIXEL_WIDTH];

    // Apply Gaussian kernel (multiply by [1,2,1,2,4,2,1,2,1], then divide by 16)
    wire [PIXEL_WIDTH+3:0] sum = 
        p00 + (p01 << 1) + p02 +
        (p10 << 1) + (p11 << 2) + (p12 << 1) +
        p20 + (p21 << 1) + p22;
    
    wire [PIXEL_WIDTH-1:0] center_blurred = sum[PIXEL_WIDTH+3:4]; // Divide by 16 (>> 4)
    
    // Only blur center pixel, keep others unchanged for next stage
    wire [PIXEL_WIDTH-1:0] b00 = p00;
    wire [PIXEL_WIDTH-1:0] b01 = p01;
    wire [PIXEL_WIDTH-1:0] b02 = p02;
    wire [PIXEL_WIDTH-1:0] b10 = p10;
    wire [PIXEL_WIDTH-1:0] b11 = center_blurred; // Center pixel is blurred
    wire [PIXEL_WIDTH-1:0] b12 = p12;
    wire [PIXEL_WIDTH-1:0] b20 = p20;
    wire [PIXEL_WIDTH-1:0] b21 = p21;
    wire [PIXEL_WIDTH-1:0] b22 = p22;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            blur_valid <= 1'b0;
            window_blurred <= {(PIXEL_WIDTH*9){1'b0}};
        end else begin
            blur_valid <= window_valid;
            if (window_valid) begin
                window_blurred <= {b22, b21, b20, b12, b11, b10, b02, b01, b00};
            end
        end
    end

endmodule
