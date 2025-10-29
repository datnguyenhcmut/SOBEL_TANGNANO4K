module line_buffer #(
    parameter IMG_WIDTH = 640,
    parameter PIXEL_WIDTH = 8,
    parameter ADDR_WIDTH = 10
)(
    input  wire clk,
    input  wire rst_n,
    input  wire pixel_valid,
    input  wire [PIXEL_WIDTH-1:0] pixel_in,
    output wire window_valid,
    output wire [PIXEL_WIDTH*9-1:0] window_out
);
    // Three line memories for 3x3 window
    reg [PIXEL_WIDTH-1:0] line_mem0 [0:IMG_WIDTH-1];
    reg [PIXEL_WIDTH-1:0] line_mem1 [0:IMG_WIDTH-1];
    reg [PIXEL_WIDTH-1:0] line_mem2 [0:IMG_WIDTH-1];

    // Column and row tracking
    reg [ADDR_WIDTH-1:0] col_addr;
    reg [ADDR_WIDTH-1:0] row_count;

    // Prefill tracker keeps window outputs suppressed until fresh data fills the pipeline
    reg prefill_active;
    reg [ADDR_WIDTH+1:0] fill_count;

    // Release first valid window once two rows plus one leading column have been loaded
    localparam integer FLUSH_THRESHOLD = (IMG_WIDTH * 2) + 1;

    // Registered 3x3 window and valid flag (single stage latency)
    reg [PIXEL_WIDTH-1:0] window_reg [0:8];
    reg window_valid_reg;
    reg [3:0] dbg_window_count;

    integer idx;

    // Column address updates per pixel
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            col_addr <= {ADDR_WIDTH{1'b0}};
        end else if (pixel_valid) begin
            if (col_addr == IMG_WIDTH - 1) begin
                col_addr <= {ADDR_WIDTH{1'b0}};
            end else begin
                col_addr <= col_addr + 1'b1;
            end
        end
    end

    // Row count increments at end of each line; only need to know >= 2
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            row_count <= {ADDR_WIDTH{1'b0}};
        end else if (prefill_active && (fill_count == 0)) begin
            // Ensure row tracker resets when warm-up restarts (covers async resets mid-frame)
            row_count <= {ADDR_WIDTH{1'b0}};
        end else if (pixel_valid && col_addr == IMG_WIDTH - 1) begin
            if (row_count != {ADDR_WIDTH{1'b1}}) begin
                row_count <= row_count + 1'b1;
            end
        end
    end

    // Shift the line memories each pixel (reads see old values this cycle)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            prefill_active <= 1'b1;
            fill_count <= {(ADDR_WIDTH+2){1'b0}};
            for (idx = 0; idx < IMG_WIDTH; idx = idx + 1) begin
                line_mem0[idx] <= {PIXEL_WIDTH{1'b0}};
                line_mem1[idx] <= {PIXEL_WIDTH{1'b0}};
                line_mem2[idx] <= {PIXEL_WIDTH{1'b0}};
            end
        end else if (pixel_valid) begin
            // Scrub stale data during warm-up so the first windows are fresh
            if (row_count == {ADDR_WIDTH{1'b0}}) begin
                line_mem2[col_addr] <= {PIXEL_WIDTH{1'b0}};
                line_mem1[col_addr] <= {PIXEL_WIDTH{1'b0}};
            end else if (row_count == {{(ADDR_WIDTH-1){1'b0}}, 1'b1}) begin
                line_mem2[col_addr] <= {PIXEL_WIDTH{1'b0}};
                line_mem1[col_addr] <= line_mem0[col_addr];
            end else begin
                line_mem2[col_addr] <= line_mem1[col_addr];
                line_mem1[col_addr] <= line_mem0[col_addr];
            end

            line_mem0[col_addr] <= pixel_in;

            if (prefill_active) begin
                if (fill_count < FLUSH_THRESHOLD) begin
                    fill_count <= fill_count + 1'b1;
                end
                if (fill_count >= FLUSH_THRESHOLD - 1) begin
                    prefill_active <= 1'b0;
                end
            end
        end
    end

    // Neighbor addressing with wrap for +1 and -1
    wire [ADDR_WIDTH-1:0] addr_m1 = (col_addr == 0) ? IMG_WIDTH - 1 : col_addr - 1;
    wire [ADDR_WIDTH-1:0] addr_p1 = (col_addr == IMG_WIDTH - 1) ? 0 : col_addr + 1;

    // Capture and pipeline the 3x3 window; align valid one cycle later
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            window_valid_reg <= 1'b0;
            dbg_window_count <= 4'd0;
            for (idx = 0; idx < 9; idx = idx + 1) begin
                window_reg[idx] <= {PIXEL_WIDTH{1'b0}};
            end
        end else if (prefill_active) begin
            window_valid_reg <= 1'b0;
            dbg_window_count <= 4'd0;
        end else if (pixel_valid && row_count >= 2 && col_addr >= 1) begin
            window_reg[0] <= line_mem2[addr_m1];
            window_reg[1] <= line_mem2[col_addr];
            window_reg[2] <= line_mem2[addr_p1];
            window_reg[3] <= line_mem1[addr_m1];
            window_reg[4] <= line_mem1[col_addr];
            window_reg[5] <= line_mem1[addr_p1];
            window_reg[6] <= line_mem0[addr_m1];
            window_reg[7] <= line_mem0[col_addr];
            window_reg[8] <= line_mem0[addr_p1];
            window_valid_reg <= 1'b1;

            if (dbg_window_count < 4'd8) begin
                dbg_window_count <= dbg_window_count + 1'b1;
                $display("[LINEBUF t=%0t] row=%0d col=%0d window=%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x",
                         $time, row_count, col_addr,
                         line_mem2[addr_m1], line_mem2[col_addr], line_mem2[addr_p1],
                         line_mem1[addr_m1], line_mem1[col_addr], line_mem1[addr_p1],
                         line_mem0[addr_m1], line_mem0[col_addr], line_mem0[addr_p1]);
            end

            // Targeted debug capture around the failing frame/rows
`ifndef SYNTHESIS
`ifdef TB_SOBEL_RANDOM
            if (tb_sobel_random.current_frame_id == 5 && row_count >= 88 && row_count <= 92) begin
                $display("[LINEBUFCHK t=%0t] frame=%0d row=%0d col=%0d addr_m1=%0d addr=%0d addr_p1=%0d wr_en=%0b win=%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x",
                         $time,
                         tb_sobel_random.current_frame_id,
                         row_count, col_addr,
                         addr_m1, col_addr, addr_p1,
                         pixel_valid,
                         line_mem2[addr_m1], line_mem2[col_addr], line_mem2[addr_p1],
                         line_mem1[addr_m1], line_mem1[col_addr], line_mem1[addr_p1],
                         line_mem0[addr_m1], line_mem0[col_addr], line_mem0[addr_p1]);
            end
`endif
`endif
        end else begin
            window_valid_reg <= 1'b0;
        end
    end

    assign window_valid = window_valid_reg;
    assign window_out[7:0]   = window_reg[0];
    assign window_out[15:8]  = window_reg[1];
    assign window_out[23:16] = window_reg[2];
    assign window_out[31:24] = window_reg[3];
    assign window_out[39:32] = window_reg[4];
    assign window_out[47:40] = window_reg[5];
    assign window_out[55:48] = window_reg[6];
    assign window_out[63:56] = window_reg[7];
    assign window_out[71:64] = window_reg[8];
endmodule


