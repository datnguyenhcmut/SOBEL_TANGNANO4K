//==============================================================================
// Module: bilateral_filter
// Description: Edge-preserving bilateral filter for noise reduction
//              Combines spatial distance AND intensity similarity
//              Better than Gaussian for preserving edges while removing noise
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
// Target: Tang Nano 4K
//==============================================================================

module bilateral_filter #(
    parameter PIXEL_WIDTH = 8,
    parameter SIGMA_SPATIAL = 2,    // Spatial kernel width (smaller = sharper)
    parameter SIGMA_RANGE = 20      // LOWERED: Sharper, less smoothing, reduce sensor noise (was 30)
)(
    input  wire clk,
    input  wire rst_n,
    input  wire window_valid,
    input  wire [PIXEL_WIDTH*9-1:0] window_flat,
    
    output reg filter_valid,
    output reg [PIXEL_WIDTH*9-1:0] window_filtered
);

    // Extract 3x3 window
    wire [PIXEL_WIDTH-1:0] p00 = window_flat[PIXEL_WIDTH*0 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p01 = window_flat[PIXEL_WIDTH*1 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p02 = window_flat[PIXEL_WIDTH*2 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p10 = window_flat[PIXEL_WIDTH*3 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p11 = window_flat[PIXEL_WIDTH*4 +: PIXEL_WIDTH]; // Center
    wire [PIXEL_WIDTH-1:0] p12 = window_flat[PIXEL_WIDTH*5 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p20 = window_flat[PIXEL_WIDTH*6 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p21 = window_flat[PIXEL_WIDTH*7 +: PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] p22 = window_flat[PIXEL_WIDTH*8 +: PIXEL_WIDTH];

    // Compute intensity differences from center pixel
    wire signed [PIXEL_WIDTH:0] diff00 = p11 - p00;
    wire signed [PIXEL_WIDTH:0] diff01 = p11 - p01;
    wire signed [PIXEL_WIDTH:0] diff02 = p11 - p02;
    wire signed [PIXEL_WIDTH:0] diff10 = p11 - p10;
    wire signed [PIXEL_WIDTH:0] diff12 = p11 - p12;
    wire signed [PIXEL_WIDTH:0] diff20 = p11 - p20;
    wire signed [PIXEL_WIDTH:0] diff21 = p11 - p21;
    wire signed [PIXEL_WIDTH:0] diff22 = p11 - p22;

    // Absolute differences
    wire [PIXEL_WIDTH-1:0] abs_diff00 = (diff00[PIXEL_WIDTH]) ? -diff00 : diff00;
    wire [PIXEL_WIDTH-1:0] abs_diff01 = (diff01[PIXEL_WIDTH]) ? -diff01 : diff01;
    wire [PIXEL_WIDTH-1:0] abs_diff02 = (diff02[PIXEL_WIDTH]) ? -diff02 : diff02;
    wire [PIXEL_WIDTH-1:0] abs_diff10 = (diff10[PIXEL_WIDTH]) ? -diff10 : diff10;
    wire [PIXEL_WIDTH-1:0] abs_diff12 = (diff12[PIXEL_WIDTH]) ? -diff12 : diff12;
    wire [PIXEL_WIDTH-1:0] abs_diff20 = (diff20[PIXEL_WIDTH]) ? -diff20 : diff20;
    wire [PIXEL_WIDTH-1:0] abs_diff21 = (diff21[PIXEL_WIDTH]) ? -diff21 : diff21;
    wire [PIXEL_WIDTH-1:0] abs_diff22 = (diff22[PIXEL_WIDTH]) ? -diff22 : diff22;

    // Simplified bilateral weights:
    // - If intensity difference < SIGMA_RANGE: weight = spatial_weight
    // - If intensity difference >= SIGMA_RANGE: weight = 0 (reject, likely edge)
    //
    // Spatial weights for 3x3 (distance-based):
    // [1 2 1]   Corner: weight=1, Edge: weight=2, Center: weight=4
    // [2 4 2]
    // [1 2 1]

    // Compute effective weights (spatial * range_similarity)
    wire [2:0] w00 = (abs_diff00 < SIGMA_RANGE) ? 3'd1 : 3'd0;
    wire [2:0] w01 = (abs_diff01 < SIGMA_RANGE) ? 3'd2 : 3'd0;
    wire [2:0] w02 = (abs_diff02 < SIGMA_RANGE) ? 3'd1 : 3'd0;
    wire [2:0] w10 = (abs_diff10 < SIGMA_RANGE) ? 3'd2 : 3'd0;
    wire [2:0] w11 = 3'd4; // Center always included
    wire [2:0] w12 = (abs_diff12 < SIGMA_RANGE) ? 3'd2 : 3'd0;
    wire [2:0] w20 = (abs_diff20 < SIGMA_RANGE) ? 3'd1 : 3'd0;
    wire [2:0] w21 = (abs_diff21 < SIGMA_RANGE) ? 3'd2 : 3'd0;
    wire [2:0] w22 = (abs_diff22 < SIGMA_RANGE) ? 3'd1 : 3'd0;

    // Weighted sum
    wire [PIXEL_WIDTH+7:0] weighted_sum = 
        (p00 * w00) + (p01 * w01) + (p02 * w02) +
        (p10 * w10) + (p11 * w11) + (p12 * w12) +
        (p20 * w20) + (p21 * w21) + (p22 * w22);

    // Sum of weights (for normalization)
    wire [4:0] weight_sum = w00 + w01 + w02 + w10 + w11 + w12 + w20 + w21 + w22;

    // Normalized output (prevent division by zero)
    wire [PIXEL_WIDTH-1:0] center_filtered = 
        (weight_sum > 0) ? (weighted_sum / weight_sum) : p11;

    // Only filter center pixel, keep others unchanged
    wire [PIXEL_WIDTH-1:0] f00 = p00;
    wire [PIXEL_WIDTH-1:0] f01 = p01;
    wire [PIXEL_WIDTH-1:0] f02 = p02;
    wire [PIXEL_WIDTH-1:0] f10 = p10;
    wire [PIXEL_WIDTH-1:0] f11 = center_filtered;
    wire [PIXEL_WIDTH-1:0] f12 = p12;
    wire [PIXEL_WIDTH-1:0] f20 = p20;
    wire [PIXEL_WIDTH-1:0] f21 = p21;
    wire [PIXEL_WIDTH-1:0] f22 = p22;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            filter_valid <= 1'b0;
            window_filtered <= {(PIXEL_WIDTH*9){1'b0}};
        end else begin
            filter_valid <= window_valid;
            if (window_valid) begin
                window_filtered <= {f22, f21, f20, f12, f11, f10, f02, f01, f00};
            end
        end
    end

endmodule
