// ==============================================================================
// tb_fft_top_n16.sv - 16-Point FFT Accelerator Testbench Wrapper
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_top_n16;
    tb_fft_top #(
        .N(16)
    ) tb ();
endmodule
