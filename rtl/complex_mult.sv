// ==============================================================================
// complex_mult.sv - 3-Stage Pipelined 4-DSP Complex Multiplier
// Computes: T = B * W
// Inputs:
//   b: Q1.15 complex data (16-bit real, 16-bit imag)
//   w: Q2.14 complex twiddle (16-bit real, 16-bit imag)
// Output:
//   p: Q1.15 complex product (convergent rounded from 29 frac bits to 15 frac bits)
// Latency: Exactly 3 clock cycles
// ==============================================================================

`timescale 1ns/1ps

module complex_mult
    import fixed_point_pkg::*;
(
    input  logic       clk,
    input  logic       rst_n,
    input  logic       en,          // Clock enable / pipeline enable
    input  logic       valid_in,
    input  cplx_data_t b_in,
    input  cplx_tw_t   w_in,
    output logic       valid_out,
    output cplx_data_t p_out
);

    // -------------------------------------------------------------------------
    // Stage 1 Registers: 4 Real Multiplications (16x16 -> 32)
    // Maps directly to 4 DSP48E1 slices
    // -------------------------------------------------------------------------
    logic signed [31:0] p_rr_s1;
    logic signed [31:0] p_ii_s1;
    logic signed [31:0] p_ri_s1;
    logic signed [31:0] p_ir_s1;
    logic               valid_s1;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p_rr_s1  <= '0;
            p_ii_s1  <= '0;
            p_ri_s1  <= '0;
            p_ir_s1  <= '0;
            valid_s1 <= 1'b0;
        end else if (en) begin
            valid_s1 <= valid_in;
            if (valid_in) begin
                p_rr_s1 <= $signed(b_in.r) * $signed(w_in.r);
                p_ii_s1 <= $signed(b_in.i) * $signed(w_in.i);
                p_ri_s1 <= $signed(b_in.r) * $signed(w_in.i);
                p_ir_s1 <= $signed(b_in.i) * $signed(w_in.r);
            end
        end
    end

    // -------------------------------------------------------------------------
    // Stage 2 Registers: Subtraction and Addition (33-bit signed accumulator)
    // -------------------------------------------------------------------------
    logic signed [32:0] t_r_raw_s2;
    logic signed [32:0] t_i_raw_s2;
    logic               valid_s2;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            t_r_raw_s2 <= '0;
            t_i_raw_s2 <= '0;
            valid_s2   <= 1'b0;
        end else if (en) begin
            valid_s2 <= valid_s1;
            if (valid_s1) begin
                t_r_raw_s2 <= p_rr_s1 - p_ii_s1;
                t_i_raw_s2 <= p_ri_s1 + p_ir_s1;
            end
        end
    end

    // -------------------------------------------------------------------------
    // Stage 3 Registers: Convergent Rounding (drop 14 fractional bits) & Clamp
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p_out.r   <= '0;
            p_out.i   <= '0;
            valid_out <= 1'b0;
        end else if (en) begin
            valid_out <= valid_s2;
            if (valid_s2) begin
                p_out.r <= round_and_sat_cmult(t_r_raw_s2);
                p_out.i <= round_and_sat_cmult(t_i_raw_s2);
            end
        end
    end

endmodule: complex_mult
