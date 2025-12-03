//==============================================================================
// Module: morphological_filter
// Description: Morphological operations to clean binary edge maps
//              - DILATION: Thicken edges, fill small gaps
//              - EROSION: Remove isolated noise pixels
//              - CLOSING: Dilation then Erosion (best for lanes)
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
//==============================================================================

module morphological_filter #(
    parameter OPERATION = 2  // 0=erosion, 1=dilation, 2=closing (dilation+erosion)
)(
    input  wire clk,
    input  wire rst_n,
    input  wire window_valid,
    input  wire [8:0] binary_window,  // 3x3 binary window (0 or 1)
    
    output reg filtered_pixel,
    output reg filtered_valid
);

    // Extract 3x3 window
    wire p00 = binary_window[0];
    wire p01 = binary_window[1];
    wire p02 = binary_window[2];
    wire p10 = binary_window[3];
    wire p11 = binary_window[4];  // Center pixel
    wire p12 = binary_window[5];
    wire p20 = binary_window[6];
    wire p21 = binary_window[7];
    wire p22 = binary_window[8];

    // Count neighbors (8-connectivity)
    wire [3:0] neighbor_count = p00 + p01 + p02 + p10 + p12 + p20 + p21 + p22;
    
    // Check if any neighbor is set (for dilation)
    wire any_neighbor = (neighbor_count > 0);

    // Morphological operations
    wire eroded_pixel;
    wire dilated_pixel;
    
    // EROSION: Keep pixel only if it has enough neighbors (removes noise)
    // Use 2+ neighbors to remove isolated dots while keeping lines
    assign eroded_pixel = p11 && (neighbor_count >= 2);
    
    // DILATION: Set pixel if center OR any neighbor is set (thickens edges)
    assign dilated_pixel = p11 || any_neighbor;
    
    // CLOSING = Dilation followed by Erosion (done in 2 stages with line buffer)
    // Here we do single-pass approximation:
    // - If center is set and has strong neighborhood → keep
    // - If center is off but has many neighbors → set (fill gaps)
    wire closing_pixel = (p11 && (neighbor_count >= 1)) || 
                         (!p11 && (neighbor_count >= 4));

    // Select operation
    wire result_pixel;
    generate
        if (OPERATION == 0) begin
            assign result_pixel = eroded_pixel;
        end else if (OPERATION == 1) begin
            assign result_pixel = dilated_pixel;
        end else begin
            assign result_pixel = closing_pixel;
        end
    endgenerate

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            filtered_pixel <= 1'b0;
            filtered_valid <= 1'b0;
        end else begin
            filtered_valid <= window_valid;
            filtered_pixel <= result_pixel;
        end
    end

endmodule
