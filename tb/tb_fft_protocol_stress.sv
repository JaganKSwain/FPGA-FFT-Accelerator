// ==============================================================================
// tb_fft_protocol_stress.sv - Protocol Stress & Timing Benchmark Testbench
// Verifies:
//   1. Randomized s_axis_tvalid bubbles / mid-stream pauses
//   2. Randomized m_axis_tready downstream backpressure stalls
//   3. Back-to-back contiguous multi-frame processing
//   4. Mid-frame synchronous reset & clean recovery
//   5. Cycle-accurate latency profiling (LOAD, COMPUTE, DRAIN, UNLOAD)
// ==============================================================================

`timescale 1ns/1ps

module tb_fft_protocol_stress;
    import fixed_point_pkg::*;

    parameter int N      = 64;
    parameter int LOG2_N = $clog2(N);

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

    // Instantiate 64-Point FFT Accelerator
    fft_top #(
        .N         (N),
        .LOG2_N    (LOG2_N),
        .INIT_FILE ("tb/vectors/twiddle_rom_64.mem")
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

    // 100 MHz clock (10.0 ns period)
    always #5 clk = ~clk;

    // Test arrays
    logic [31:0] stim_mem [0:N-1];
    logic [31:0] exp_mem  [0:N-1];
    logic [31:0] rx_mem   [0:N-1];

    int stress_mismatches = 0;

    // Timing profile variables
    longint t_start, t_load_done, t_compute_done, t_unload_done;
    int cycles_load, cycles_compute, cycles_unload, cycles_total;

    // -------------------------------------------------------------------------
    // Helper Task: Send Frame with Optional Valid Gaps
    // -------------------------------------------------------------------------
    task send_frame(input bit inject_gaps);
        int tx_idx = 0;
        while (tx_idx < N) begin
            @(negedge clk);
            if (inject_gaps && ($urandom_range(0, 3) == 0)) begin
                // Random bubble / pause
                s_axis_tvalid = 1'b0;
                s_axis_tdata  = '0;
                s_axis_tlast  = 1'b0;
                @(posedge clk);
            end else begin
                s_axis_tvalid = 1'b1;
                s_axis_tdata  = stim_mem[tx_idx];
                s_axis_tlast  = (tx_idx == N - 1);
                @(posedge clk);
                if (s_axis_tready) begin
                    tx_idx++;
                end
            end
        end
        @(negedge clk);
        s_axis_tvalid = 1'b0;
        s_axis_tlast  = 1'b0;
    endtask

    // -------------------------------------------------------------------------
    // Helper Task: Receive Frame with Optional Backpressure Stalls
    // -------------------------------------------------------------------------
    task receive_frame(input bit inject_stalls);
        int rx_idx = 0;
        int watchdog = 0;
        while (rx_idx < N && watchdog < 10000) begin
            @(negedge clk);
            if (inject_stalls && ($urandom_range(0, 2) == 0)) begin
                m_axis_tready = 1'b0; // Downstream not ready
            end else begin
                m_axis_tready = 1'b1;
            end

            @(posedge clk);
            watchdog++;
            if (m_axis_tvalid && m_axis_tready) begin
                rx_mem[rx_idx] = m_axis_tdata;
                rx_idx++;
            end
        end

        if (rx_idx < N) begin
            $display("ERROR: Watchdog timeout in receive_frame! (rx_idx=%0d)", rx_idx);
            stress_mismatches++;
        end
    endtask

    // -------------------------------------------------------------------------
    // Main Stress Verification Sequence
    // -------------------------------------------------------------------------
    initial begin
        clk           = 0;
        rst_n         = 0;
        s_axis_tvalid = 0;
        s_axis_tdata  = '0;
        s_axis_tlast  = 0;
        m_axis_tready = 1;

        $readmemh("tb/vectors/stimulus_bin_centered_tone_N64.mem", stim_mem);
        $readmemh("tb/vectors/expected_bin_centered_tone_N64.mem", exp_mem);

        repeat(10) @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);

        $display("======================================================================");
        $display("  Starting Protocol Stress & Latency Profiling (N=64, Artix-7)");
        $display("======================================================================");

        // ---------------------------------------------------------------------
        // Test 1: Ideal Baseline & Cycle-Accurate Latency Profiling
        // ---------------------------------------------------------------------
        $display("--> Test 1: Cycle-Accurate Latency Profiling (No Stalls)...");
        t_start = $time / 10; // Clock cycles (10 ns clock)

        // Fork sender and receiver
        fork
            begin
                send_frame(0);
                t_load_done = $time / 10;
            end
            begin
                // Wait for compute to finish (when m_axis_tvalid first asserts)
                @(posedge m_axis_tvalid);
                t_compute_done = $time / 10;
                receive_frame(0);
                t_unload_done = $time / 10;
            end
        join

        cycles_load    = int'(t_load_done - t_start);
        cycles_compute = int'(t_compute_done - t_load_done);
        cycles_unload  = int'(t_unload_done - t_compute_done);
        cycles_total   = int'(t_unload_done - t_start);

        $display("    LOAD Latency     : %0d clock cycles (%0.2f us)", cycles_load, cycles_load * 0.01);
        $display("    COMPUTE Latency  : %0d clock cycles (%0.2f us) [192 BFs + inter-stage drains]", cycles_compute, cycles_compute * 0.01);
        $display("    UNLOAD Latency   : %0d clock cycles (%0.2f us)", cycles_unload, cycles_unload * 0.01);
        $display("    TOTAL Frame Time : %0d clock cycles (%0.2f us)", cycles_total, cycles_total * 0.01);

        // Verify output correctness
        for (int k = 0; k < N; k++) begin
            if (rx_mem[k] !== exp_mem[k]) begin
                $display("ERROR in Test 1 at bin [%0d]: Expected 0x%08X, Got 0x%08X", k, exp_mem[k], rx_mem[k]);
                stress_mismatches++;
            end
        end
        if (stress_mismatches == 0) begin
            $display("    >> Test 1 Passed (0 LSB error).");
        end

        // ---------------------------------------------------------------------
        // Test 2: Randomized Input Bubbles (s_axis_tvalid dropping)
        // ---------------------------------------------------------------------
        $display("\n--> Test 2: Ingestion with Randomized Input Bubbles (s_axis_tvalid gaps)...");
        fork
            send_frame(1); // With gaps
            receive_frame(0);
        join

        for (int k = 0; k < N; k++) begin
            if (rx_mem[k] !== exp_mem[k]) begin
                $display("ERROR in Test 2 at bin [%0d]: Expected 0x%08X, Got 0x%08X", k, exp_mem[k], rx_mem[k]);
                stress_mismatches++;
            end
        end
        if (stress_mismatches == 0) begin
            $display("    >> Test 2 Passed: Protocol handled input bubbles cleanly.");
        end

        // ---------------------------------------------------------------------
        // Test 3: Randomized Output Backpressure (m_axis_tready stalls)
        // ---------------------------------------------------------------------
        $display("\n--> Test 3: Egress with Downstream Backpressure (m_axis_tready stalls)...");
        fork
            send_frame(0);
            receive_frame(1); // With stalls
        join

        for (int k = 0; k < N; k++) begin
            if (rx_mem[k] !== exp_mem[k]) begin
                $display("ERROR in Test 3 at bin [%0d]: Expected 0x%08X, Got 0x%08X", k, exp_mem[k], rx_mem[k]);
                stress_mismatches++;
            end
        end
        if (stress_mismatches == 0) begin
            $display("    >> Test 3 Passed: Protocol handled downstream backpressure cleanly.");
        end

        // ---------------------------------------------------------------------
        // Test 4: Back-to-Back Contiguous Multi-Frame Execution
        // ---------------------------------------------------------------------
        $display("\n--> Test 4: Back-to-Back Continuous Multi-Frame Execution (3 Frames)...");
        for (int f = 0; f < 3; f++) begin
            fork
                send_frame(0);
                receive_frame(0);
            join
            for (int k = 0; k < N; k++) begin
                if (rx_mem[k] !== exp_mem[k]) begin
                    $display("ERROR in Test 4 Frame %0d at bin [%0d]", f, k);
                    stress_mismatches++;
                end
            end
        end
        if (stress_mismatches == 0) begin
            $display("    >> Test 4 Passed: 3 contiguous back-to-back frames succeeded with 0 LSB diff.");
        end

        // ---------------------------------------------------------------------
        // Test 5: Mid-Frame Reset Recovery
        // ---------------------------------------------------------------------
        $display("\n--> Test 5: Mid-Frame Synchronous Reset Recovery...");
        // Start sending frame
        @(negedge clk);
        s_axis_tvalid = 1;
        s_axis_tdata = stim_mem[0];
        repeat(20) @(posedge clk);
        // Assert synchronous reset mid-flight
        @(negedge clk);
        rst_n = 0;
        s_axis_tvalid = 0;
        repeat(5) @(posedge clk);
        rst_n = 1;
        repeat(5) @(posedge clk);

        // Verify clean resumption on fresh frame
        fork
            send_frame(0);
            receive_frame(0);
        join
        for (int k = 0; k < N; k++) begin
            if (rx_mem[k] !== exp_mem[k]) begin
                $display("ERROR in Test 5 Post-Reset at bin [%0d]", k);
                stress_mismatches++;
            end
        end
        if (stress_mismatches == 0) begin
            $display("    >> Test 5 Passed: Mid-frame reset recovered cleanly.");
        end

        $display("\n======================================================================");
        $display("  Protocol Stress Testing Complete.");
        $display("  Total Mismatches: %0d", stress_mismatches);
        $display("======================================================================");

        if (stress_mismatches == 0) begin
            $display(">>> ALL PROTOCOL STRESS TESTS PASSED (0 LSB MISMATCH) <<<");
            $finish(0);
        end else begin
            $display(">>> PROTOCOL STRESS TESTS FAILED! <<<");
            $finish(1);
        end
    end

endmodule
