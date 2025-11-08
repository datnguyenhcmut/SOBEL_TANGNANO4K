`timescale 1ns/1ps

// Randomized self-checking testbench for sobel_processor
module tb_sobel_random;
    // Parameters
    localparam CLK_PERIOD = 40; // 25 MHz
    localparam IMG_WIDTH  = 64;
    localparam IMG_HEIGHT = 48;
    localparam FRAME_COUNT = 2;
    localparam PIPELINE_LATENCY = 5;
    localparam MAX_EXPECT_DEPTH = IMG_WIDTH * IMG_HEIGHT * 8;

    // DUT I/O
    reg clk, rst_n, href, vsync;
    reg [15:0] pixel_in;
    reg sobel_enable;
    wire pixel_valid;
    wire [15:0] pixel_out;

    // Instantiate DUT
    sobel_processor #(.IMG_WIDTH(IMG_WIDTH), .IMG_HEIGHT(IMG_HEIGHT), .PIXEL_WIDTH(8)) dut (
        .clk(clk), .rst_n(rst_n), .href(href), .vsync(vsync),
        .pixel_in(pixel_in), .sobel_enable(sobel_enable),
        .pixel_valid(pixel_valid), .pixel_out(pixel_out)
    );

    // Clock gen
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // FIFO to align expected outputs with DUT pixel_valid
    integer wptr, rptr;
    integer mismatches;
    integer expect_count;
    integer seed;
    integer base_seed;
    reg scoreboard_active;
    integer total_enqueued;
    integer total_observed;
    integer rand_seed_drain;
    integer handshake_errors;
    reg href_q;
    integer tail_allow;
    reg reset_injected;
    reg [127:0] frame_tag;
    reg [127:0] scenario_tag;
    reg [15:0] exp_fifo [0:MAX_EXPECT_DEPTH-1]; // allow for multi-frame + reset stress
    integer exp_row    [0:MAX_EXPECT_DEPTH-1];
    integer exp_col    [0:MAX_EXPECT_DEPTH-1];
    integer exp_frame  [0:MAX_EXPECT_DEPTH-1];
    reg [15:0] cap2_pixel_latched;
    integer current_frame_id;

    reg [71:0] exp_window [0:MAX_EXPECT_DEPTH-1];
    reg [71:0] rtl_window [0:MAX_EXPECT_DEPTH-1];
    integer rtl_wptr;
    integer rtl_rptr;

    // Reference model state mirroring RTL line buffer semantics
    integer row_count;
    reg [7:0] line_mem0 [0:IMG_WIDTH-1];
    reg [7:0] line_mem1 [0:IMG_WIDTH-1];
    reg [7:0] line_mem2 [0:IMG_WIDTH-1];

    // Helpers: RGB565 to expanded 8-bit RGB
    function [7:0] exp5to8;
        input [4:0] v5;
        begin
            exp5to8 = {v5, v5[4:2]};
        end
    endfunction

    function [7:0] exp6to8;
        input [5:0] v6;
        begin
            exp6to8 = {v6, v6[5:4]};
        end
    endfunction

    // Compute grayscale like rtl (weighted)
    function [7:0] rgb565_to_gray8;
        input [15:0] rgb;
        reg [7:0] r8, g8, b8;
        reg [15:0] rw, gw, bw;
        reg [17:0] sum;
        begin
            r8 = exp5to8(rgb[15:11]);
            g8 = exp6to8(rgb[10:5]);
            b8 = exp5to8(rgb[4:0]);
            rw = r8 * 8'd77;
            gw = g8 * 8'd151;
            bw = b8 * 8'd28;
            sum = rw + gw + bw;
            rgb565_to_gray8 = sum[15:8];
        end
    endfunction

    // Compute sobel magnitude and pack to RGB565 like RTL
    function [15:0] sobel_pack_rgb565;
        input signed [10:0] gx;
        input signed [10:0] gy;
        reg [10:0] ax, ay;
        reg [11:0] mag;
        reg [7:0] e8;
        begin
            ax = gx[10] ? (~gx + 11'd1) : gx;
            ay = gy[10] ? (~gy + 11'd1) : gy;
            mag = {1'b0, ax} + {1'b0, ay};
            if (mag > 12'd255) e8 = 8'hFF; else e8 = mag[7:0];
            sobel_pack_rgb565 = {e8[7:3], e8[7:2], e8[7:3]};
        end
    endfunction

    task flush_scoreboard;
        begin
            wptr = 0;
            rptr = 0;
            expect_count = 0;
            scoreboard_active = 1'b0;
            rtl_wptr = 0;
            rtl_rptr = 0;
        end
    endtask

    task reset_reference_state;
        integer idx;
        begin
            row_count = 0;
            for (idx = 0; idx < IMG_WIDTH; idx = idx + 1) begin
                line_mem0[idx] = 0;
                line_mem1[idx] = 0;
                line_mem2[idx] = 0;
            end
        end
    endtask

    task pump_pixel;
        input [15:0] pix;
        input integer col;
        integer xm1, xp1;
        reg [7:0] gray_local;
        reg [7:0] p0,p1,p2,p3,p4,p5,p6,p7,p8;
        reg signed [10:0] gx_local, gy_local;
        begin
            pixel_in = pix;
            gray_local = rgb565_to_gray8(pixel_in);

            if ((row_count >= 2) && (col >= 1)) begin
                xm1 = col - 1;
                xp1 = (col == IMG_WIDTH-1) ? 0 : (col + 1);

                p0 = line_mem2[xm1];
                p1 = line_mem2[col];
                p2 = line_mem2[xp1];
                p3 = line_mem1[xm1];
                p4 = line_mem1[col];
                p5 = line_mem1[xp1];
                p6 = line_mem0[xm1];
                p7 = line_mem0[col];
                p8 = line_mem0[xp1];

                gx_local = -$signed({1'b0,p0}) + $signed({1'b0,p2})
                         - ($signed({1'b0,p3}) <<< 1) + ($signed({1'b0,p5}) <<< 1)
                         - $signed({1'b0,p6}) + $signed({1'b0,p8});
                gy_local = -$signed({1'b0,p0}) - ($signed({1'b0,p1}) <<< 1) - $signed({1'b0,p2})
                         + $signed({1'b0,p6}) + ($signed({1'b0,p7}) <<< 1) + $signed({1'b0,p8});

                if (wptr >= MAX_EXPECT_DEPTH) begin
                    $display("[FATAL t=%0t] Scoreboard queue overflow (wptr=%0d depth=%0d)", $time, wptr, MAX_EXPECT_DEPTH);
                    $fatal;
                end
                exp_fifo[wptr] = sobel_pack_rgb565(gx_local, gy_local);
                exp_window[wptr] = {p0, p1, p2, p3, p4, p5, p6, p7, p8};
                exp_row[wptr]   = row_count;
                exp_col[wptr]   = col;
                exp_frame[wptr] = current_frame_id;
                if (wptr < 5) begin
                    $display("[EXPDBG t=%0t] idx=%0d frame=%0d row=%0d col=%0d val=%h",
                             $time, wptr, exp_frame[wptr], exp_row[wptr], exp_col[wptr], exp_fifo[wptr]);
                end
                if (current_frame_id >= 4 && row_count >= 2 && wptr < 8) begin
                    $display("[REFWIN t=%0t] frame=%0d row=%0d col=%0d p0=%h p1=%h p2=%h p3=%h p4=%h p5=%h p6=%h p7=%h p8=%h",
                             $time, current_frame_id, row_count, col,
                             p0, p1, p2, p3, p4, p5, p6, p7, p8);
                end
                wptr = wptr + 1;
                expect_count = expect_count + 1;
                total_enqueued = total_enqueued + 1;
                scoreboard_active = 1'b1;
            end

            line_mem2[col] = line_mem1[col];
            line_mem1[col] = line_mem0[col];
            line_mem0[col] = gray_local;
        end
    endtask

    task apply_async_reset;
        input integer idle_cycles;
        begin
            $display("[RESET] Asserting rst_n for %0d cycles at t=%0t", idle_cycles, $time);
            rst_n = 0;
            flush_scoreboard();
            reset_reference_state();
            tail_allow = 0;
            href = 0;
            vsync = 0;
            pixel_in = 0;
            repeat(idle_cycles) #(CLK_PERIOD);
            rst_n = 1;
            repeat(idle_cycles) #(CLK_PERIOD);
        end
    endtask

    task stream_frame;
        input integer frame_seed;
        input [127:0] tag;
        integer row, col;
        begin
            current_frame_id = current_frame_id + 1;
            frame_tag = tag;
            $display("[FRAME] %s seed=%0d start t=%0t", frame_tag, frame_seed, $time);
            rand_seed_drain = $urandom(frame_seed);
            vsync = 1; #(CLK_PERIOD*2); vsync = 0;

            for (row = 0; row < IMG_HEIGHT; row = row + 1) begin
                href = 1;
                for (col = 0; col < IMG_WIDTH; col = col + 1) begin
                    pump_pixel($urandom(), col);
                    #(CLK_PERIOD);
                end
                href = 0;
                row_count = row_count + 1;
                #(CLK_PERIOD*2);
            end
        end
    endtask

    task stream_partial_frame_with_reset;
        input integer frame_seed;
        input integer trigger_row;
        input integer trigger_col;
        output reg performed_reset;
        integer row, col;
        begin
            current_frame_id = current_frame_id + 1;
            performed_reset = 1'b0;
            $display("[PARTIAL] seed=%0d trigger=(%0d,%0d) t=%0t", frame_seed, trigger_row, trigger_col, $time);
            rand_seed_drain = $urandom(frame_seed);
            vsync = 1; #(CLK_PERIOD*2); vsync = 0;

            for (row = 0; row < IMG_HEIGHT; row = row + 1) begin : partial_rows
                href = 1;
                for (col = 0; col < IMG_WIDTH; col = col + 1) begin
                    pump_pixel($urandom(), col);
                    #(CLK_PERIOD);
                    if (!performed_reset && row == trigger_row && col == trigger_col) begin
                        href = 0;
                        #(CLK_PERIOD*2);
                        apply_async_reset(5);
                        performed_reset = 1'b1;
                        disable partial_rows;
                    end
                end
                if (!performed_reset) begin
                    href = 0;
                    row_count = row_count + 1;
                    #(CLK_PERIOD*2);
                end
            end
        end
    endtask

    task run_reset_recovery;
        input integer scenario_seed;
        integer trigger_row;
        integer trigger_col;
        reg partial_reset;
        begin
            scenario_tag = "reset-recovery";
            $display("[SCENARIO] %s seed=%0d", scenario_tag, scenario_seed);
            trigger_row = (IMG_HEIGHT/3);
            if (trigger_row < 3) trigger_row = 3;
            trigger_col = (IMG_WIDTH/4);
            if (trigger_col < 2) trigger_col = 2;
            stream_partial_frame_with_reset(scenario_seed, trigger_row, trigger_col, partial_reset);
            if (!partial_reset) begin
                $display("[WARN] Reset trigger not hit; forcing reset now.");
                apply_async_reset(5);
            end
            stream_frame(scenario_seed + 32'h1001, "post-reset #0");
            stream_frame(scenario_seed + 32'h2001, "post-reset #1");
        end
    endtask

    // Test sequence
    initial begin
        $dumpfile("sobel_wave.vcd");
        $dumpvars(0, tb_sobel_random);
        $display("=== tb_sobel_random: Randomized self-check ===");

        // Init defaults
        clk = 0; rst_n = 0; href = 0; vsync = 0; pixel_in = 0; sobel_enable = 1;
        wptr = 0; rptr = 0; mismatches = 0; expect_count = 0; total_enqueued = 0; total_observed = 0;
        handshake_errors = 0; scoreboard_active = 1'b0; tail_allow = 0; href_q = 0; current_frame_id = 0;
        seed = 32'h1BADB002;
        base_seed = seed;
        if ($value$plusargs("SEED=%d", seed)) begin
            base_seed = seed;
            $display("Using supplied seed %0d", seed);
        end else begin
            $display("Using default seed %0d", seed);
        end

        reset_reference_state();
        #(CLK_PERIOD*10);
        rst_n = 1;
        #(CLK_PERIOD*5);

        // Multi-frame stress
        begin
            integer frame_idx;
            for (frame_idx = 0; frame_idx < FRAME_COUNT; frame_idx = frame_idx + 1) begin
                stream_frame(base_seed + frame_idx, "multi-frame");
            end
        end

        #(CLK_PERIOD*PIPELINE_LATENCY*8);

        // Reset stress scenario
        run_reset_recovery(base_seed ^ 32'h55AA55AA);

        #(CLK_PERIOD*PIPELINE_LATENCY*8);

        $display("Expected outputs queued (active window): %0d", expect_count);
        $display("Outputs observed in queue: %0d", rptr);
        $display("Total outputs observed: %0d", total_observed);
        $display("Total outputs expected: %0d", total_enqueued);
        $display("Handshake errors detected: %0d", handshake_errors);

        if (mismatches == 0 && handshake_errors == 0 && (!scoreboard_active || (rptr == expect_count))) begin
            if (scoreboard_active && rptr != expect_count)
                $display("[WARN] Scoreboard active with unmatched counts (got %0d expected %0d)", rptr, expect_count);
            else
                $display("PASS: Randomized self-check + reset recovery completed with no mismatches.");
        end else begin
            if (mismatches != 0)
                $display("FAIL: Found %0d mismatches.", mismatches);
            if (handshake_errors != 0)
                $display("FAIL: Detected %0d handshake violations.", handshake_errors);
            if (scoreboard_active && rptr != expect_count)
                $display("FAIL: Output count mismatch (got %0d, expected %0d).", rptr, expect_count);
        end

        #(CLK_PERIOD*20);
        $finish;
    end

    // Capture RTL line-buffer windows for mismatch correlation
    always @(posedge clk) begin
        if (!rst_n) begin
            rtl_wptr <= 0;
        end else if (dut.u_linebuf.window_valid) begin
            if (rtl_wptr < MAX_EXPECT_DEPTH) begin
                rtl_window[rtl_wptr] <= dut.u_linebuf.window_out;
                rtl_wptr <= rtl_wptr + 1;
            end else begin
                $display("[WARN t=%0t] RTL window queue overflow (ptr=%0d)", $time, rtl_wptr);
            end
        end
    end

    // Compare when DUT asserts pixel_valid
    always @(posedge clk) begin
        reg [15:0] pixel_current;
        if (!rst_n) begin
            rptr <= 0;
            rtl_rptr <= 0;
            cap2_pixel_latched <= 16'h0;
        end else if (pixel_valid) begin
            pixel_current = pixel_out;
`ifndef SYNTHESIS
            if (exp_frame[rptr] == 5 &&
                exp_row[rptr] >= 88 && exp_row[rptr] <= 92) begin
                $display("[CAP2DBG t=%0t idx=%0d frame=%0d row=%0d col=%0d pixel_pre=%0h pixel_latched=%0h valid=%b sobel_en=%b]",
                         $time,
                         rptr,
                         exp_frame[rptr],
                         exp_row[rptr],
                         exp_col[rptr],
                         pixel_current,
                         cap2_pixel_latched,
                         pixel_valid,
                         sobel_enable);
            end
