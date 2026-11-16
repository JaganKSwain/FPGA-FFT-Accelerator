// ==============================================================================
// twiddle_rom.sv - Parameterized Synchronous Twiddle Factor ROM
// Initialized from .mem hex files via $readmemh.
// Twiddle width: 16-bit real, 16-bit imag packed into 32-bit word:
//   [31:16] = Real (Q2.14)
//   [15:0]  = Imag (Q2.14)
// Latency: 1 clock cycle (synchronous read)
// ==============================================================================

`timescale 1ns/1ps

module twiddle_rom
    import fixed_point_pkg::*;
#(
    parameter int N          = 64,
    parameter int DEPTH      = N / 2,
    parameter int ADDR_W     = (DEPTH > 1) ? $clog2(DEPTH) : 1,
    parameter     INIT_FILE  = "twiddle_rom_64.mem"
)(
    input  logic              clk,
    input  logic              en,
    input  logic [ADDR_W-1:0] addr,
    output cplx_tw_t          tw_out
);

    // ROM storage
    logic [31:0] rom_data [0:DEPTH-1];
    logic [31:0] rdata_reg;

    initial begin
        if (INIT_FILE != "") begin
            $readmemh(INIT_FILE, rom_data);
        end
    end

    always_ff @(posedge clk) begin
        if (en) begin
            rdata_reg <= rom_data[addr];
        end
    end

    // Unpack 32-bit word into signed real and imag
    assign tw_out.r = $signed(rdata_reg[31:16]);
    assign tw_out.i = $signed(rdata_reg[15:0]);

endmodule: twiddle_rom
