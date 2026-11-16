// ==============================================================================
// butterfly.sv - 4-Stage Pipelined Radix-2 DIT Butterfly Unit
// Computes:
//   T  = B * W                 (3 cycles via complex_mult)
//   A' = (A + T) / 2           (1 cycle add + convergent round)
//   B' = (A - T) / 2           (1 cycle sub + convergent round)
// Latency: Exactly 4 clock cycles
// Address / Metadata tagging: Automatically pipelined through to output
// ==============================================================================

`timescale 1ns/1ps

module butterfly
    import fixed_point_pkg::*;
#(
    parameter int ADDR_W = 6 // Default for 64-point (depth 64)
)(
    input  logic                 clk,
    input  logic                 rst_n,
    input  logic                 en,
    input  logic                 valid_in,
    input  cplx_data_t           a_in,
    input  cplx_data_t           b_in,
    input  cplx_tw_t             w_in,
    input  logic [ADDR_W-1:0]    addr_p_in,
    input  logic [ADDR_W-1:0]    addr_q_in,
    
    output logic                 valid_out,
    output cplx_data_t           a_out,
    output cplx_data_t           b_out,
    output logic [ADDR_W-1:0]    addr_p_out,
    output logic [ADDR_W-1:0]    addr_q_out
);

    // -------------------------------------------------------------------------
    // Instantiation: 3-Stage Complex Multiplier
    // -------------------------------------------------------------------------
    logic       mult_valid_out;
    cplx_data_t t_prod;

    complex_mult u_cmult (
        .clk       (clk),
        .rst_n     (rst_n),
        .en        (en),
        .valid_in  (valid_in),
        .b_in      (b_in),
        .w_in      (w_in),
        .valid_out (mult_valid_out),
        .p_out     (t_prod)
    );

    // -------------------------------------------------------------------------
    // 3-Stage Delay Pipeline for Operand A and Addresses
    // Matches the 3-cycle latency of complex_mult
    // -------------------------------------------------------------------------
    cplx_data_t        a_d1, a_d2, a_d3;
    logic [ADDR_W-1:0] p_d1, p_d2, p_d3;
    logic [ADDR_W-1:0] q_d1, q_d2, q_d3;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_d1 <= '0; a_d2 <= '0; a_d3 <= '0;
            p_d1 <= '0; p_d2 <= '0; p_d3 <= '0;
            q_d1 <= '0; q_d2 <= '0; q_d3 <= '0;
        end else if (en) begin
            a_d1 <= a_in;
            a_d2 <= a_d1;
            a_d3 <= a_d2;

            p_d1 <= addr_p_in;
            p_d2 <= p_d1;
            p_d3 <= p_d2;

            q_d1 <= addr_q_in;
            q_d2 <= q_d1;
            q_d3 <= q_d2;
        end
    end

    // -------------------------------------------------------------------------
    // Stage 4: Butterfly Combination with 1/2 Stage Scaling
    // Add / Sub followed by 1-bit convergent rounding and saturation
    // -------------------------------------------------------------------------
    logic signed [DATA_W:0] sum_r, sum_i;
    logic signed [DATA_W:0] diff_r, diff_i;

    always_comb begin
        sum_r  = $signed(a_d3.r) + $signed(t_prod.r);
        sum_i  = $signed(a_d3.i) + $signed(t_prod.i);
        diff_r = $signed(a_d3.r) - $signed(t_prod.r);
        diff_i = $signed(a_d3.i) - $signed(t_prod.i);
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            a_out.r    <= '0;
            a_out.i    <= '0;
            b_out.r    <= '0;
            b_out.i    <= '0;
            addr_p_out <= '0;
            addr_q_out <= '0;
            valid_out  <= 1'b0;
        end else if (en) begin
            valid_out  <= mult_valid_out;
            addr_p_out <= p_d3;
            addr_q_out <= q_d3;

            if (mult_valid_out) begin
                a_out.r <= round_and_sat_bf(sum_r);
                a_out.i <= round_and_sat_bf(sum_i);
                b_out.r <= round_and_sat_bf(diff_r);
                b_out.i <= round_and_sat_bf(diff_i);
            end
        end
    end

endmodule: butterfly
