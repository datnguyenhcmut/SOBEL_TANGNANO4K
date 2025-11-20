//==============================================================================
// Module: uart_top
// Description: UART top wrapper với TX và RX
//              Giao tiếp serial với PC để debug/transfer data
// Author: Nguyễn Văn Đạt
// Date: 2025
// Target: Tang Nano 4K (GW1NSR-LV4C)
//==============================================================================
module uart_top #(
    parameter CLK_FREQ = 27_000_000,
    parameter BAUD_RATE = 115200
)(
    input  wire       clk,
    input  wire       rst_n,
    
    // TX interface
    input  wire [7:0] tx_data,
    input  wire       tx_valid,
    output wire       tx_ready,
    
    // RX interface
    output wire [7:0] rx_data,
    output wire       rx_valid,
    
    // UART pins
    input  wire       uart_rx,
    output wire       uart_tx
);

    uart_tx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_tx (
        .clk(clk),
        .rst_n(rst_n),
        .tx_data(tx_data),
        .tx_valid(tx_valid),
        .tx_ready(tx_ready),
        .tx_pin(uart_tx)
    );

    uart_rx #(
        .CLK_FREQ(CLK_FREQ),
        .BAUD_RATE(BAUD_RATE)
    ) u_uart_rx (
        .clk(clk),
        .rst_n(rst_n),
        .rx_pin(uart_rx),
        .rx_data(rx_data),
        .rx_valid(rx_valid)
    );

endmodule