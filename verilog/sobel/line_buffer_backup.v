module line_buffer #(
    parameter IMG_WIDTH   = 640,
    parameter PIXEL_WIDTH = 8,
    parameter ADDR_WIDTH  = 10
)(
    input  wire                     clk,
    input  wire                     rst_n,
    input  wire                     pixel_valid,
    input  wire [PIXEL_WIDTH-1:0]   pixel_in,
    output wire                     window_valid,
    output wire [PIXEL_WIDTH*9-1:0] window_out
);
    // Address tracking - simplified
    reg [ADDR_WIDTH-1:0] col_addr;
    reg [ADDR_WIDTH-1:0] row_count;

    // Pipeline for BRAM 2-cycle read latency
    reg pixel_valid_d1, pixel_valid_d2;
    reg [ADDR_WIDTH-1:0] col_addr_d1, col_addr_d2;
    reg [ADDR_WIDTH-1:0] row_count_d1, row_count_d2;

    // Current row pixel pipeline
    reg [PIXEL_WIDTH-1:0] pixel_in_d1;
    reg [PIXEL_WIDTH-1:0] pixel_in_d2;

    // Outputs from the three BRAM line memories
    wire [PIXEL_WIDTH-1:0] line0_q;
    wire [PIXEL_WIDTH-1:0] line1_q;
    wire [PIXEL_WIDTH-1:0] line2_q;

    // Registered BRAM outputs (align with shift registers)
    reg [PIXEL_WIDTH-1:0] line0_q_d;
    reg [PIXEL_WIDTH-1:0] line1_q_d;    
    reg [PIXEL_WIDTH-1:0] line2_q_d;

    // 3x3 window shift registers
    reg [PIXEL_WIDTH-1:0] top_row  [0:2];
    reg [PIXEL_WIDTH-1:0] mid_row  [0:2];
    reg [PIXEL_WIDTH-1:0] bot_row  [0:2];

    // Warm-up / debug infrastructure
    reg                    prefill_active;
    reg [ADDR_WIDTH+1:0]   fill_count;
    reg [3:0]              dbg_window_count;

    localparam integer FLUSH_THRESHOLD      = (IMG_WIDTH * 2) + 1;
    localparam [PIXEL_WIDTH-1:0] ZERO_PIXEL = {PIXEL_WIDTH{1'b0}};

    reg                   window_valid_reg;

    integer i;

    // Column / write address tracker (wraps at IMG_WIDTH)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            col_addr      <= {ADDR_WIDTH{1'b0}};
            write_addr    <= {ADDR_WIDTH{1'b0}};
            write_addr_d0 <= {ADDR_WIDTH{1'b0}};
            write_addr_d1 <= {ADDR_WIDTH{1'b0}};
        end else begin
            if (pixel_valid) begin
                if (col_addr == IMG_WIDTH - 1) begin
                    col_addr   <= {ADDR_WIDTH{1'b0}};
                    write_addr <= {ADDR_WIDTH{1'b0}};
                end else begin
                    col_addr   <= col_addr + 1'b1;
                    write_addr <= write_addr + 1'b1;
                end
                write_addr_d0 <= write_addr;
            end
            if (pixel_valid_d0) begin
                write_addr_d1 <= write_addr_d0;
            end
        end
    end

    // Row counter saturates once two rows have been buffered
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            row_count <= {ADDR_WIDTH{1'b0}};
        end else if (pixel_valid && (col_addr == IMG_WIDTH - 1)) begin
            if (row_count != {ADDR_WIDTH{1'b1}}) begin
                row_count <= row_count + 1'b1;
            end
        end
    end

    // Prefill tracking to scrub stale data before enabling outputs
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prefill_active   <= 1'b1;
            fill_count       <= {(ADDR_WIDTH+2){1'b0}};
        end else begin
            if (prefill_active) begin
                if (pixel_valid) begin
                    if (fill_count >= FLUSH_THRESHOLD - 1) begin
                        prefill_active <= 1'b0;
                    end else begin
                        fill_count <= fill_count + 1'b1;
                    end
                end
            end
        end
    end

    // Pipeline control signals / delayed coordinates
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pixel_valid_d0 <= 1'b0;
            pixel_valid_d1 <= 1'b0;
            col_addr_d0    <= {ADDR_WIDTH{1'b0}};
            col_addr_d1    <= {ADDR_WIDTH{1'b0}};
            row_count_d0   <= {ADDR_WIDTH{1'b0}};
            row_count_d1   <= {ADDR_WIDTH{1'b0}};
            pixel_in_d0    <= {PIXEL_WIDTH{1'b0}};
            pixel_in_d1    <= {PIXEL_WIDTH{1'b0}};
        end else begin
            pixel_valid_d0 <= pixel_valid;
            pixel_valid_d1 <= pixel_valid_d0;
            if (pixel_valid) begin
                col_addr_d0  <= col_addr;
                row_count_d0 <= row_count;
                pixel_in_d0  <= pixel_in;
            end
            if (pixel_valid_d0) begin
                col_addr_d1  <= col_addr_d0;
                row_count_d1 <= row_count_d0;
                pixel_in_d1  <= pixel_in_d0;
            end
        end
    end

    // Register BRAM outputs to align with pipeline stage
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            line0_q_d <= {PIXEL_WIDTH{1'b0}};
            line1_q_d <= {PIXEL_WIDTH{1'b0}};
            line2_q_d <= {PIXEL_WIDTH{1'b0}};
        end else if (pixel_valid_d0) begin
            line0_q_d <= line0_q;
            line1_q_d <= line1_q;
            line2_q_d <= line2_q;
        end
    end

    // Shift registers create 3x3 window (left-center-right taps)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (i = 0; i < 3; i = i + 1) begin
                top_row[i] <= {PIXEL_WIDTH{1'b0}};
                mid_row[i] <= {PIXEL_WIDTH{1'b0}};
                bot_row[i] <= {PIXEL_WIDTH{1'b0}};
            end
            dbg_window_count <= 4'd0;
        end else if (pixel_valid_d1) begin
            if (prefill_active) begin
                top_row[0] <= ZERO_PIXEL;
                top_row[1] <= ZERO_PIXEL;
                top_row[2] <= ZERO_PIXEL;

                mid_row[0] <= ZERO_PIXEL;
                mid_row[1] <= ZERO_PIXEL;
                mid_row[2] <= ZERO_PIXEL;

                bot_row[0] <= ZERO_PIXEL;
                bot_row[1] <= ZERO_PIXEL;
                bot_row[2] <= ZERO_PIXEL;

                dbg_window_count <= 4'd0;
            end else begin
                top_row[0] <= top_row[1];
                top_row[1] <= top_row[2];
                top_row[2] <= line2_q_d;

                mid_row[0] <= mid_row[1];
                mid_row[1] <= mid_row[2];
                mid_row[2] <= line1_q_d;

                bot_row[0] <= bot_row[1];
                bot_row[1] <= bot_row[2];
                bot_row[2] <= pixel_in_d1;

`ifndef SYNTHESIS
                if (dbg_window_count < 4'd8) begin
                    dbg_window_count <= dbg_window_count + 1'b1;
                    $display("[LINEBUF t=%0t] row=%0d col=%0d window=%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x",
                             $time,
                             row_count_d1,
                             col_addr_d1,
                             top_row[1],
                             top_row[2],
                             line2_q_d,
                             mid_row[1],
                             mid_row[2],
                             line1_q_d,
                             bot_row[1],
                             bot_row[2],
                             pixel_in_d1);
                end

`ifdef TB_SOBEL_RANDOM
                if (tb_sobel_random.current_frame_id == 5 &&
                    row_count_d1 >= 10'd88 && row_count_d1 <= 10'd92) begin
                    $display("[LINEBUFCHK t=%0t] frame=%0d row=%0d col=%0d win=%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x",
                             $time,
                             tb_sobel_random.current_frame_id,
                             row_count_d1,
                             col_addr_d1,
                             top_row[1],
                             top_row[2],
                             line2_q_d,
                             mid_row[1],
                             mid_row[2],
                             line1_q_d,
                             bot_row[1],
                             bot_row[2],
                             pixel_in_d1);
                end
`endif
`endif
            end
        end
    end

    // Valid once we have seen at least two rows and two columns
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            window_valid_reg <= 1'b0;
        end else begin
            window_valid_reg <= pixel_valid_d1 &&
                                (row_count_d1 >= 2) &&
                                (col_addr_d1 >= 1) &&
                                !prefill_active;
        end
    end

    assign window_valid = window_valid_reg;

    assign window_out[7:0]   = top_row[0];
    assign window_out[15:8]  = top_row[1];
    assign window_out[23:16] = top_row[2];
    assign window_out[31:24] = mid_row[0];
    assign window_out[39:32] = mid_row[1];
    assign window_out[47:40] = mid_row[2];
    assign window_out[55:48] = bot_row[0];
    assign window_out[63:56] = bot_row[1];
    assign window_out[71:64] = bot_row[2];

    // ------------------------------------------------------------------
    // Instantiate three BRAM primitives generated via Gowin SDPB IP
    // Each buffer stores one image line using true dual-port RAM
    // ------------------------------------------------------------------

    bram line0 (
        .dout   (line0_q),
        .clk    (clk),
        .cea    (pixel_valid),
        .reseta (~rst_n),
        .ceb    (1'b1),
        .resetb (~rst_n),
        .oce    (1'b1),
        .ada    (write_addr),
        .din    (pixel_in),
        .adb    (col_addr)
    );

    wire [PIXEL_WIDTH-1:0] line1_din = (prefill_active && (row_count_d0 == {ADDR_WIDTH{1'b0}}))
                                       ? ZERO_PIXEL
                                       : line0_q_d;
    wire [PIXEL_WIDTH-1:0] line2_din = (prefill_active && (row_count_d1 <= {{(ADDR_WIDTH-1){1'b0}}, 1'b1}))
                                       ? ZERO_PIXEL
                                       : line1_q_d;

    bram line1 (
        .dout   (line1_q),
        .clk    (clk),
        .cea    (pixel_valid_d0),
        .reseta (~rst_n),
        .ceb    (1'b1),
        .resetb (~rst_n),
        .oce    (1'b1),
        .ada    (write_addr_d0),
        .din    (line1_din),
        .adb    (col_addr_d0)
    );

    bram line2 (
        .dout   (line2_q),
        .clk    (clk),
        .cea    (pixel_valid_d1),
        .reseta (~rst_n),
        .ceb    (1'b1),
        .resetb (~rst_n),
        .oce    (1'b1),
        .ada    (write_addr_d1),
        .din    (line2_din),
        .adb    (col_addr_d1)
    );

endmodule


