// ==============================================================================
// tb_butterfly.sv - Self-Checking Unit Test for 4-Stage Pipelined Butterfly
// Tests:
//   1. T = B * W computation through complex multiplier
//   2. A' = (A + T)/2 and B' = (A - T)/2 stage scaling with convergent round
//   3. Correct 4-cycle pipelining of data and address metadata
//   4. Boundary / full-scale saturation behavior
// Pass Criteria: Exact 0-LSB match on 100% of test cycles
// ==============================================================================

`timescale 1ns/1ps

module tb_butterfly;
    import fixed_point_pkg::*;

    localparam int ADDR_W = 6;

    logic                 clk;
    logic                 rst_n;
    logic                 en;
    logic                 valid_in;
    cplx_data_t           a_in;
    cplx_data_t           b_in;
    cplx_tw_t             w_in;
    logic [ADDR_W-1:0]    addr_p_in;
    logic [ADDR_W-1:0]    addr_q_in;

    logic                 valid_out;
    cplx_data_t           a_out;
    cplx_data_t           b_out;
    logic [ADDR_W-1:0]    addr_p_out;
    logic [ADDR_W-1:0]    addr_q_out;

    // Instantiate Butterfly UUT
    butterfly #(
        .ADDR_W(ADDR_W)
    ) uut (
        .clk        (clk),
        .rst_n      (rst_n),
        .en         (en),
        .valid_in   (valid_in),
        .a_in       (a_in),
        .b_in       (b_in),
        .w_in       (w_in),
        .addr_p_in  (addr_p_in),
        .addr_q_in  (addr_q_in),
        .valid_out  (valid_out),
        .a_out      (a_out),
        .b_out      (b_out),
        .addr_p_out (addr_p_out),
        .addr_q_out (addr_q_out)
    );

    // 100 MHz clock
    always #5 clk = ~clk;

    // 4-stage pipeline for expected outputs
    typedef struct {
        logic valid;
        logic signed [15:0] exp_ar, exp_ai;
        logic signed [15:0] exp_br, exp_bi;
        logic [ADDR_W-1:0]  exp_p, exp_q;
    } exp_bf_t;

    exp_bf_t exp_pipe[4];

    // Reference calculation function matching Python model
    function automatic void calc_bf_expected(
        input  logic signed [15:0] ar, ai,
        input  logic signed [15:0] br, bi,
        input  logic signed [15:0] wr, wi,
        input  logic [ADDR_W-1:0]  pin, qin,
        output logic signed [15:0] exp_ar, exp_ai,
        output logic signed [15:0] exp_br, exp_bi,
        output logic [ADDR_W-1:0]  exp_p, exp_q
    );
        logic signed [31:0] prr, pii, pri, pir;
        logic signed [32:0] raw_tr, raw_ti;
        logic signed [15:0] tr, ti;
        logic signed [16:0] sum_r, sum_i, diff_r, diff_i;

        prr = br * wr;
        pii = bi * wi;
        pri = br * wi;
        pir = bi * wr;
        raw_tr = prr - pii;
        raw_ti = pri + pir;

        tr = round_and_sat_cmult(raw_tr);
        ti = round_and_sat_cmult(raw_ti);

        sum_r  = ar + tr;
        sum_i  = ai + ti;
        diff_r = ar - tr;
        diff_i = ai - ti;

        exp_ar = round_and_sat_bf(sum_r);
        exp_ai = round_and_sat_bf(sum_i);
        exp_br = round_and_sat_bf(diff_r);
        exp_bi = round_and_sat_bf(diff_i);

        exp_p = pin;
        exp_q = qin;
    endfunction

    int total_tests = 0;
    int pass_count  = 0;
    int fail_count  = 0;

    // Checker logic on posedge
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 4; i++) begin
                exp_pipe[i].valid <= 1'b0;
            end
        end else if (en) begin
            if (exp_pipe[3].valid) begin
                total_tests++;
                if (valid_out &&
                    (a_out.r === exp_pipe[3].exp_ar) && (a_out.i === exp_pipe[3].exp_ai) &&
                    (b_out.r === exp_pipe[3].exp_br) && (b_out.i === exp_pipe[3].exp_bi) &&
                    (addr_p_out === exp_pipe[3].exp_p) && (addr_q_out === exp_pipe[3].exp_q)) begin
                    pass_count++;
                end else begin
                    fail_count++;
                    $display("FAIL @ %0t ps: A=(%0d,%0d), B=(%0d,%0d) P=%0d Q=%0d | Exp A=(%0d,%0d), B=(%0d,%0d) P=%0d Q=%0d",
                             $time, a_out.r, a_out.i, b_out.r, b_out.i, addr_p_out, addr_q_out,
                             exp_pipe[3].exp_ar, exp_pipe[3].exp_ai, exp_pipe[3].exp_br, exp_pipe[3].exp_bi,
                             exp_pipe[3].exp_p, exp_pipe[3].exp_q);
                end
            end

            // Shift expected pipe
            exp_pipe[3] <= exp_pipe[2];
            exp_pipe[2] <= exp_pipe[1];
            exp_pipe[1] <= exp_pipe[0];

            if (valid_in) begin
                exp_pipe[0].valid <= 1'b1;
                calc_bf_expected(a_in.r, a_in.i, b_in.r, b_in.i, w_in.r, w_in.i,
                                 addr_p_in, addr_q_in,
                                 exp_pipe[0].exp_ar, exp_pipe[0].exp_ai,
                                 exp_pipe[0].exp_br, exp_pipe[0].exp_bi,
                                 exp_pipe[0].exp_p, exp_pipe[0].exp_q);
            end else begin
                exp_pipe[0].valid <= 1'b0;
            end
        end
    end

    // Stimulus task
    task send_butterfly(
        input logic signed [15:0] ar, ai,
        input logic signed [15:0] br, bi,
        input logic signed [15:0] wr, wi,
        input logic [ADDR_W-1:0]  pin, qin
    );
        @(negedge clk);
        valid_in  = 1'b1;
        a_in.r    = ar;
        a_in.i    = ai;
        b_in.r    = br;
        b_in.i    = bi;
        w_in.r    = wr;
        w_in.i    = wi;
        addr_p_in = pin;
        addr_q_in = qin;
        @(posedge clk);
    endtask

    initial begin
        clk       = 0;
        rst_n     = 0;
        en        = 1;
        valid_in  = 0;
        a_in      = '0;
        b_in      = '0;
        w_in      = '0;
        addr_p_in = '0;
        addr_q_in = '0;

        $display("------------------------------------------------------------");
        $display("  Starting tb_butterfly Unit Test");
        $display("------------------------------------------------------------");

        repeat(5) @(posedge clk);
        rst_n = 1;
        repeat(3) @(posedge clk);

        // Test 1: Simple butterfly with W^0 = (16384, 0)
        // A = (1000, 0), B = (1000, 0) -> A' = 1000, B' = 0
        send_butterfly(16'sd1000, 16'sd0, 16'sd1000, 16'sd0, 16'sd16384, 16'sd0, 6'd0, 6'd32);

        // Test 2: Full-scale maximum input
        send_butterfly(16'sd32767, 16'sd32767, 16'sd32767, 16'sd32767, 16'sd16384, 16'sd0, 6'd1, 6'd33);

        // Test 3: Negative full-scale
        send_butterfly(-16'sd32768, -16'sd32768, -16'sd32768, -16'sd32768, 16'sd16384, 16'sd0, 6'd2, 6'd34);

        // Test 4: W_8^1 rotation
        send_butterfly(16'sd15000, -16'sd8000, 16'sd20000, 16'sd10000, 16'sd11585, -16'sd11585, 6'd3, 6'd35);

        // Test 5: 50 Randomized consecutive butterflies
        for (int i = 0; i < 50; i++) begin
            logic [ADDR_W-1:0] p_idx, q_idx;
            p_idx = ADDR_W'(i);
            q_idx = ADDR_W'(i + 32);
            send_butterfly($urandom_range(0, 65535), $urandom_range(0, 65535),
                           $urandom_range(0, 65535), $urandom_range(0, 65535),
                           $urandom_range(0, 32767) - 16384, $urandom_range(0, 32767) - 16384,
                           p_idx, q_idx);
        end

        // Drain pipeline
        @(negedge clk);
        valid_in = 1'b0;
        repeat(12) @(posedge clk);

        $display("------------------------------------------------------------");
        $display("  tb_butterfly Complete:");
        $display("  Total Checked: %0d | Passed: %0d | Failed: %0d", total_tests, pass_count, fail_count);
        $display("------------------------------------------------------------");

        if (fail_count == 0 && total_tests > 50) begin
            $display(">>> ALL tb_butterfly TESTS PASSED (0 LSB MISMATCH) <<<");
            $finish(0);
        end else begin
            $display(">>> tb_butterfly FAILED! <<<");
            $finish(1);
        end
    end

endmodule
