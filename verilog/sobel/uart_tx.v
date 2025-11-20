//==============================================================================
// Module: uart_tx
// Description: UART transmitter
//              Gửi dữ liệu 8-bit qua serial port với configurable baud rate
// Author: Nguyễn Văn Đạt
// Date: 2025
// Target: Tang Nano 4K (GW1NSR-LV4C)
//==============================================================================
module uart_tx #(
    parameter CLK_FREQ = 27_000_000,  // Clock frequency in Hz
    parameter BAUD_RATE = 115200       // Baud rate
)(
    input  wire       clk,
    input  wire       rst_n,
    input  wire [7:0] tx_data,        // Data to transmit
    input  wire       tx_valid,       // Start transmission
    output reg        tx_ready,       // Ready for new data
    output reg        tx_pin          // UART TX pin
);

    localparam CLKS_PER_BIT = CLK_FREQ / BAUD_RATE;
    
    localparam IDLE  = 3'd0;
    localparam START = 3'd1;
    localparam DATA  = 3'd2;
    localparam STOP  = 3'd3;
    
    reg [2:0] state;
    reg [15:0] clk_count;
    reg [2:0] bit_index;
    reg [7:0] tx_data_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            tx_pin <= 1'b1;
            tx_ready <= 1'b1;
            clk_count <= 16'd0;
            bit_index <= 3'd0;
            tx_data_reg <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx_pin <= 1'b1;
                    tx_ready <= 1'b1;
                    clk_count <= 16'd0;
                    bit_index <= 3'd0;
                    
                    if (tx_valid) begin
                        tx_data_reg <= tx_data;
                        tx_ready <= 1'b0;
                        state <= START;
                    end
                end
                
                START: begin
                    tx_pin <= 1'b0;  // Start bit
                    
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 16'd0;
                        state <= DATA;
                    end
                end
                
                DATA: begin
                    tx_pin <= tx_data_reg[bit_index];
                    
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 16'd0;
                        
                        if (bit_index < 7) begin
                            bit_index <= bit_index + 1;
                        end else begin
                            bit_index <= 3'd0;
                            state <= STOP;
                        end
                    end
                end
                
                STOP: begin
                    tx_pin <= 1'b1;  // Stop bit
                    
                    if (clk_count < CLKS_PER_BIT - 1) begin
                        clk_count <= clk_count + 1;
                    end else begin
                        clk_count <= 16'd0;
                        state <= IDLE;
                    end
                end
                
                default: state <= IDLE;
            endcase
        end
    end

endmodule