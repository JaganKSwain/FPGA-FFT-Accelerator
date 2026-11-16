// ==============================================================================
// fft_top.sv - Top-Level Radix-2 DIT FFT Accelerator
// Architecture:
//   - Parameterized N in {4, 8, 16, 32, 64} (Default: 64)
//   - AXI4-Stream valid/ready handshaking for input & output
//   - In-place single Radix-2 butterfly engine with stage scaling
//   - Conflict-free scheduled True Dual-Port Block RAM
//   - Synchronous Twiddle ROM
// ==============================================================================

`timescale 1ns/1ps

module fft_top
    import fixed_point_pkg::*;
#(
    parameter int N         = 64,
    parameter int LOG2_N    = $clog2(N),
    parameter     INIT_FILE = "tb/vectors/twiddle_rom_64.mem"
)(
    input  logic        clk,
    input  logic        rst_n,

    // AXI4-Stream Slave Interface (Input Samples)
    input  logic [31:0] s_axis_tdata,   // [31:16] Real, [15:0] Imag
    input  logic        s_axis_tvalid,
    output logic        s_axis_tready,
    input  logic        s_axis_tlast,

    // AXI4-Stream Master Interface (Output Bins)
    output logic [31:0] m_axis_tdata,   // [31:16] Real, [15:0] Imag
    output logic        m_axis_tvalid,
    input  logic        m_axis_tready,
    output logic        m_axis_tlast,

    // Status Flags
    output logic        busy,
    output logic        done
);

    // -------------------------------------------------------------------------
    // Internal Interconnect Signals
    // -------------------------------------------------------------------------
    // RAM Signals
    logic              ram_ena, ram_wea;
    logic [LOG2_N-1:0] ram_addra;
    cplx_data_t        ram_dina, ram_douta;

    logic              ram_enb, ram_web;
    logic [LOG2_N-1:0] ram_addrb;
    cplx_data_t        ram_dinb, ram_doutb;

    logic              ram_sel_input;

    // Twiddle ROM Signals
    logic              rom_en;
    logic [LOG2_N-1:0] rom_addr;
    cplx_tw_t          tw_data;

    // Butterfly Signals
    logic              bf_en;
    logic              bf_valid_in;
    logic [LOG2_N-1:0] bf_addr_p_in, bf_addr_q_in;
    logic              bf_valid_out;
    cplx_data_t        bf_a_out, bf_b_out;
    logic [LOG2_N-1:0] bf_addr_p_out, bf_addr_q_out;

    // -------------------------------------------------------------------------
    // FFT Controller FSM
    // -------------------------------------------------------------------------
    fft_controller #(
        .N      (N),
        .LOG2_N (LOG2_N)
    ) u_controller (
        .clk           (clk),
        .rst_n         (rst_n),
        .s_axis_tvalid (s_axis_tvalid),
        .s_axis_tready (s_axis_tready),
        .s_axis_tlast  (s_axis_tlast),
        .m_axis_tvalid (m_axis_tvalid),
        .m_axis_tready (m_axis_tready),
        .m_axis_tlast  (m_axis_tlast),
        .ram_ena       (ram_ena),
        .ram_wea       (ram_wea),
        .ram_addra     (ram_addra),
        .ram_enb       (ram_enb),
        .ram_web       (ram_web),
        .ram_addrb     (ram_addrb),
        .ram_sel_input (ram_sel_input),
        .rom_en        (rom_en),
        .rom_addr      (rom_addr),
        .bf_en         (bf_en),
        .bf_valid_in   (bf_valid_in),
        .bf_addr_p_in  (bf_addr_p_in),
        .bf_addr_q_in  (bf_addr_q_in),
        .bf_valid_out  (bf_valid_out),
        .bf_addr_p_out (bf_addr_p_out),
        .bf_addr_q_out (bf_addr_q_out),
        .busy          (busy),
        .done          (done)
    );

    // -------------------------------------------------------------------------
    // RAM Data Routing (Multiplex input stream vs Butterfly outputs)
    // -------------------------------------------------------------------------
    cplx_data_t s_axis_cplx;
    assign s_axis_cplx.r = s_axis_tdata[31:16];
    assign s_axis_cplx.i = s_axis_tdata[15:0];

    assign ram_dina = ram_sel_input ? s_axis_cplx : bf_a_out;
    assign ram_dinb = bf_b_out;

    // Output stream data packed from RAM Port A read output
    assign m_axis_tdata = {ram_douta.r, ram_douta.i};

    // -------------------------------------------------------------------------
    // True Dual-Port Block RAM
    // -------------------------------------------------------------------------
    data_ram #(
        .DEPTH  (N),
        .ADDR_W (LOG2_N)
    ) u_data_ram (
        .clk   (clk),
        .ena   (ram_ena),
        .wea   (ram_wea),
        .addra (ram_addra),
        .dina  (ram_dina),
        .douta (ram_douta),
        .enb   (ram_enb),
        .web   (ram_web),
        .addrb (ram_addrb),
        .dinb  (ram_dinb),
        .doutb (ram_doutb)
    );

    // -------------------------------------------------------------------------
    // Twiddle ROM
    // -------------------------------------------------------------------------
    twiddle_rom #(
        .N         (N),
        .DEPTH     (N / 2),
        .ADDR_W    (LOG2_N - 1),
        .INIT_FILE (INIT_FILE)
    ) u_twiddle_rom (
        .clk    (clk),
        .en     (rom_en),
        .addr   (rom_addr[LOG2_N-2:0]),
        .tw_out (tw_data)
    );

    // -------------------------------------------------------------------------
    // Butterfly Arithmetic Unit
    // -------------------------------------------------------------------------
    butterfly #(
        .ADDR_W (LOG2_N)
    ) u_butterfly (
        .clk        (clk),
        .rst_n      (rst_n),
        .en         (bf_en),
        .valid_in   (bf_valid_in),
        .a_in       (ram_douta),
        .b_in       (ram_doutb),
        .w_in       (tw_data),
        .addr_p_in  (bf_addr_p_in),
        .addr_q_in  (bf_addr_q_in),
        .valid_out  (bf_valid_out),
        .a_out      (bf_a_out),
        .b_out      (bf_b_out),
        .addr_p_out (bf_addr_p_out),
        .addr_q_out (bf_addr_q_out)
    );

endmodule: fft_top
