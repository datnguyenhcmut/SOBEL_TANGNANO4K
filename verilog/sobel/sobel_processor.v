module sobel_processor #(
    parameter IMG_WIDTH = 640,
    parameter IMG_HEIGHT = 480,
    parameter PIXEL_WIDTH = 8
)(
    input  wire clk,
    input  wire rst_n,
    input  wire href,
    input  wire vsync,
    input  wire [15:0] pixel_in,
    input  wire sobel_enable,
    output wire pixel_valid,
    output wire [15:0] pixel_out
);
    wire [PIXEL_WIDTH-1:0] gray_pixel;
    wire gray_valid;
    wire [PIXEL_WIDTH*9-1:0] window_flat;
    wire window_valid;
    wire signed [10:0] gx, gy;
    wire sobel_valid;
    wire [PIXEL_WIDTH-1:0] edge_magnitude;
    wire edge_valid;

    rgb_to_gray #(.USE_WEIGHTED(1)) u_rgb2gray (
        .clk(clk), .rst_n(rst_n), .pixel_valid(href),
        .rgb565_in(pixel_in), .gray_out(gray_pixel), .gray_valid(gray_valid)
    );

    line_buffer #(.IMG_WIDTH(IMG_WIDTH)) u_linebuf (
        .clk(clk), .rst_n(rst_n), .pixel_valid(gray_valid),
        .pixel_in(gray_pixel), .window_valid(window_valid), .window_out(window_flat)
    );

    sobel_kernel u_sobel (
        .clk(clk), .rst_n(rst_n), .window_valid(window_valid),
        .window_flat(window_flat), .sobel_valid(sobel_valid), .gx_out(gx), .gy_out(gy)
    );

    edge_mag u_magnitude (
        .clk(clk), .rst_n(rst_n), .sobel_valid(sobel_valid),
        .gx_in(gx), .gy_in(gy), .edge_valid(edge_valid), .edge_magnitude(edge_magnitude)
    );


    wire [15:0] sobel_rgb565 = {edge_magnitude[7:3], edge_magnitude[7:2], edge_magnitude[7:3]};

    assign pixel_valid = sobel_enable ? edge_valid : href;
    assign pixel_out = sobel_enable ? sobel_rgb565 : pixel_in;

`ifndef SYNTHESIS
`ifdef TB_SOBEL_RANDOM
    always @(posedge clk) begin
        if (tb_sobel_random.current_frame_id == 5 &&
            tb_sobel_random.dut.u_linebuf.row_count >= 88 &&
            tb_sobel_random.dut.u_linebuf.row_count <= 92 &&
            !tb_sobel_random.dut.u_linebuf.prefill_active) begin
            if (sobel_enable && edge_valid) begin
                $display("[PROCDBG frame=%0d row=%0d col=%0d mag=%0h rgb565=%0h sobel_en=%b]",
                         tb_sobel_random.current_frame_id,
                         tb_sobel_random.dut.u_linebuf.row_count,
                         tb_sobel_random.dut.u_linebuf.col_addr,
                         edge_magnitude,
                         sobel_rgb565,
                         sobel_enable);
            end

            if (pixel_valid) begin
                $display("[BOUNDDBG t=%0t frame=%0d row=%0d col=%0d sobel_rgb565=%0h pixel_out=%0h sobel_en=%b]",
                         $time,
                         tb_sobel_random.current_frame_id,
                         tb_sobel_random.dut.u_linebuf.row_count,
                         tb_sobel_random.dut.u_linebuf.col_addr,
                         sobel_rgb565,
                         pixel_out,
                         sobel_enable);
                $display("[MUXDBG t=%0t frame=%0d row=%0d col=%0d sobel_rgb=%0h bypass_rgb=%0h pixel_out=%0h sobel_en=%b edge_valid=%b pixel_valid=%b]",
                         $time,
                         tb_sobel_random.current_frame_id,
                         tb_sobel_random.dut.u_linebuf.row_count,
                         tb_sobel_random.dut.u_linebuf.col_addr,
                         sobel_rgb565,
                         pixel_in,
                         pixel_out,
                         sobel_enable,
                         edge_valid,
                         pixel_valid);
            end
        end
    end
`endif
`endif

endmodule
