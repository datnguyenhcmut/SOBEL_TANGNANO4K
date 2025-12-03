//==============================================================================
// Module: lane_detector
// Description: Simplified lane detection using region-based line finding
//              Optimized for real-time FPGA implementation
//              Detects left and right lane lines
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
// Target: Tang Nano 4K
//==============================================================================

module lane_detector #(
    parameter IMG_WIDTH = 640,
    parameter IMG_HEIGHT = 480,
    parameter ROI_TOP = 240,           // Region of interest top (ignore sky)
    parameter ROI_BOTTOM = 460         // Region of interest bottom
)(
    input  wire clk,
    input  wire rst_n,
    
    // Input: Binary edge pixels
    input  wire pixel_in,              // 1 = edge, 0 = background
    input  wire pixel_valid,
    input  wire [9:0] pixel_x,
    input  wire [9:0] pixel_y,
    input  wire frame_start,
    
    // Output: Lane line parameters
    output reg left_lane_valid,
    output reg [9:0] left_x_top,       // X coordinate at ROI_TOP
    output reg [9:0] left_x_bottom,    // X coordinate at ROI_BOTTOM
    
    output reg right_lane_valid,
    output reg [9:0] right_x_top,
    output reg [9:0] right_x_bottom,
    
    output reg detection_done          // Pulse when detection complete
);

    //==========================================================================
    // Region Division: Split into left and right halves
    //==========================================================================
    localparam MIDDLE_X = IMG_WIDTH / 2;
    
    //==========================================================================
    // Line Accumulators: Count edge pixels at different Y positions
    //==========================================================================
    reg [11:0] left_acc_top;      // Left region, top half
    reg [11:0] left_acc_bottom;   // Left region, bottom half
    reg [9:0] left_x_sum_top;
    reg [9:0] left_x_sum_bottom;
    
    reg [11:0] right_acc_top;
    reg [11:0] right_acc_bottom;
    reg [9:0] right_x_sum_top;
    reg [9:0] right_x_sum_bottom;
    
    wire in_roi = (pixel_y >= ROI_TOP) && (pixel_y <= ROI_BOTTOM);
    wire in_top_half = (pixel_y >= ROI_TOP) && (pixel_y < ((ROI_TOP + ROI_BOTTOM) / 2));
    wire in_bottom_half = (pixel_y >= ((ROI_TOP + ROI_BOTTOM) / 2)) && (pixel_y <= ROI_BOTTOM);
    
    //==========================================================================
    // Accumulation Phase
    //==========================================================================
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            left_acc_top <= 0;
            left_acc_bottom <= 0;
            left_x_sum_top <= 0;
            left_x_sum_bottom <= 0;
            right_acc_top <= 0;
            right_acc_bottom <= 0;
            right_x_sum_top <= 0;
            right_x_sum_bottom <= 0;
            detection_done <= 0;
        end else begin
            // Clear at frame start
            if (frame_start) begin
                left_acc_top <= 0;
                left_acc_bottom <= 0;
                left_x_sum_top <= 0;
                left_x_sum_bottom <= 0;
                right_acc_top <= 0;
                right_acc_bottom <= 0;
                right_x_sum_top <= 0;
                right_x_sum_bottom <= 0;
                detection_done <= 0;
            end
            
            // Accumulate edge pixels in ROI
            else if (pixel_valid && pixel_in && in_roi) begin
                // Left region
                if (pixel_x < MIDDLE_X) begin
                    if (in_top_half) begin
                        left_acc_top <= left_acc_top + 1;
                        left_x_sum_top <= left_x_sum_top + pixel_x;
                    end else if (in_bottom_half) begin
                        left_acc_bottom <= left_acc_bottom + 1;
                        left_x_sum_bottom <= left_x_sum_bottom + pixel_x;
                    end
                end
                // Right region
                else begin
                    if (in_top_half) begin
                        right_acc_top <= right_acc_top + 1;
                        right_x_sum_top <= right_x_sum_top + pixel_x;
                    end else if (in_bottom_half) begin
                        right_acc_bottom <= right_acc_bottom + 1;
                        right_x_sum_bottom <= right_x_sum_bottom + pixel_x;
                    end
                end
            end
            
            // Detection complete at end of frame (last row)
            else if (pixel_valid && pixel_y == (IMG_HEIGHT - 1) && pixel_x == (IMG_WIDTH - 1)) begin
                detection_done <= 1;
                
                // Calculate average X positions (simple division)
                // Left lane - LOWERED threshold from 10 to 3
                if (left_acc_top > 3) begin
                    left_lane_valid <= 1;
                    left_x_top <= left_x_sum_top / left_acc_top[9:0];
                    left_x_bottom <= left_x_sum_bottom / left_acc_bottom[9:0];
                end else begin
                    left_lane_valid <= 0;
                end
                
                // Right lane - LOWERED threshold from 10 to 3
                if (right_acc_top > 3) begin
                    right_lane_valid <= 1;
                    right_x_top <= right_x_sum_top / right_acc_top[9:0];
                    right_x_bottom <= right_x_sum_bottom / right_acc_bottom[9:0];
                end else begin
                    right_lane_valid <= 0;
                end
            end else begin
                detection_done <= 0;
            end
        end
    end

endmodule
