//==============================================================================
// Module: binary_line_buffer
// Description: Line buffer for binary images (1-bit per pixel)
//              Used for morphological operations on binary edge maps
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
//==============================================================================

module binary_line_buffer #(
    parameter IMG_WIDTH = 640
)(
    input  wire clk,
    input  wire rst_n,
    input  wire pixel_valid,
    input  wire pixel_in,
    
    output reg window_valid,
    output reg [8:0] window_out  // 3x3 binary window
);

    // Two line buffers (each stores 1 row)
    reg line0 [0:IMG_WIDTH-1];
    reg line1 [0:IMG_WIDTH-1];
    
    // Window registers
    reg [2:0] row0, row1, row2;
    
    // Column counter
    reg [10:0] col_count;
    reg [9:0] row_count;
    
    integer i;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            col_count <= 0;
            row_count <= 0;
            window_valid <= 0;
            row0 <= 3'b0;
            row1 <= 3'b0;
            row2 <= 3'b0;
            for (i = 0; i < IMG_WIDTH; i = i + 1) begin
                line0[i] <= 0;
                line1[i] <= 0;
            end
        end else if (pixel_valid) begin
            // Shift window horizontally
            row0 <= {row0[1:0], line1[col_count]};
            row1 <= {row1[1:0], line0[col_count]};
            row2 <= {row2[1:0], pixel_in};
            
            // Update line buffers
            line1[col_count] <= line0[col_count];
            line0[col_count] <= pixel_in;
            
            // Column counter
            if (col_count == IMG_WIDTH - 1) begin
                col_count <= 0;
                row_count <= row_count + 1;
            end else begin
                col_count <= col_count + 1;
            end
            
            // Window valid after 2 rows + 2 columns
            window_valid <= (row_count >= 2) && (col_count >= 2);
        end
    end
    
    // Output 3x3 window
    always @(*) begin
        window_out = {row0, row1, row2};
    end

endmodule
