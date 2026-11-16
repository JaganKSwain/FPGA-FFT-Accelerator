// ==============================================================================
// tb_fft_top_n64.sv - 64-Point FFT Accelerator Testbench Wrapper (MVP Target)
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_top_n64;
    tb_fft_top #(
        .N(64)
    ) tb ();
endmodule