`endif
            cap2_pixel_latched <= pixel_current;
            total_observed = total_observed + 1;
            if (!scoreboard_active) begin
                $display("[DROP t=%0t] pixel_out=%h while scoreboard inactive", $time, pixel_current);
            end else begin
                if (rptr >= expect_count) begin
                    $display("[OVERFLOW t=%0t] got extra output %h (idx=%0d)", $time, pixel_current, rptr);
                    mismatches = mismatches + 1;
                end else begin
                    if (exp_frame[rptr] == 5 &&
                        exp_row[rptr] >= 88 && exp_row[rptr] <= 92) begin
                        $display("[CAPDBG t=%0t idx=%0d frame=%0d row=%0d col=%0d valid=%b sobel_en=%b pixel_out=%h]",
                                 $time,
                                 rptr,
                                 exp_frame[rptr],
                                 exp_row[rptr],
                                 exp_col[rptr],
                                 pixel_valid,
                                 sobel_enable,
                                 pixel_current);
                    end
                    if (pixel_current !== exp_fifo[rptr]) begin
                        $display("[MISMATCH t=%0t] got=%h exp=%h (idx=%0d frame=%0d row=%0d col=%0d)",
                                 $time, pixel_current, exp_fifo[rptr], rptr, exp_frame[rptr], exp_row[rptr], exp_col[rptr]);
                        $display("          exp_window=%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x",
                                 exp_window[rptr][71:64], exp_window[rptr][63:56], exp_window[rptr][55:48],
                                 exp_window[rptr][47:40], exp_window[rptr][39:32], exp_window[rptr][31:24],
                                 exp_window[rptr][23:16], exp_window[rptr][15:8], exp_window[rptr][7:0]);
                        if (rtl_rptr < rtl_wptr) begin
                            $display("          rtl_window=%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x_%02x",
                                     rtl_window[rtl_rptr][71:64], rtl_window[rtl_rptr][63:56], rtl_window[rtl_rptr][55:48],
                                     rtl_window[rtl_rptr][47:40], rtl_window[rtl_rptr][39:32], rtl_window[rtl_rptr][31:24],
                                     rtl_window[rtl_rptr][23:16], rtl_window[rtl_rptr][15:8], rtl_window[rtl_rptr][7:0]);
                        end else begin
                            $display("          rtl_window=<missing ptr=%0d total=%0d>", rtl_rptr, rtl_wptr);
                        end
                        mismatches = mismatches + 1;
                    end
                end
                rptr = rptr + 1;
                if (rtl_rptr < rtl_wptr)
                    rtl_rptr = rtl_rptr + 1;
                if (rptr == wptr)
                    scoreboard_active = 1'b0;
            end
        end
    end

    // Handshake monitor ensuring pixel_valid only during active video or pipeline drain
    always @(posedge clk) begin
        if (!rst_n) begin
            href_q <= 0;
            tail_allow <= 0;
        end else begin
            integer tail_next;
            reg href_fall;

            href_fall = href_q && !href;
            tail_next = tail_allow;

            if (href_fall) begin
                tail_next = PIPELINE_LATENCY;
            end else if (!href && tail_next > 0) begin
                tail_next = tail_next - 1;
            end else if (href) begin
                tail_next = 0;
            end

            if (!href && !href_fall && tail_next == 0 && pixel_valid) begin
                handshake_errors = handshake_errors + 1;
                $display("[HANDSHAKE t=%0t] pixel_valid outside active video (frame=%0d row=%0d tail=%0d)", $time, current_frame_id, row_count, tail_next);
            end

            tail_allow <= tail_next;
            href_q <= href;
        end
    end
endmodule
