//==============================================================================
// Module: edge_mag
// Description: TÃ­nh Ä‘á»™ lá»›n edge tá»« gradient Gx, Gy
//              Magnitude = |Gx| + |Gy| (Manhattan distance)
//              Scaling: chia 2, saturation vá» 255
// Author: Nguyá»…n VÄƒn Äáº¡t
// Date: 2025
// Target: Tang Nano 4K
//==============================================================================

module edge_mag #(
    parameter SOBEL_WIDTH = 11,
    parameter OUTPUT_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire sobel_valid,
    input  wire signed [SOBEL_WIDTH-1:0] gx_in,
    input  wire signed [SOBEL_WIDTH-1:0] gy_in,
    
    output reg edge_valid,
    output reg [OUTPUT_WIDTH-1:0] edge_magnitude
);

    wire [SOBEL_WIDTH-1:0] gx_abs = gx_in[SOBEL_WIDTH-1] ? (~gx_in + 1'b1) : gx_in;
    wire [SOBEL_WIDTH-1:0] gy_abs = gy_in[SOBEL_WIDTH-1] ? (~gy_in + 1'b1) : gy_in;
    wire [SOBEL_WIDTH:0] magnitude_sum = {1'b0, gx_abs} + {1'b0, gy_abs};
    wire [SOBEL_WIDTH:0] magnitude_scaled = magnitude_sum >> 1;
    wire [OUTPUT_WIDTH-1:0] magnitude_pre = magnitude_scaled[OUTPUT_WIDTH-1:0];
    wire [OUTPUT_WIDTH-1:0] max_value = {OUTPUT_WIDTH{1'b1}};
    wire [OUTPUT_WIDTH-1:0] magnitude_sat = (magnitude_scaled > max_value) ? max_value : magnitude_pre;
    
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            edge_valid <= 1'b0;
            edge_magnitude <= {OUTPUT_WIDTH{1'b0}};
        end else begin
            edge_valid <= sobel_valid;
            if (sobel_valid) begin
                edge_magnitude <= magnitude_sat;
// TB for video
// `ifndef SYNTHESIS
// `ifdef TB_SOBEL_RANDOM
//                 if (tb_sobel_random.current_frame_id == 5 &&
//                     tb_sobel_random.dut.u_linebuf.row_count >= 88 &&
//                     tb_sobel_random.dut.u_linebuf.row_count <= 92 &&
//                     tb_sobel_random.dut.u_linebuf.col_addr >= 1) begin
//                     $display("[GRADDBG frame=%0d row=%0d col=%0d gx=%0h gy=%0h mag=%0h]",
//                              tb_sobel_random.current_frame_id,
//                              tb_sobel_random.dut.u_linebuf.row_count,
//                              tb_sobel_random.dut.u_linebuf.col_addr,
//                              gx_in,
//                              gy_in,
//                              magnitude_sat);
//                     $display("[MAGDBG frame=%0d row=%0d col=%0d gx_abs=%0d gy_abs=%0d mag_raw=%0d mag_pre=%0d mag_sat=%0d]",
//                              tb_sobel_random.current_frame_id,
//                              tb_sobel_random.dut.u_linebuf.row_count,
//                              tb_sobel_random.dut.u_linebuf.col_addr,
//                              gx_abs,
//                              gy_abs,
//                              magnitude_sum,
//                              magnitude_pre,
//                              magnitude_sat);
//                 end
// `endif
// `endif
            end else begin
                edge_magnitude <= {OUTPUT_WIDTH{1'b0}};
            end
        end
    end

endmodule
