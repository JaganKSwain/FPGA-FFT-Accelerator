// ==============================================================================
// tb_fft_top_n8.sv - 8-Point FFT Accelerator Testbench Wrapper
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_top_n8;
    tb_fft_top #(
        .N(8)
    ) tb ();
endmodule
