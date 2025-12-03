//==============================================================================
// Module: hough_transform
// Description: Real-time Hough Transform for line detection (optimized for FPGA)
//              Detects straight lines in binary edge images
//              Uses simplified voting scheme for low resource usage
// Author: Nguyễn Văn Đạt
// Date: 2025-12-02
// Target: Tang Nano 4K
//==============================================================================

module hough_transform #(
    parameter IMG_WIDTH = 640,
    parameter IMG_HEIGHT = 480,
    parameter RHO_RESOLUTION = 2,        // ρ resolution (pixels) - higher = less memory
    parameter THETA_STEPS = 90,          // Number of θ angles (0° to 180°)
    parameter ACCUMULATOR_BITS = 12,     // Max votes per bin
    parameter MIN_VOTES = 50             // Minimum votes to detect line
)(
    input  wire clk,
    input  wire rst_n,
    
    // Input: Binary edge pixels
    input  wire pixel_in,           // 1 = edge pixel, 0 = background
    input  wire pixel_valid,
    input  wire [9:0] pixel_x,      // Current X position (0-639)
    input  wire [9:0] pixel_y,      // Current Y position (0-479)
    input  wire frame_start,        // Pulse at start of new frame
    
    // Output: Detected lines (top N lines)
    output reg line_valid,
    output reg [15:0] line_rho,     // ρ value (distance from origin)
    output reg [7:0] line_theta,    // θ angle (0-179 degrees)
    output reg [ACCUMULATOR_BITS-1:0] line_votes  // Number of votes
);

    //==========================================================================
    // Constants
    //==========================================================================
    localparam MAX_RHO = ((IMG_WIDTH + IMG_HEIGHT) / RHO_RESOLUTION);
    localparam ADDR_BITS = $clog2(MAX_RHO * THETA_STEPS);
    
    // Pre-computed sin/cos lookup tables (Q8.8 fixed point)
    // θ from 0° to 179° in steps of 2° (90 values)
    reg signed [15:0] cos_lut [0:THETA_STEPS-1];
    reg signed [15:0] sin_lut [0:THETA_STEPS-1];
    
    //==========================================================================
    // State Machine
    //==========================================================================
    localparam STATE_ACCUMULATE = 2'd0;  // Voting phase (during frame)
    localparam STATE_FIND_PEAKS = 2'd1;  // Find top lines (between frames)
    localparam STATE_OUTPUT = 2'd2;      // Output detected lines
    
    reg [1:0] state;
    
    //==========================================================================
    // Accumulator Memory (Hough Space)
    // Size: MAX_RHO × THETA_STEPS bins
    //==========================================================================
    reg [ACCUMULATOR_BITS-1:0] accumulator [0:(MAX_RHO*THETA_STEPS-1)];
    
    //==========================================================================
    // Voting Logic
    //==========================================================================
    reg [7:0] theta_idx;
    reg [15:0] rho_calc;
    reg [ADDR_BITS-1:0] bin_addr;
    reg vote_enable;
    
    // Initialize sin/cos lookup tables - size depends on THETA_STEPS parameter
    integer i;
    initial begin
        // Generate lookup table based on THETA_STEPS
        // Angle step = 180° / THETA_STEPS
        // For THETA_STEPS=45: 0°, 4°, 8°, ..., 176°
        // For THETA_STEPS=90: 0°, 2°, 4°, ..., 178°
        for (i = 0; i < THETA_STEPS; i = i + 1) begin
            // Calculate angle in radians: angle = i * 180 / THETA_STEPS
            // Using fixed-point approximation for cos/sin
            // Q8.8 format: multiply by 256
            case (i % 45)  // Base pattern for 0-44 (0°-176° in 4° steps)
                0:  begin cos_lut[i] = 16'd256;   sin_lut[i] = 16'd0;     end  // 0°
                1:  begin cos_lut[i] = 16'd255;   sin_lut[i] = 16'd18;    end  // 4°
                2:  begin cos_lut[i] = 16'd253;   sin_lut[i] = 16'd36;    end  // 8°
                3:  begin cos_lut[i] = 16'd249;   sin_lut[i] = 16'd53;    end  // 12°
                4:  begin cos_lut[i] = 16'd243;   sin_lut[i] = 16'd70;    end  // 16°
                5:  begin cos_lut[i] = 16'd236;   sin_lut[i] = 16'd87;    end  // 20°
                6:  begin cos_lut[i] = 16'd228;   sin_lut[i] = 16'd103;   end  // 24°
                7:  begin cos_lut[i] = 16'd218;   sin_lut[i] = 16'd119;   end  // 28°
                8:  begin cos_lut[i] = 16'd208;   sin_lut[i] = 16'd135;   end  // 32°
                9:  begin cos_lut[i] = 16'd196;   sin_lut[i] = 16'd150;   end  // 36°
                10: begin cos_lut[i] = 16'd184;   sin_lut[i] = 16'd164;   end  // 40°
                11: begin cos_lut[i] = 16'd171;   sin_lut[i] = 16'd177;   end  // 44°
                12: begin cos_lut[i] = 16'd157;   sin_lut[i] = 16'd190;   end  // 48°
                13: begin cos_lut[i] = 16'd142;   sin_lut[i] = 16'd202;   end  // 52°
                14: begin cos_lut[i] = 16'd127;   sin_lut[i] = 16'd213;   end  // 56°
                15: begin cos_lut[i] = 16'd111;   sin_lut[i] = 16'd223;   end  // 60°
                16: begin cos_lut[i] = 16'd95;    sin_lut[i] = 16'd232;   end  // 64°
                17: begin cos_lut[i] = 16'd78;    sin_lut[i] = 16'd240;   end  // 68°
                18: begin cos_lut[i] = 16'd61;    sin_lut[i] = 16'd246;   end  // 72°
                19: begin cos_lut[i] = 16'd44;    sin_lut[i] = 16'd251;   end  // 76°
                20: begin cos_lut[i] = 16'd27;    sin_lut[i] = 16'd254;   end  // 80°
                21: begin cos_lut[i] = 16'd9;     sin_lut[i] = 16'd256;   end  // 84°
                22: begin cos_lut[i] = -16'd9;    sin_lut[i] = 16'd256;   end  // 88°
                23: begin cos_lut[i] = -16'd27;   sin_lut[i] = 16'd254;   end  // 92°
                24: begin cos_lut[i] = -16'd44;   sin_lut[i] = 16'd251;   end  // 96°
                25: begin cos_lut[i] = -16'd61;   sin_lut[i] = 16'd246;   end  // 100°
                26: begin cos_lut[i] = -16'd78;   sin_lut[i] = 16'd240;   end  // 104°
                27: begin cos_lut[i] = -16'd95;   sin_lut[i] = 16'd232;   end  // 108°
                28: begin cos_lut[i] = -16'd111;  sin_lut[i] = 16'd223;   end  // 112°
                29: begin cos_lut[i] = -16'd127;  sin_lut[i] = 16'd213;   end  // 116°
                30: begin cos_lut[i] = -16'd142;  sin_lut[i] = 16'd202;   end  // 120°
                31: begin cos_lut[i] = -16'd157;  sin_lut[i] = 16'd190;   end  // 124°
                32: begin cos_lut[i] = -16'd171;  sin_lut[i] = 16'd177;   end  // 128°
                33: begin cos_lut[i] = -16'd184;  sin_lut[i] = 16'd164;   end  // 132°
                34: begin cos_lut[i] = -16'd196;  sin_lut[i] = 16'd150;   end  // 136°
                35: begin cos_lut[i] = -16'd208;  sin_lut[i] = 16'd135;   end  // 140°
                36: begin cos_lut[i] = -16'd218;  sin_lut[i] = 16'd119;   end  // 144°
                37: begin cos_lut[i] = -16'd228;  sin_lut[i] = 16'd103;   end  // 148°
                38: begin cos_lut[i] = -16'd236;  sin_lut[i] = 16'd87;    end  // 152°
                39: begin cos_lut[i] = -16'd243;  sin_lut[i] = 16'd70;    end  // 156°
                40: begin cos_lut[i] = -16'd249;  sin_lut[i] = 16'd53;    end  // 160°
                41: begin cos_lut[i] = -16'd253;  sin_lut[i] = 16'd36;    end  // 164°
                42: begin cos_lut[i] = -16'd255;  sin_lut[i] = 16'd18;    end  // 168°
                43: begin cos_lut[i] = -16'd256;  sin_lut[i] = 16'd0;     end  // 172°
                44: begin cos_lut[i] = -16'd255;  sin_lut[i] = -16'd18;   end  // 176°
                default: begin cos_lut[i] = 16'd0; sin_lut[i] = 16'd0; end
            endcase
        end
    end
    
    //==========================================================================
    // Main State Machine
    //==========================================================================
    reg [7:0] vote_theta;
    reg vote_busy;
    reg signed [31:0] rho_temp;
    
    // Peak detection
    reg [ADDR_BITS-1:0] search_addr;
    reg [ACCUMULATOR_BITS-1:0] max_votes;
    reg [ADDR_BITS-1:0] max_addr;
    
    // Clear accumulator state
    reg clearing;
    reg [ADDR_BITS-1:0] clear_addr;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= STATE_ACCUMULATE;
            theta_idx <= 0;
            vote_enable <= 0;
            vote_busy <= 0;
            line_valid <= 0;
            search_addr <= 0;
            max_votes <= 0;
            max_addr <= 0;
            clearing <= 1;
            clear_addr <= 0;
        end else begin
            // Clear accumulator incrementally (to avoid loop limit)
            if (clearing) begin
                accumulator[clear_addr] <= 0;
                if (clear_addr < (MAX_RHO * THETA_STEPS - 1)) begin
                    clear_addr <= clear_addr + 1;
                end else begin
                    clearing <= 0;
                end
            end
            
            // State machine
            else case (state)
                STATE_ACCUMULATE: begin
                    line_valid <= 0;
                    
                    // Start clearing accumulator at frame start
                    if (frame_start) begin
                        clearing <= 1;
                        clear_addr <= 0;
                        vote_busy <= 0;
                        theta_idx <= 0;
                    end
                    
                    // Process edge pixel
                    else if (pixel_valid && pixel_in && !vote_busy) begin
                        vote_busy <= 1;
                        vote_theta <= 0;
                    end
                    
                    // Vote for all theta angles
                    else if (vote_busy) begin
                        if (vote_theta < THETA_STEPS) begin
                            // Calculate ρ = x·cos(θ) + y·sin(θ)
                            // Using Q8.8 fixed point: divide by 256
                            rho_temp = ($signed(pixel_x) * cos_lut[vote_theta] + 
                                       $signed(pixel_y) * sin_lut[vote_theta]) >>> 8;
                            
                            // Convert to bin index (handle negative ρ)
                            if (rho_temp >= 0) begin
                                rho_calc = rho_temp[15:0] / RHO_RESOLUTION;
                            end else begin
                                rho_calc = (MAX_RHO/2) - ((-rho_temp[15:0]) / RHO_RESOLUTION);
                            end
                            
                            // Calculate bin address
                            bin_addr = (rho_calc * THETA_STEPS) + vote_theta;
                            
                            // Increment vote (with saturation)
                            if (bin_addr < (MAX_RHO * THETA_STEPS)) begin
                                if (accumulator[bin_addr] < {ACCUMULATOR_BITS{1'b1}}) begin
                                    accumulator[bin_addr] <= accumulator[bin_addr] + 1;
                                end
                            end
                            
                            vote_theta <= vote_theta + 1;
                        end else begin
                            vote_busy <= 0;
                        end
                    end
                end
                
                STATE_FIND_PEAKS: begin
                    // Search through accumulator to find maximum
                    if (search_addr < (MAX_RHO * THETA_STEPS)) begin
                        if (accumulator[search_addr] > max_votes) begin
                            max_votes <= accumulator[search_addr];
                            max_addr <= search_addr;
                        end
                        search_addr <= search_addr + 1;
                    end else begin
                        // Search complete, check if valid line found
                        if (max_votes >= MIN_VOTES) begin
                            state <= STATE_OUTPUT;
                        end else begin
                            line_valid <= 0;
                            state <= STATE_ACCUMULATE;
                        end
                    end
                end
                
                STATE_OUTPUT: begin
                    // Decode max_addr back to rho and theta
                    line_theta <= max_addr % THETA_STEPS;
                    line_rho <= (max_addr / THETA_STEPS) * RHO_RESOLUTION;
                    line_votes <= max_votes;
                    line_valid <= 1;
                    
                    // Reset for next frame
                    max_votes <= 0;
                    search_addr <= 0;
                    state <= STATE_ACCUMULATE;
                end
            endcase  // end case(state)
        end  // end else (not clearing)
    end  // end always

endmodule
