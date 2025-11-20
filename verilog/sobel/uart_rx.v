//==============================================================================
// Module: uart_rx
// Description: UART receiver
//              Nhận dữ liệu 8-bit qua serial port với configurable baud rate
// Author: Nguyễn Văn Đạt
// Date: 2025
// Target: Tang Nano 4K (GW1NSR-LV4C)
//==============================================================================
module uart_rx #(
    parameter CLK_FREQ = 27_000_000,  // Clock frequency in Hz
    parameter BAUD_RATE = 115200       // Baud rate
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire       rx_pin,         // UART RX pin
    output reg  [7:0] rx_data,        // Received data
    output reg        rx_valid        // Data valid pulse
);

    localparam CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;
    
    localparam IDLE  = 3'd0;
    localparam START = 3'd1;
    localparam DATA  = 3'd2;
    localparam STOP  = 3'd3;
    
    reg [2:0] state;
    reg [15:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] rx_data_reg;
    reg rx_pin_d1, rx_pin_d2;

    // Synchronize RX input
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_pin_d1 <= 1'b1;
            rx_pin_d2 <= 1'b1;
        end else begin
            rx_pin_d1 <= rx_pin;
            rx_pin_d2 <= rx_pin_d1;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            rx_data <= 8'd0;
            rx_valid <= 1'b0;
            clk_count <= 16'd0;
            bit_index <= 3'd0;
            rx_data_reg <= 8'd0;
        end else begin
            rx_valid <= 1'b0;  // Default
            
            case (state)
                IDLE: begin
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;
                    
                    if (rx_pin_d2 == 1'b0) begin  // Start bit detected
                        state <= START;
                    end
                end
                
                START: begin
                    if (clk_count < (CLKS_PER_BIT / 2) - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        if (rx_pin_d2 == 1'b0) begin  // Validate start bit
                            clk_count <= 16'd0;
                            state <= DATA;
                        end else begin
                            state <= IDLE;
                        end
                    end
                end
                
                DATA: begin
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 16'd0;
                        rx_data_reg[bit_index] <= rx_pin_d2;
                        
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1;
                        end else begin
                            bit_index <= 3'd0;
                            state <= STOP;
                        end
                    end
                end
                
                STOP: begin
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 16'd0;
                        rx_data <= rx_data_reg;
                        rx_valid <= 1'b1;
                        state <= IDLE;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule