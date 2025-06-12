// Simple hello world module for testing cocotb setup
// This module implements a basic counter with enable and reset

module hello_world #(
    parameter WIDTH = 8
) (
    input  logic                clk,
    input  logic                rst_n,
    input  logic                enable,
    output logic [WIDTH-1:0]    counter,
    output logic                overflow
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            counter <= '0;
            overflow <= 1'b0;
        end else if (enable) begin
            if (counter == (2**WIDTH - 1)) begin
                counter <= '0;
                overflow <= 1'b1;
            end else begin
                counter <= counter + 1;
                overflow <= 1'b0;
            end
        end else begin
            overflow <= 1'b0;
        end
    end

    // Simple assertion for basic functionality
    /* verilator lint_off SYNCASYNCNET */
    assert property (@(posedge clk) disable iff (!rst_n)
        enable && (counter == (2**WIDTH - 1)) |=> (counter == 0))
    else $error("Counter overflow behavior incorrect");
    /* verilator lint_on SYNCASYNCNET */

endmodule
