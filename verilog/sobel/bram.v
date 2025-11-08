// Generic inferred true dual-port block RAM with Gowin-style control signals.
// Behavioural model keeps simulation simple while hinting the synthesiser
// to map the storage into block RAM / SSRAM resources.

module bram #(
    parameter ADDR_WIDTH = 10,
    parameter DATA_WIDTH = 8
)(
    output reg  [DATA_WIDTH-1:0] dout,
    input  wire                   clk,
    input  wire                   cea,
    input  wire                   reseta,
    input  wire [ADDR_WIDTH-1:0]  ada,
    input  wire [DATA_WIDTH-1:0]  din,
    input  wire                   ceb,
    input  wire                   resetb,
    input  wire                   oce,
    input  wire [ADDR_WIDTH-1:0]  adb
);
    localparam integer DEPTH = 1 << ADDR_WIDTH;

    // Instruct Gowin tools to infer simple dual-port block RAM.
    (* ram_style = "block", syn_ramstyle = "block_ram" *)
    reg [DATA_WIDTH-1:0] mem [0:DEPTH-1];
    reg [DATA_WIDTH-1:0] dout_reg;

    integer idx;

    initial begin
        for (idx = 0; idx < DEPTH; idx = idx + 1) begin
            mem[idx] = {DATA_WIDTH{1'b0}};
        end
    dout_reg = {DATA_WIDTH{1'b0}};
    dout     = {DATA_WIDTH{1'b0}};
    end

    // Port A write path. reseta acts as a synchronous write enable gate.
    always @(posedge clk) begin
        if (!reseta && cea) begin
            mem[ada] <= din;
        end
    end

    // Port B read path follows Gowin SDPB timing (read-first behaviour).
    always @(posedge clk) begin
        if (resetb) begin
            dout_reg <= {DATA_WIDTH{1'b0}};
            dout     <= {DATA_WIDTH{1'b0}};
        end else begin
            if (ceb) begin
                dout_reg <= mem[adb];
            end
            if (oce) begin
                dout <= dout_reg;
            end
        end
    end

endmodule

