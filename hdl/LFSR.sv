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
reg             reg0;

always @(posedge clk_i) begin
    if (!reset_ni) begin
        data_o <= '0;
        for (integer i = 0; i < N; i++) begin
            shift_reg[i] <= (START_VALUE >> i) & 1'b1;
        end
    end else begin
        data_o <= shift_reg[N - 1];
        reg0 = 0;
        for (integer i = 0; i < N; i++) begin
            reg0 = reg0 + shift_reg[i] & ((TAPS >> i) & 1'b1);
        end
        shift_reg <= {shift_reg[N - 2 : 0], reg0};
    end
end

endmodule