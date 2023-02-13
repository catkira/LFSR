`timescale 1ns / 1ns

module LFSR
#(
    parameter N = 8,
    parameter START_VALUE = 8'b00000001,
    parameter TAPS = 8'b00000011,
    parameter VARIABLE_CONFIG = 0
)
(
    input                       clk_i,
    input                       reset_ni,
    input                       load_config_i,
    input   wire [N - 1 : 0]    taps_i,
    input   wire [N - 1 : 0]    start_value_i,
    output  reg                 data_o,
    output  reg                 valid_o
);

reg [N - 1 : 0] shift_reg;
reg             newBit;

// only needed when VARIABLE_CONFIG = 1, should get optimized away if VARIABLE_CONFIG = 0
reg [N - 1 : 0] taps;

always @(posedge clk_i) begin
    if (!reset_ni) begin
        data_o <= '0;
        valid_o <= '0;
        if (VARIABLE_CONFIG) begin
            shift_reg <= '0;
        end else begin    
            for (integer i = 0; i < N; i++) begin
                shift_reg[i] <= (START_VALUE >> i) & 1'b1;
            end
        end
        // $display("%x", shift_reg);
    end else begin
        data_o <= shift_reg[0];
        if (VARIABLE_CONFIG) begin
            if (load_config_i) begin
                valid_o <= '0;
                taps <= taps_i;
                shift_reg <= start_value_i;
                $display("taps = %d  shift_reg = %d\n\n\n", taps, shift_reg);
            end else begin
                valid_o <= 1;
                newBit = 0;
                for (integer i = 0; i < N; i++) begin
                    newBit = newBit + (shift_reg[i] & taps[i]);
                end
                shift_reg <= {newBit, shift_reg[N - 1 : 1]};            
            end
        end else begin
            valid_o <= 1;
            newBit = 0;
            for (integer i = 0; i < N; i++) begin
                newBit = newBit + (shift_reg[i] & ((TAPS >> i) & 1'b1));
            end
            // [R_(N-1) .... R_0] -> [newBit R_(N-1) .... R_1]
            shift_reg <= {newBit, shift_reg[N - 1 : 1]};
        end
    end
end

endmodule