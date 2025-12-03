//==============================================================================
// Module: system_top
// Description: System top-level module tích hợp:
//              - video_top: Camera input, frame buffer, HDMI output
//              - Sobel edge detection processor
//              - UART: Debug/data transfer interface
// Author: Nguyễn Văn Đạt
// Date: 2025
// Target: Tang Nano 4K (GW1NSR-LV4C)
//==============================================================================

module system_top (
    input  wire        sys_clk,        // 27MHz system clock
    input  wire        sys_resetn,     // Active-low reset button
    
    // Camera interface (OV2640)
    input  wire        cam_pclk,
    input  wire        cam_href,
    input  wire        cam_vsync,
    input  wire [7:0]  cam_data,
    output wire        cam_xclk,
    inout  wire        cam_scl,
    inout  wire        cam_sda,
    output wire        cam_pwdn,
    output wire        cam_rst_n,
    
    // HDMI output
    output wire        tmds_clk_p,
    output wire        tmds_clk_n,
    output wire [2:0]  tmds_data_p,
    output wire [2:0]  tmds_data_n,
    
    // HyperRAM interface
    output wire        O_hpram_ck,
    output wire        O_hpram_ck_n,
    inout  wire [7:0]  IO_hpram_dq,
    output wire        O_hpram_reset_n,
    inout  wire        IO_hpram_rwds,
    output wire        O_hpram_cs_n,
    
    // LED indicators
    output wire [5:0]  led,
    
    // Button input (for mode switching)
    input  wire        key,
    
    // UART interface
    input  wire        uart_rx,
    output wire        uart_tx
);

    //==========================================================================
    // Internal signals
    //==========================================================================
    wire clk_pixel;           // Pixel clock for video
    wire clk_serial;          // Serial clock for HDMI
    wire pll_lock;
    
    // Video signals
    wire [15:0] video_rgb565;
    wire        video_de;
    wire        video_hsync;
    wire        video_vsync;
    
    // Sobel processor signals
    wire [7:0]  sobel_magnitude;
    wire        sobel_valid;
    wire        sobel_enable;
    
    // UART signals
    wire [7:0]  uart_tx_data;
    wire        uart_tx_valid;
    wire        uart_tx_ready;
    wire [7:0]  uart_rx_data;
    wire        uart_rx_valid;
    
    // Debug/control registers
    reg [7:0]   debug_reg;
    reg [15:0]  frame_counter;
    
    //==========================================================================
    // Video subsystem (existing video_top)
    //==========================================================================
    video_top u_video_top (
        .sys_clk(sys_clk),
        .sys_resetn(sys_resetn),
        
        // Camera
        .PIXCLK(cam_pclk),
        .HREF(cam_href),
        .VSYNC(cam_vsync),
        .PIXDATA(cam_data),
        .XCLK(cam_xclk),
        .SCL(cam_scl),
        .SDA(cam_sda),
        .PWDN(cam_pwdn),
        .RESET(cam_rst_n),
        
        // HDMI
        .tmds_clk_p(tmds_clk_p),
        .tmds_clk_n(tmds_clk_n),
        .tmds_data_p(tmds_data_p),
        .tmds_data_n(tmds_data_n),
        
        // HyperRAM
        .O_hpram_ck(O_hpram_ck),
        .O_hpram_ck_n(O_hpram_ck_n),
        .IO_hpram_dq(IO_hpram_dq),
        .O_hpram_reset_n(O_hpram_reset_n),
        .IO_hpram_rwds(IO_hpram_rwds),
        .O_hpram_cs_n(O_hpram_cs_n),
        
        // LED and button
        .led(led),
        .key(key)
    );
    
    //==========================================================================
    // UART subsystem
    //==========================================================================
    uart_top #(
        .CLK_FREQ(27_000_000),
        .BAUD_RATE(115200)
    ) u_uart (
        .clk(sys_clk),
        .rst_n(sys_resetn),
        
        .tx_data(uart_tx_data),
        .tx_valid(uart_tx_valid),
        .tx_ready(uart_tx_ready),
        
        .rx_data(uart_rx_data),
        .rx_valid(uart_rx_valid),
        
        .uart_rx(uart_rx),
        .uart_tx(uart_tx)
    );
    
    //==========================================================================
    // UART control logic
    // Commands:
    //   'S' - Enable Sobel
    //   's' - Disable Sobel
    //   'R' - Send frame statistics
    //   'D' - Send debug info
    //==========================================================================
    always @(posedge sys_clk or negedge sys_resetn) begin
        if (!sys_resetn) begin
            debug_reg <= 8'd0;
        end else begin
            if (uart_rx_valid) begin
                debug_reg <= uart_rx_data;
                // Handle commands here
            end
        end
    end
    
    // Frame counter for statistics
    always @(posedge sys_clk or negedge sys_resetn) begin
        if (!sys_resetn) begin
            frame_counter <= 16'd0;
        end else begin
            if (cam_vsync) begin
                frame_counter <= frame_counter + 1;
            end
        end
    end
    
    //==========================================================================
    // UART transmit logic (example: send frame count on 'R' command)
    //==========================================================================
    reg [1:0] tx_state;
    reg [7:0] tx_byte;
    
    localparam TX_IDLE = 2'd0;
    localparam TX_HIGH = 2'd1;
    localparam TX_LOW  = 2'd2;
    
    assign uart_tx_data = tx_byte;
    assign uart_tx_valid = (tx_state != TX_IDLE);
    
    always @(posedge sys_clk or negedge sys_resetn) begin
        if (!sys_resetn) begin
            tx_state <= TX_IDLE;
            tx_byte <= 8'd0;
        end else begin
            case (tx_state)
                TX_IDLE: begin
                    if (uart_rx_valid && uart_rx_data == 8'h52) begin  // 'R'
                        tx_byte <= frame_counter[15:8];
                        tx_state <= TX_HIGH;
                    end
                end
                
                TX_HIGH: begin
                    if (uart_tx_ready) begin
                        tx_byte <= frame_counter[7:0];
                        tx_state <= TX_LOW;
                    end
                end
                
                TX_LOW: begin
                    if (uart_tx_ready) begin
                        tx_state <= TX_IDLE;
                    end
                end
                
                default: tx_state <= TX_IDLE;
            endcase
        end
    end

endmodule