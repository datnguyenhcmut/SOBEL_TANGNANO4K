module sobel_kernel #(
    parameter PIXEL_WIDTH = 8,
    parameter SOBEL_WIDTH = 11
)(
    input  wire clk,
    input  wire rst_n,
    input  wire window_valid,
    input  wire [PIXEL_WIDTH*9-1:0] window_flat,
    output reg sobel_valid,
    output reg signed [SOBEL_WIDTH-1:0] gx_out,
    output reg signed [SOBEL_WIDTH-1:0] gy_out
);
    // Unpack flat window
    wire [PIXEL_WIDTH-1:0] p0 = window_flat[7:0];
    wire [PIXEL_WIDTH-1:0] p1 = window_flat[15:8];
    wire [PIXEL_WIDTH-1:0] p2 = window_flat[23:16];
    wire [PIXEL_WIDTH-1:0] p3 = window_flat[31:24];
    wire [PIXEL_WIDTH-1:0] p4 = window_flat[39:32];
    wire [PIXEL_WIDTH-1:0] p5 = window_flat[47:40];
    wire [PIXEL_WIDTH-1:0] p6 = window_flat[55:48];
    wire [PIXEL_WIDTH-1:0] p7 = window_flat[63:56];
    wire [PIXEL_WIDTH-1:0] p8 = window_flat[71:64];

    // Convert to signed
    wire signed [PIXEL_WIDTH:0] ps0 = {1'b0, p0};
    wire signed [PIXEL_WIDTH:0] ps1 = {1'b0, p1};
    wire signed [PIXEL_WIDTH:0] ps2 = {1'b0, p2};
    wire signed [PIXEL_WIDTH:0] ps3 = {1'b0, p3};
    wire signed [PIXEL_WIDTH:0] ps4 = {1'b0, p4};
    wire signed [PIXEL_WIDTH:0] ps5 = {1'b0, p5};
    wire signed [PIXEL_WIDTH:0] ps6 = {1'b0, p6};
    wire signed [PIXEL_WIDTH:0] ps7 = {1'b0, p7};
    wire signed [PIXEL_WIDTH:0] ps8 = {1'b0, p8};

    // Gx: [-1 0 1; -2 0 2; -1 0 1]
    wire signed [SOBEL_WIDTH-1:0] gx_result =
        -ps0 + ps2 - (ps3 <<< 1) + (ps5 <<< 1) - ps6 + ps8;

    // Gy: [-1 -2 -1; 0 0 0; 1 2 1]
    wire signed [SOBEL_WIDTH-1:0] gy_result =
        -ps0 - (ps1 <<< 1) - ps2 + ps6 + (ps7 <<< 1) + ps8;

    // Debug magnitude mirrors edge_mag stage to expose intermediate data
    wire [SOBEL_WIDTH-1:0] gx_abs_dbg = gx_result[SOBEL_WIDTH-1] ? (~gx_result + 1'b1) : gx_result;
    wire [SOBEL_WIDTH-1:0] gy_abs_dbg = gy_result[SOBEL_WIDTH-1] ? (~gy_result + 1'b1) : gy_result;
    wire [SOBEL_WIDTH:0] mag_sum_dbg = {1'b0, gx_abs_dbg} + {1'b0, gy_abs_dbg};
    wire mag_overflow_dbg = |mag_sum_dbg[SOBEL_WIDTH:PIXEL_WIDTH];
    wire [PIXEL_WIDTH-1:0] mag_sat_dbg = mag_overflow_dbg ? {PIXEL_WIDTH{1'b1}} : mag_sum_dbg[PIXEL_WIDTH-1:0];

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sobel_valid <= 1'b0;
            gx_out <= 0;
            gy_out <= 0;
        end else begin
            sobel_valid <= window_valid;
            gx_out <= gx_result;
            gy_out <= gy_result;

`ifndef SYNTHESIS
`ifdef TB_SOBEL_RANDOM
            if (window_valid &&
                tb_sobel_random.current_frame_id == 5 &&
                tb_sobel_random.dut.u_linebuf.row_count >= 88 &&
                tb_sobel_random.dut.u_linebuf.row_count <= 92 &&
                !tb_sobel_random.dut.u_linebuf.prefill_active) begin
                $display("[GRADDBG frame=%0d row=%0d col=%0d gx=%0h gy=%0h mag=%0h]",
                         tb_sobel_random.current_frame_id,
                         tb_sobel_random.dut.u_linebuf.row_count,
                         tb_sobel_random.dut.u_linebuf.col_addr,
                         gx_result,
                         gy_result,
                         mag_sat_dbg);
            end
`endif
`endif
        end
    end
endmodule
