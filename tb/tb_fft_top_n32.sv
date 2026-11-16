// ==============================================================================
// tb_fft_top_n32.sv - 32-Point FFT Accelerator Testbench Wrapper
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_top_n32;
    tb_fft_top #(
        .N(32)
    ) tb ();
endmodule
