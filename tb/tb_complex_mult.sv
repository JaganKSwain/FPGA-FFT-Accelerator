// ==============================================================================
// tb_complex_mult.sv - Self-Checking Unit Test for 3-Stage Complex Multiplier
// Tests:
//   1. Identity multiplication: W^0 = (16384, 0)
//   2. -j multiplication: W_4^1 = (0, -16384)
//   3. Non-trivial angle: W_8^1 = (11585, -11585)
//   4. Negative full-scale boundary: -32768 x -32768
//   5. Continuous streaming with randomized inputs
// Pass Criteria: Exact 0-LSB match on 100% of test cycles
// ==============================================================================

`timescale 1ns/1ps

module tb_complex_mult;
    import fixed_point_pkg::*;

    logic       clk;
    logic       rst_n;
    logic       en;
    logic       valid_in;
    cplx_data_t b_in;
    cplx_tw_t   w_in;
    logic       valid_out;
    cplx_data_t p_out;

    // Instantiate Unit Under Test (UUT)
    complex_mult uut (
        .clk       (clk),
        .rst_n     (rst_n),
        .en        (en),
        .valid_in  (valid_in),
        .b_in      (b_in),
        .w_in      (w_in),
        .valid_out (valid_out),
        .p_out     (p_out)
    );

    // Clock generator: 100 MHz (10 ns period)
    always #5 clk = ~clk;

    // Pipeline delay tracking for expected values (3 cycle latency)
    typedef struct {
        logic valid;
        logic signed [15:0] exp_r;
        logic signed [15:0] exp_i;
    } exp_entry_t;

    exp_entry_t exp_pipe[3];

    // Reference model function for expected value in testbench
    function automatic void calc_expected(
        input  logic signed [15:0] br,
        input  logic signed [15:0] bi,
        input  logic signed [15:0] wr,
        input  logic signed [15:0] wi,
        output logic signed [15:0] exp_r,
        output logic signed [15:0] exp_i
    );
        logic signed [31:0] prr, pii, pri, pir;
        logic signed [32:0] raw_r, raw_i;
        prr = br * wr;
        pii = bi * wi;
        pri = br * wi;
        pir = bi * wr;
        raw_r = prr - pii;
        raw_i = pri + pir;
        exp_r = round_and_sat_cmult(raw_r);
        exp_i = round_and_sat_cmult(raw_i);
    endfunction

    int total_tests = 0;
    int pass_count  = 0;
    int fail_count  = 0;

    // Golden verification checker on every clock edge
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (int i = 0; i < 3; i++) begin
                exp_pipe[i].valid <= 1'b0;
                exp_pipe[i].exp_r <= '0;
                exp_pipe[i].exp_i <= '0;
            end
        end else if (en) begin
            // Check output against stage 2 of pipe
            if (exp_pipe[2].valid) begin
                total_tests++;
                if (valid_out && (p_out.r === exp_pipe[2].exp_r) && (p_out.i === exp_pipe[2].exp_i)) begin
                    pass_count++;
                end else begin
                    fail_count++;
                    $display("FAIL @ %0t ps: Expected (%0d, %0d), Got (%0d, %0d) [valid_out=%b]",
                             $time, exp_pipe[2].exp_r, exp_pipe[2].exp_i, p_out.r, p_out.i, valid_out);
                end
            end

            // Shift expected pipeline
            exp_pipe[2] <= exp_pipe[1];
            exp_pipe[1] <= exp_pipe[0];

            if (valid_in) begin
                exp_pipe[0].valid <= 1'b1;
                calc_expected(b_in.r, b_in.i, w_in.r, w_in.i, exp_pipe[0].exp_r, exp_pipe[0].exp_i);
            end else begin
                exp_pipe[0].valid <= 1'b0;
                exp_pipe[0].exp_r <= '0;
                exp_pipe[0].exp_i <= '0;
            end
        end
    end

    // Stimulus task
    task send_vector(
        input logic signed [15:0] br,
        input logic signed [15:0] bi,
        input logic signed [15:0] wr,
        input logic signed [15:0] wi
    );
        @(negedge clk);
        valid_in = 1'b1;
        b_in.r   = br;
        b_in.i   = bi;
        w_in.r   = wr;
        w_in.i   = wi;
        @(posedge clk);
    endtask

    // Main Test Sequence
    initial begin
        clk      = 0;
        rst_n    = 0;
        en       = 1;
        valid_in = 0;
        b_in     = '0;
        w_in     = '0;

        $display("------------------------------------------------------------");
        $display("  Starting tb_complex_mult Unit Test");
        $display("------------------------------------------------------------");

        // Reset pulse
        repeat(5) @(posedge clk);
        rst_n = 1;
        repeat(3) @(posedge clk);

        // Test 1: Identity W^0 = (16384, 0)
        $display("--> Test 1: W^0 Identity");
        send_vector(16'sd10000, 16'sd20000, 16'sd16384, 16'sd0);
        send_vector(-16'sd15000, 16'sd8000, 16'sd16384, 16'sd0);

        // Test 2: -j W_4^1 = (0, -16384)
        $display("--> Test 2: -j Rotation");
        send_vector(16'sd12000, 16'sd5000, 16'sd0, -16'sd16384);

        // Test 3: W_8^1 = (11585, -11585)
        $display("--> Test 3: W_8^1 45-degree Rotation");
        send_vector(16'sd16384, 16'sd0, 16'sd11585, -16'sd11585);

        // Test 4: Corner & Saturation Cases
        $display("--> Test 4: Full-Scale & Boundary Cases");
        send_vector(16'sh7FFF, 16'sh7FFF, 16'sd16384, 16'sd0);       // Max pos
        send_vector(-16'sd32768, -16'sd32768, 16'sd16384, 16'sd0);    // Max neg
        send_vector(-16'sd32768, 16'sd0, -16'sd16384, 16'sd0);        // -32768 * -1.0

        // Test 5: 50 Randomized Vectors Continuous Stream
        $display("--> Test 5: Continuous Random Stream");
        for (int i = 0; i < 50; i++) begin
            send_vector($urandom_range(0, 65535), $urandom_range(0, 65535),
                        $urandom_range(0, 32767) - 16384, $urandom_range(0, 32767) - 16384);
        end

        // Drain pipeline
        @(negedge clk);
        valid_in = 1'b0;
        repeat(10) @(posedge clk);

        $display("------------------------------------------------------------");
        $display("  tb_complex_mult Complete:");
        $display("  Total Checked: %0d | Passed: %0d | Failed: %0d", total_tests, pass_count, fail_count);
        $display("------------------------------------------------------------");

        if (fail_count == 0 && total_tests > 50) begin
            $display(">>> ALL tb_complex_mult TESTS PASSED (0 LSB MISMATCH) <<<");
            $finish(0);
        end else begin
            $display(">>> tb_complex_mult FAILED! <<<");
            $finish(1);
        end
    end

endmodule
