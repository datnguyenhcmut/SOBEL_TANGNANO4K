//==============================================================================
// Module: noise_rejection_filter
// Description: Remove isolated noise pixels while preserving continuous edges
//              Uses simple neighbor counting - faster than morphological ops
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
//==============================================================================

module noise_rejection_filter (
    input  wire clk,
    input  wire rst_n,
    input  wire pixel_valid,
    input  wire pixel_in,
    
    output reg pixel_out,
    output reg pixel_out_valid
);

    // Shift register for 3 pixels horizontal (current row)
    reg [2:0] row_current;
    
    // Previous pixel outputs (for vertical checking)
    reg prev_out;
    reg prev_prev_out;
    
    // Combinational logic for neighbor detection
    wire has_horizontal;
    wire has_vertical;
    wire keep_pixel;
    
    assign has_horizontal = row_current[0] | row_current[2];  // left or right neighbor
    assign has_vertical = prev_out | prev_prev_out;            // recent outputs (vertical-ish)
    assign keep_pixel = row_current[1] && (has_horizontal || has_vertical);
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            row_current <= 3'b0;
            prev_out <= 1'b0;
            prev_prev_out <= 1'b0;
            pixel_out <= 1'b0;
            pixel_out_valid <= 1'b0;
        end else if (pixel_valid) begin
            // Shift horizontal window
            row_current <= {row_current[1:0], pixel_in};
            
            // Update output
            prev_prev_out <= prev_out;
            prev_out <= keep_pixel;
            pixel_out <= keep_pixel;
            pixel_out_valid <= pixel_valid;
        end
    end

endmodule
