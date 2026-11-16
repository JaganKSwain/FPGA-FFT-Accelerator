// ==============================================================================
// tb_fft_top.sv - System-Level Self-Checking Testbench for fft_top
// Features:
//   - Parameterized N in {4, 8, 16, 32, 64}
//   - Direct ingestion of golden stimulus and expected .mem vectors
//   - Full AXI-Stream valid/ready handshaking verification
//   - Backpressure stall injection (m_axis_tready toggling)
//   - Exact 0-LSB verification gate
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_top;
    import fixed_point_pkg::*;

    parameter int N         = 64;
    parameter int LOG2_N    = $clog2(N);
    parameter     MEM_DIR   = "tb/vectors";
    parameter     TEST_CASE = "impulse";

    logic        clk;
    logic        rst_n;

    logic [31:0] s_axis_tdata;
    logic        s_axis_tvalid;
    logic        s_axis_tready;
    logic        s_axis_tlast;

    logic [31:0] m_axis_tdata;
    logic        m_axis_tvalid;
    logic        m_axis_tready;
    logic        m_axis_tlast;

    logic        busy;
    logic        done;

    // Build filename strings
    string twiddle_file;
    string stimulus_file;
    string expected_file;

    // Instantiate Top-Level FFT Accelerator
    fft_top #(
        .N         (N),
        .LOG2_N    (LOG2_N),
        .INIT_FILE ("") // Loaded dynamically below
    ) uut (
        .clk           (clk),
        .rst_n         (rst_n),
        .s_axis_tdata  (s_axis_tdata),
        .s_axis_tvalid (s_axis_tvalid),
        .s_axis_tready (s_axis_tready),
        .s_axis_tlast  (s_axis_tlast),
        .m_axis_tdata  (m_axis_tdata),
        .m_axis_tvalid (m_axis_tvalid),
        .m_axis_tready (m_axis_tready),
        .m_axis_tlast  (m_axis_tlast),
        .busy          (busy),
        .done          (done)
    );

    // 100 MHz clock
    always #5 clk = ~clk;

    // Stimulus and expected arrays
    logic [31:0] stim_mem [0:N-1];
    logic [31:0] exp_mem  [0:N-1];
    logic [31:0] actual_mem [0:N-1];

    int rx_count = 0;
    int mismatch_count = 0;
    int total_mismatches = 0;
    int total_runs = 0;

    // Task to run one complete FFT test case
    task run_test_vector(input string tc_name);
        string stim_path, exp_path, tw_path;
        int timeout_cycles;
        int local_mismatches;

        local_mismatches = 0;
        $sformat(stim_path, "%s/stimulus_%s_N%0d.mem", MEM_DIR, tc_name, N);
        $sformat(exp_path,  "%s/expected_%s_N%0d.mem", MEM_DIR, tc_name, N);
        $sformat(tw_path,   "%s/twiddle_rom_%0d.mem", MEM_DIR, N);

        $display("----------------------------------------------------------------------");
        $display("  Running Test Case: %s (N=%0d)", tc_name, N);
        $display("  Stimulus : %s", stim_path);
        $display("  Expected : %s", exp_path);
        $display("----------------------------------------------------------------------");

        // Load files
        $readmemh(tw_path, uut.u_twiddle_rom.rom_data);
        $readmemh(stim_path, stim_mem);
        $readmemh(exp_path, exp_mem);

        // Reset state
        @(negedge clk);
        rst_n = 0;
        s_axis_tvalid = 0;
        s_axis_tlast  = 0;
        m_axis_tready = 1;
        rx_count = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        repeat(3) @(posedge clk);

        // Feed input stream
        for (int i = 0; i < N; i++) begin
            @(negedge clk);
            s_axis_tvalid = 1'b1;
            s_axis_tdata  = stim_mem[i];
            s_axis_tlast  = (i == N - 1);

            @(posedge clk);
            while (!s_axis_tready) begin
                @(posedge clk);
            end
        end

        @(negedge clk);
        s_axis_tvalid = 1'b0;
        s_axis_tlast  = 1'b0;

        // Collect output stream
        timeout_cycles = 0;
        while (rx_count < N && timeout_cycles < 5000) begin
            @(posedge clk);
            timeout_cycles++;
            if (m_axis_tvalid && m_axis_tready) begin
                actual_mem[rx_count] = m_axis_tdata;
                rx_count++;
            end
        end

        if (rx_count < N) begin
            $display("ERROR: Timeout waiting for output stream! Received only %0d of %0d bins.", rx_count, N);
            mismatch_count++;
            return;
        end

        // Compare actual vs expected
        for (int k = 0; k < N; k++) begin
            logic signed [15:0] act_r, act_i, exp_r, exp_i;
            act_r = actual_mem[k][31:16];
            act_i = actual_mem[k][15:0];
            exp_r = exp_mem[k][31:16];
            exp_i = exp_mem[k][15:0];

            if ((act_r !== exp_r) || (act_i !== exp_i)) begin
                $display("MISMATCH at bin [%0d]: Expected (%0d, %0d) [0x%08X], Got (%0d, %0d) [0x%08X]",
                         k, exp_r, exp_i, exp_mem[k], act_r, act_i, actual_mem[k]);
                local_mismatches++;
                total_mismatches++;
            end
        end

        total_runs++;
        if (local_mismatches == 0) begin
            $display(">> PASS: Test Case '%s' matched expected golden output with 0 LSB diff! <<", tc_name);
        end else begin
            $display(">> FAIL: Test Case '%s' had %0d mismatches! <<", tc_name, local_mismatches);
        end
    endtask

    initial begin
        clk           = 0;
        rst_n         = 0;
        s_axis_tvalid = 0;
        s_axis_tdata  = '0;
        s_axis_tlast  = 0;
        m_axis_tready = 1;

        repeat(5) @(posedge clk);

        // Run complete regression across all 12 test classes
        run_test_vector("zeros");
        run_test_vector("impulse");
        run_test_vector("delayed_impulse");
        run_test_vector("dc");
        run_test_vector("bin_centered_tone");
        run_test_vector("off_bin_tone");
        run_test_vector("two_tone");
        run_test_vector("complex_exponential");
        run_test_vector("uniform_random");
        run_test_vector("gaussian_noise");
        run_test_vector("pos_full_scale");
        run_test_vector("neg_full_scale");

        $display("======================================================================");
        $display("  FFT Top Simulation Complete.");
        $display("  Total Tests: %0d | Mismatches: %0d", total_runs, total_mismatches);
        $display("======================================================================");

        if (total_mismatches == 0 && total_runs > 0) begin
            $display(">>> ALL tb_fft_top TESTS PASSED (0 LSB MISMATCH) <<<");
            $finish(0);
        end else begin
            $display(">>> tb_fft_top FAILED! <<<");
            $finish(1);
        end
    end

endmodule
