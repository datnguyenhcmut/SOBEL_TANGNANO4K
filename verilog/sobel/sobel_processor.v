//==============================================================================
// Module: sobel_processor
// Description: Top-level Sobel edge detection pipeline - tích hợp RGB→Gray,
//              Line Buffer, Gaussian Blur, Sobel Kernel, Edge Magnitude
// Author: Nguyễn Văn Đạt
// Date: 2025
// Target: Tang Nano 4K
//==============================================================================

module sobel_processor #(
    parameter IMG_WIDTH = 640,
    parameter IMG_HEIGHT = 480,
    parameter PIXEL_WIDTH = 8,
    parameter USE_BILATERAL = 0              // 0=Gaussian, 1=Bilateral (edge-preserving)
)(
    input  wire clk,
    input  wire rst_n,
    input  wire href,
    input  wire vsync,
    input  wire [15:0] pixel_in,
    input  wire sobel_enable,
    input  wire [7:0] edge_threshold,        // ← NEW: Binarization threshold
    input  wire [1:0] threshold_mode,        // ← NEW: 00=fixed, 01=adaptive, 10=hysteresis
    output wire pixel_valid,
    output wire [15:0] pixel_out,
    output wire binary_pixel,                // ← NEW: Binary edge output
    output wire binary_valid,                // ← NEW: Binary valid
    output wire strong_edge,                 // ← NEW: Strong edge (Canny)
    output wire weak_edge                    // ← NEW: Weak edge (Canny)
);

    wire [PIXEL_WIDTH-1:0] gray_pixel;
    wire gray_valid;
    wire [PIXEL_WIDTH*9-1:0] window_flat;
    wire window_valid;
    
    // Gaussian blur signals
    wire [PIXEL_WIDTH*9-1:0] window_blurred;
    wire blur_valid;
    
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
    
    // Gaussian blur (traditional - smooths everything)
    gaussian_blur #(.PIXEL_WIDTH(PIXEL_WIDTH)) u_gaussian (
        .clk(clk), .rst_n(rst_n), .window_valid(window_valid),
        .window_flat(window_flat), .blur_valid(blur_valid), .window_blurred(window_blurred)
    );
    
    // Bilateral filter (edge-preserving - keeps sharp edges, removes noise)
    wire [PIXEL_WIDTH*9-1:0] window_bilateral;
    wire bilateral_valid;
    bilateral_filter #(
        .PIXEL_WIDTH(PIXEL_WIDTH),
        .SIGMA_RANGE(28)  // BALANCED: Sharp edges with noise reduction (was 35)
    ) u_bilateral (
        .clk(clk), .rst_n(rst_n), .window_valid(window_valid),
        .window_flat(window_flat), .filter_valid(bilateral_valid), .window_filtered(window_bilateral)
    );
    
    // Select filter: 0=Gaussian (smoother), 1=Bilateral (edge-preserving)
    wire [PIXEL_WIDTH*9-1:0] window_filtered = USE_BILATERAL ? window_bilateral : window_blurred;
    wire filter_valid = USE_BILATERAL ? bilateral_valid : blur_valid;

    sobel_kernel u_sobel (
        .clk(clk), .rst_n(rst_n), .window_valid(filter_valid),
        .window_flat(window_filtered), .sobel_valid(sobel_valid), .gx_out(gx), .gy_out(gy)
    );

    edge_mag u_magnitude (
        .clk(clk), .rst_n(rst_n), .sobel_valid(sobel_valid),
        .gx_in(gx), .gy_in(gy), .edge_valid(edge_valid), .edge_magnitude(edge_magnitude)
    );

    //==========================================================================
    // Shadow & Blob Rejection Filter
    // - Shadows/blobs: Low gradient consistency, weak magnitude
    // - Object edges: High consistency, strong magnitude
    //==========================================================================
    reg signed [10:0] gx_prev, gy_prev;
    reg edge_valid_d;
    reg [PIXEL_WIDTH-1:0] edge_magnitude_d;
    reg [PIXEL_WIDTH-1:0] magnitude_prev;
    
    always @(posedge clk) begin
        if (edge_valid) begin
            gx_prev <= gx;
            gy_prev <= gy;
            edge_valid_d <= edge_valid;
            edge_magnitude_d <= edge_magnitude;
            magnitude_prev <= edge_magnitude;
        end
    end
    
    // 1. Gradient Direction Consistency (removes shadows/light patches)
    wire signed [21:0] dot_product = (gx * gx_prev) + (gy * gy_prev);
    wire signed [21:0] mag_product = (gx * gx) + (gy * gy) + 1;
    wire gradient_consistent = (dot_product > (mag_product >>> 1)); // >0.5 (balanced)
    
    // 2. Magnitude Consistency (removes blobs/patches)
    // Object edges have similar magnitude along the edge, blobs vary wildly
    wire [PIXEL_WIDTH-1:0] mag_diff = (edge_magnitude_d > magnitude_prev) ? 
                                      (edge_magnitude_d - magnitude_prev) : 
                                      (magnitude_prev - edge_magnitude_d);
    wire magnitude_stable = (mag_diff < 8'd40); // Balanced: Keep edges, remove patches
    
    // 3. Minimum magnitude threshold (remove weak gradients)
    wire magnitude_strong = (edge_magnitude_d > 8'd65); // LOWERED: Detect more edges, noise filter active
    
    // Combine all filters: Must pass ALL conditions
    wire edge_is_valid = gradient_consistent && magnitude_stable && magnitude_strong && edge_valid_d;
    
    // Apply filters
    wire [PIXEL_WIDTH-1:0] filtered_magnitude = edge_is_valid ? edge_magnitude_d : 8'd0;
    wire filtered_valid = edge_valid_d;

    //==========================================================================
    // NEW: Image Binarization Module
    // Supports multiple thresholding methods (fixed, adaptive, hysteresis)
    //==========================================================================
    wire binary_pixel_raw;
    wire binary_valid_raw;
    
    image_binarization #(
        .PIXEL_WIDTH(8),
        .DEFAULT_THRESHOLD(8'd100),
        .HIGH_THRESHOLD(8'd95),         // LOWERED: Detect more edges (was 105)
        .LOW_THRESHOLD(8'd55)           // LOWERED: Include weaker edges (was 65)
    ) u_binarization (
        .clk            (clk),
        .rst_n          (rst_n),
        .edge_magnitude (filtered_magnitude),  // Use shadow-filtered magnitude
        .edge_valid     (filtered_valid),      // Use filtered valid signal
        .threshold      (edge_threshold),
        .threshold_mode (threshold_mode),
        .binary_pixel   (binary_pixel_raw),    // Raw binary (before morphological filter)
        .binary_valid   (binary_valid_raw),
        .strong_edge    (strong_edge),
        .weak_edge      (weak_edge)
    );

    //==========================================================================
    // Noise Rejection Filter: Remove isolated pixels, keep continuous edges
    // Simple spatial filter - NO line buffer needed (no white lines!)
    //==========================================================================
    noise_rejection_filter u_noise_filter (
        .clk              (clk),
        .rst_n            (rst_n),
        .pixel_valid      (binary_valid_raw),
        .pixel_in         (binary_pixel_raw),
        .pixel_out        (binary_pixel),
        .pixel_out_valid  (binary_valid)
    );

    wire [15:0] sobel_rgb565 = {edge_magnitude[7:3], edge_magnitude[7:2], edge_magnitude[7:3]};

    assign pixel_valid = sobel_enable ? edge_valid : href;
    assign pixel_out = sobel_enable ? sobel_rgb565 : pixel_in;

// `ifndef SYNTHESIS
// `ifdef TB_SOBEL_RANDOM
//     always @(posedge clk) begin
//         if (tb_sobel_random.current_frame_id == 5 &&
//             tb_sobel_random.dut.u_linebuf.row_count >= 88 &&
//             tb_sobel_random.dut.u_linebuf.row_count <= 92 &&
//             /!tb_sobel_random.dut.u_linebuf.prefill_active) begin
//             if (sobel_enable && edge_valid) begin
//                 $display("[PROCDBG frame=%0d row=%0d col=%0d mag=%0h rgb565=%0h sobel_en=%b]",
//                          tb_sobel_random.current_frame_id,
//                          tb_sobel_random.dut.u_linebuf.row_count,
//                          tb_sobel_random.dut.u_linebuf.col_addr,
//                          edge_magnitude,
//                          sobel_rgb565,
//                          sobel_enable);
//             end

//             if (pixel_valid) begin
//                 $display("[BOUNDDBG t=%0t frame=%0d row=%0d col=%0d sobel_rgb565=%0h pixel_out=%0h sobel_en=%b]",
//                          $time,
//                          tb_sobel_random.current_frame_id,
//                          tb_sobel_random.dut.u_linebuf.row_count,
//                          tb_sobel_random.dut.u_linebuf.col_addr,
//                          sobel_rgb565,
//                          pixel_out,
//                          sobel_enable);
//                 $display("[MUXDBG t=%0t frame=%0d row=%0d col=%0d sobel_rgb=%0h bypass_rgb=%0h pixel_out=%0h sobel_en=%b edge_valid=%b pixel_valid=%b]",
//                          $time,
//                          tb_sobel_random.current_frame_id,
//                          tb_sobel_random.dut.u_linebuf.row_count,
//                          tb_sobel_random.dut.u_linebuf.col_addr,
//                          sobel_rgb565,
//                          pixel_in,
//                          pixel_out,
//                          sobel_enable,
//                          edge_valid,
//                          pixel_valid);
//             end
//         end
//     end
// `endif
// `endif

endmodule
