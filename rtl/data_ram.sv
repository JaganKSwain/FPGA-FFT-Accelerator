// ==============================================================================
// data_ram.sv - True Dual-Port Synchronous Block RAM (TDP BRAM)
// Infers dedicated Block RAM on Xilinx 7-series (RAMB18E1/RAMB36E1).
// Ports:
//   Port A: Read/Write (Width: 32 bits = 16-bit real + 16-bit imag)
//   Port B: Read/Write (Width: 32 bits = 16-bit real + 16-bit imag)
// Latency: 1 clock cycle
// ==============================================================================

`timescale 1ns/1ps

module data_ram
    import fixed_point_pkg::*;
#(
    parameter int DEPTH  = 64,
    parameter int ADDR_W = $clog2(DEPTH)
)(
    input  logic              clk,
    
    // Port A
    input  logic              ena,
    input  logic              wea,
    input  logic [ADDR_W-1:0] addra,
    input  cplx_data_t        dina,
    output cplx_data_t        douta,

    // Port B
    input  logic              enb,
    input  logic              web,
    input  logic [ADDR_W-1:0] addrb,
    input  cplx_data_t        dinb,
    output cplx_data_t        doutb
);

    // RAM array: 32 bits wide, DEPTH entries
    logic [31:0] ram [0:DEPTH-1];

    logic [31:0] rdata_a;
    logic [31:0] rdata_b;

    // Port A synchronous logic
    always_ff @(posedge clk) begin
        if (ena) begin
            if (wea) begin
                ram[addra] <= {dina.r, dina.i};
            end
            rdata_a <= ram[addra];
        end
    end

    // Port B synchronous logic
    always_ff @(posedge clk) begin
        if (enb) begin
            if (web) begin
                ram[addrb] <= {dinb.r, dinb.i};
            end
            rdata_b <= ram[addrb];
        end
    end

    assign douta.r = $signed(rdata_a[31:16]);
    assign douta.i = $signed(rdata_a[15:0]);

    assign doutb.r = $signed(rdata_b[31:16]);
    assign doutb.i = $signed(rdata_b[15:0]);

endmodule: data_ram
