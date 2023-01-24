`timescale 1ns / 1ns

module LFSR
#(
    parameter N = 8,
    parameter START_VALUE = 8'b00000001,
    parameter TAPS = 8'b00000011
)
(
    input                       clk_i,
    input                       reset_ni,
    output  reg                 data_o
);

reg [N - 1 : 0] shift_reg;
reg             newBit;

always @(posedge clk_i) begin
    if (!reset_ni) begin
        data_o <= '0;
        for (integer i = 0; i < N; i++) begin
            shift_reg[i] <= (START_VALUE >> i) & 1'b1;
        end
        // $display("%x", shift_reg);
    end else begin
        data_o <= shift_reg[0];
        newBit = 0;
        for (integer i = 0; i < N; i++) begin
            newBit = newBit + (shift_reg[i] & ((TAPS >> i) & 1'b1));
        end
        // [R_(N-1) .... R_0] -> [newBit R_(N-1) .... R_1]
        shift_reg <= {newBit, shift_reg[N - 1 : 1]};
    end
end

endmodule