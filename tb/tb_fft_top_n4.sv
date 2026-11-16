// ==============================================================================
// tb_fft_top_n4.sv - 4-Point FFT Accelerator Testbench Wrapper
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_top_n4;
    tb_fft_top #(
        .N(4)
    ) tb ();
endmodule
