`timescale 1ns/1ps

module tb_sobel_video;
    localparam CLK_PERIOD_NS = 40; // 25 MHz pixel clock
    localparam IMG_WIDTH = 640;
    localparam IMG_HEIGHT = 480;
    localparam string INPUT_PATH = "../data/video_in.rgb";
    localparam string META_PATH = "../data/video_meta.txt";
    localparam string OUTPUT_PATH = "../data/video_out.rgb";

    reg clk = 1'b0;
    reg rst_n = 1'b0;
    reg href = 1'b0;
    reg vsync = 1'b0;
    reg [15:0] pixel_in = 16'h0000;
    reg sobel_enable = 1'b1;
    wire pixel_valid;
    wire [15:0] pixel_out;

    localparam PIPE_DEPTH = 4;

    reg [9:0] stim_row = 10'd0;
    reg [9:0] stim_col = 10'd0;
    reg [9:0] row_pipe [0:PIPE_DEPTH-1];
    reg [9:0] col_pipe [0:PIPE_DEPTH-1];
    reg       valid_pipe [0:PIPE_DEPTH-1];
    integer pipe_idx;

    integer frame_count;
    integer meta_width;
    integer meta_height;
    integer in_fd;
    integer out_fd;
    integer outputs_seen = 0;

    always #(CLK_PERIOD_NS/2.0) clk = ~clk;

    sobel_processor #(
        .IMG_WIDTH(IMG_WIDTH),
        .IMG_HEIGHT(IMG_HEIGHT),
        .PIXEL_WIDTH(8)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .href(href),
        .vsync(vsync),
        .pixel_in(pixel_in),
        .sobel_enable(sobel_enable),
        .pixel_valid(pixel_valid),
        .pixel_out(pixel_out)
    );

    function automatic [15:0] read_pixel_word;
        integer byte_lo;
        integer byte_hi;
        begin
            byte_lo = $fgetc(in_fd);
            byte_hi = $fgetc(in_fd);
            if (byte_hi == -1) begin
                $fatal(1, "[tb_sobel_video] Unexpected EOF while reading %s", INPUT_PATH);
            end
            read_pixel_word = {byte_hi[7:0], byte_lo[7:0]};
        end
    endfunction

    task automatic read_metadata;
        integer meta_fd;
        integer status;
        reg [8*128-1:0] line;
        begin
            meta_fd = $fopen(META_PATH, "r");
            if (meta_fd == 0) begin
                $fatal(1, "[tb_sobel_video] Unable to open metadata file %s", META_PATH);
            end

            line = {(8*128){1'b0}};
            if (!$fgets(line, meta_fd)) begin
                $fatal(1, "[tb_sobel_video] Metadata file %s is empty", META_PATH);
            end
            status = $sscanf(line, "frames=%d", frame_count);
            if (status != 1) $fatal(1, "[tb_sobel_video] Failed to parse frame count from %s", META_PATH);

            line = {(8*128){1'b0}};
            if (!$fgets(line, meta_fd)) begin
                $fatal(1, "[tb_sobel_video] Metadata missing width entry in %s", META_PATH);
            end
            status = $sscanf(line, "width=%d", meta_width);
            if (status != 1) $fatal(1, "[tb_sobel_video] Failed to parse width from %s", META_PATH);

            line = {(8*128){1'b0}};
            if (!$fgets(line, meta_fd)) begin
                $fatal(1, "[tb_sobel_video] Metadata missing height entry in %s", META_PATH);
            end
            status = $sscanf(line, "height=%d", meta_height);
            if (status != 1) $fatal(1, "[tb_sobel_video] Failed to parse height from %s", META_PATH);

            $fclose(meta_fd);
            if (meta_width != IMG_WIDTH || meta_height != IMG_HEIGHT) begin
                $fatal(1, "[tb_sobel_video] Metadata resolution %0dx%0d does not match expected %0dx%0d", meta_width, meta_height, IMG_WIDTH, IMG_HEIGHT);
            end
        end
    endtask

    task automatic play_frame(input integer frame_idx);
        integer row;
        integer col;
        begin
            $display("[tb_sobel_video] Streaming frame %0d/%0d", frame_idx + 1, frame_count);
            vsync <= 1'b1;
            @(posedge clk);
            vsync <= 1'b0;
            @(posedge clk);
            for (row = 0; row < IMG_HEIGHT; row = row + 1) begin
                href <= 1'b1;
                for (col = 0; col < IMG_WIDTH; col = col + 1) begin
                    pixel_in <= read_pixel_word();
                    @(posedge clk);
                end
                href <= 1'b0;
                pixel_in <= 16'h0000;
                repeat (2) @(posedge clk);
            end
            repeat (IMG_WIDTH/4) @(posedge clk);
        end
    endtask

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            stim_row <= 10'd0;
            stim_col <= 10'd0;
            for (pipe_idx = 0; pipe_idx < PIPE_DEPTH; pipe_idx = pipe_idx + 1) begin
                row_pipe[pipe_idx] <= 10'd0;
                col_pipe[pipe_idx] <= 10'd0;
                valid_pipe[pipe_idx] <= 1'b0;
            end
        end else begin
            if (vsync) begin
                stim_row <= 10'd0;
                stim_col <= 10'd0;
            end else if (href) begin
                if (stim_col == IMG_WIDTH - 1) begin
                    stim_col <= 10'd0;
                    if (stim_row != IMG_HEIGHT - 1) begin
                        stim_row <= stim_row + 1'b1;
                    end
                end else begin
                    stim_col <= stim_col + 1'b1;
                end
            end

            valid_pipe[0] <= href;
            row_pipe[0] <= stim_row;
            col_pipe[0] <= stim_col;

            for (pipe_idx = 1; pipe_idx < PIPE_DEPTH; pipe_idx = pipe_idx + 1) begin
                valid_pipe[pipe_idx] <= valid_pipe[pipe_idx - 1];
                row_pipe[pipe_idx] <= row_pipe[pipe_idx - 1];
                col_pipe[pipe_idx] <= col_pipe[pipe_idx - 1];
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            outputs_seen <= 0;
        end else if (pixel_valid && valid_pipe[PIPE_DEPTH-1]) begin
            if (row_pipe[PIPE_DEPTH-1] >= 2 && row_pipe[PIPE_DEPTH-1] < IMG_HEIGHT &&
                col_pipe[PIPE_DEPTH-1] >= 1 && col_pipe[PIPE_DEPTH-1] < IMG_WIDTH) begin
                if (out_fd == 0) begin
                    $fatal(1, "[tb_sobel_video] Output handle invalid");
                end
                $fwrite(out_fd, "%c", pixel_out[7:0]);
                $fwrite(out_fd, "%c", pixel_out[15:8]);
                outputs_seen <= outputs_seen + 1;
            end
        end
    end

    initial begin
        integer expected_outputs_per_frame;
        integer total_expected_outputs;
        integer frame_idx;

        read_metadata();
        in_fd = $fopen(INPUT_PATH, "rb");
        if (in_fd == 0) $fatal(1, "[tb_sobel_video] Cannot open input %s", INPUT_PATH);
        out_fd = $fopen(OUTPUT_PATH, "wb");
        if (out_fd == 0) $fatal(1, "[tb_sobel_video] Cannot open output %s", OUTPUT_PATH);

        expected_outputs_per_frame = (IMG_HEIGHT - 2) * (IMG_WIDTH - 1);
        total_expected_outputs = expected_outputs_per_frame * frame_count;

        repeat (20) @(posedge clk);
        rst_n <= 1'b1;
        repeat (10) @(posedge clk);

        for (frame_idx = 0; frame_idx < frame_count; frame_idx = frame_idx + 1) begin
            play_frame(frame_idx);
        end

        repeat (IMG_WIDTH * 4) @(posedge clk);

        if (outputs_seen != total_expected_outputs) begin
            $display("[tb_sobel_video][WARN] Output count mismatch: %0d vs %0d", outputs_seen, total_expected_outputs);
        end else begin
            $display("[tb_sobel_video] Output samples: %0d", outputs_seen);
        end

        $fclose(in_fd);
        $fclose(out_fd);
        $display("[tb_sobel_video] Simulation done");
        $finish;
    end
endmodule