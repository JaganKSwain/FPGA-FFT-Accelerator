// ==============================================================================
// fft_controller.sv - FSM & Address Generation for Iterative Radix-2 DIT FFT
// States:
//   IDLE    : Awaiting input stream frame
//   LOAD    : Stream in N samples directly into bit-reversed RAM addresses
//   COMPUTE : 2-cycle scheduled butterfly compute (Even cycle: Read, Odd cycle: Write)
//   DRAIN   : Flush arithmetic pipeline at stage boundaries
//   UNLOAD  : Stream out N frequency bins in natural order with valid/ready
// ==============================================================================

`timescale 1ns/1ps

module fft_controller
    import fixed_point_pkg::*;
#(
    parameter int N      = 64,
    parameter int LOG2_N = $clog2(N)
)(
    input  logic              clk,
    input  logic              rst_n,

    // AXI-Stream Slave (Input)
    input  logic              s_axis_tvalid,
    output logic              s_axis_tready,
    input  logic              s_axis_tlast,

    // AXI-Stream Master (Output)
    output logic              m_axis_tvalid,
    input  logic              m_axis_tready,
    output logic              m_axis_tlast,

    // RAM Control Ports
    output logic              ram_ena,
    output logic              ram_wea,
    output logic [LOG2_N-1:0] ram_addra,
    output logic              ram_enb,
    output logic              ram_web,
    output logic [LOG2_N-1:0] ram_addrb,
    output logic              ram_sel_input,

    // Twiddle ROM Control
    output logic              rom_en,
    output logic [LOG2_N-1:0] rom_addr,

    // Butterfly Unit Control
    output logic              bf_en,
    output logic              bf_valid_in,
    output logic [LOG2_N-1:0] bf_addr_p_in,
    output logic [LOG2_N-1:0] bf_addr_q_in,
    input  logic              bf_valid_out,
    input  logic [LOG2_N-1:0] bf_addr_p_out,
    input  logic [LOG2_N-1:0] bf_addr_q_out,

    // Status
    output logic              busy,
    output logic              done
);

    // Bit-reversal function for LOG2_N bits
    function automatic logic [LOG2_N-1:0] bit_rev(input logic [LOG2_N-1:0] in);
        logic [LOG2_N-1:0] out;
        for (int i = 0; i < LOG2_N; i++) begin
            out[i] = in[LOG2_N - 1 - i];
        end
        return out;
    endfunction

    // FSM States
    typedef enum logic [2:0] {
        ST_IDLE,
        ST_LOAD,
        ST_COMPUTE,
        ST_DRAIN,
        ST_UNLOAD,
        ST_DONE
    } state_t;

    state_t state, state_next;

    // Counters sized with extra bit to prevent overflow
    logic [LOG2_N:0]   load_cnt;
    logic [LOG2_N:0]   unload_cnt;
    logic [3:0]        stage_cnt;      // 1 to LOG2_N
    logic [LOG2_N:0]   bf_cnt;         // 0 to (N/2 - 1)
    logic              phase;          // 0: Read phase, 1: Launch phase
    logic [LOG2_N:0]   written_cnt;    // 0 to N/2

    // Derived butterfly address logic
    logic [LOG2_N-1:0] half_len;
    logic [LOG2_N-1:0] step;
    logic [LOG2_N-1:0] tw_step;
    logic [LOG2_N-1:0] group_idx;
    logic [LOG2_N-1:0] j_idx;
    logic [LOG2_N-1:0] curr_p;
    logic [LOG2_N-1:0] curr_q;
    logic [LOG2_N-1:0] curr_k;

    assign half_len  = 1 << (stage_cnt - 1);
    assign step      = 1 << stage_cnt;
    assign tw_step   = N >> stage_cnt;

    always_comb begin
        j_idx     = bf_cnt & (half_len - 1);
        group_idx = (bf_cnt >> (stage_cnt - 1)) << stage_cnt;
        curr_p    = group_idx + j_idx;
        curr_q    = curr_p + half_len;
        curr_k    = j_idx * tw_step;
    end

    // -------------------------------------------------------------------------
    // Next State Logic
    // -------------------------------------------------------------------------
    always_comb begin
        state_next = state;
        case (state)
            ST_IDLE: begin
                if (s_axis_tvalid) begin
                    state_next = ST_LOAD;
                end
            end

            ST_LOAD: begin
                if (s_axis_tvalid && (load_cnt == N - 1)) begin
                    state_next = ST_COMPUTE;
                end
            end

            ST_COMPUTE: begin
                if ((bf_cnt == (N/2 - 1)) && (phase == 1'b1)) begin
                    state_next = ST_DRAIN;
                end
            end

            ST_DRAIN: begin
                if (written_cnt == (N/2)) begin
                    if (stage_cnt == LOG2_N) begin
                        state_next = ST_UNLOAD;
                    end else begin
                        state_next = ST_COMPUTE;
                    end
                end
            end

            ST_UNLOAD: begin
                if (m_axis_tready && (unload_cnt == N)) begin
                    state_next = ST_DONE;
                end
            end

            ST_DONE: begin
                state_next = ST_IDLE;
            end

            default: state_next = ST_IDLE;
        endcase
    end

    // -------------------------------------------------------------------------
    // Sequential State & Counter Updates
    // -------------------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state       <= ST_IDLE;
            load_cnt    <= '0;
            unload_cnt  <= '0;
            stage_cnt   <= 4'd1;
            bf_cnt      <= '0;
            phase       <= 1'b0;
            written_cnt <= '0;
        end else begin
            state <= state_next;

            case (state)
                ST_IDLE: begin
                    load_cnt    <= '0;
                    unload_cnt  <= '0;
                    stage_cnt   <= 4'd1;
                    bf_cnt      <= '0;
                    phase       <= 1'b0;
                    written_cnt <= '0;
                    if (s_axis_tvalid) begin
                        load_cnt <= load_cnt + 1'b1;
                    end
                end

                ST_LOAD: begin
                    if (s_axis_tvalid) begin
                        if (load_cnt == N - 1) begin
                            load_cnt <= '0;
                        end else begin
                            load_cnt <= load_cnt + 1'b1;
                        end
                    end
                    phase       <= 1'b0;
                    bf_cnt      <= '0;
                    written_cnt <= '0;
                end

                ST_COMPUTE: begin
                    phase <= ~phase;
                    if (phase == 1'b1) begin
                        if (bf_cnt < (N/2 - 1)) begin
                            bf_cnt <= bf_cnt + 1'b1;
                        end
                    end

                    if (bf_valid_out) begin
                        written_cnt <= written_cnt + 1'b1;
                    end
                end

                ST_DRAIN: begin
                    if (bf_valid_out) begin
                        written_cnt <= written_cnt + 1'b1;
                    end

                    if (written_cnt == (N/2)) begin
                        written_cnt <= '0;
                        bf_cnt      <= '0;
                        phase       <= 1'b0;
                        if (stage_cnt < LOG2_N) begin
                            stage_cnt <= stage_cnt + 1'b1;
                        end
                    end
                end

                ST_UNLOAD: begin
                    if (m_axis_tready) begin
                        unload_cnt <= unload_cnt + 1'b1;
                    end
                end

                ST_DONE: begin
                    unload_cnt <= '0;
                    load_cnt   <= '0;
                end
            endcase
        end
    end

    // -------------------------------------------------------------------------
    // Control Signal Outputs
    // -------------------------------------------------------------------------
    assign s_axis_tready = (state == ST_IDLE) || (state == ST_LOAD);
    assign busy          = (state != ST_IDLE);
    assign done          = (state == ST_DONE);
    assign bf_en         = 1'b1;

    always_comb begin
        ram_ena       = 1'b0;
        ram_wea       = 1'b0;
        ram_addra     = '0;
        ram_enb       = 1'b0;
        ram_web       = 1'b0;
        ram_addrb     = '0;
        ram_sel_input = 1'b0;

        rom_en        = 1'b0;
        rom_addr      = '0;

        bf_valid_in   = 1'b0;
        bf_addr_p_in  = '0;
        bf_addr_q_in  = '0;

        case (state)
            ST_IDLE: begin
                if (s_axis_tvalid) begin
                    ram_sel_input = 1'b1;
                    ram_ena       = 1'b1;
                    ram_wea       = 1'b1;
                    ram_addra     = bit_rev(load_cnt[LOG2_N-1:0]);
                end
            end

            ST_LOAD: begin
                ram_sel_input = 1'b1;
                ram_ena       = s_axis_tvalid;
                ram_wea       = s_axis_tvalid;
                ram_addra     = bit_rev(load_cnt[LOG2_N-1:0]);
            end

            ST_COMPUTE: begin
                // Even cycle: Initiate Dual-Port Read
                if (phase == 1'b0) begin
                    ram_ena   = 1'b1;
                    ram_wea   = 1'b0;
                    ram_addra = curr_p;

                    ram_enb   = 1'b1;
                    ram_web   = 1'b0;
                    ram_addrb = curr_q;

                    rom_en    = 1'b1;
                    rom_addr  = curr_k;
                end else begin
                    // Odd cycle: Launch into butterfly unit
                    bf_valid_in  = 1'b1;
                    bf_addr_p_in = curr_p;
                    bf_addr_q_in = curr_q;
                end

                // Writeback when butterfly completes
                if (bf_valid_out) begin
                    ram_ena   = 1'b1;
                    ram_wea   = 1'b1;
                    ram_addra = bf_addr_p_out;

                    ram_enb   = 1'b1;
                    ram_web   = 1'b1;
                    ram_addrb = bf_addr_q_out;
                end
            end

            ST_DRAIN: begin
                if (bf_valid_out) begin
                    ram_ena   = 1'b1;
                    ram_wea   = 1'b1;
                    ram_addra = bf_addr_p_out;

                    ram_enb   = 1'b1;
                    ram_web   = 1'b1;
                    ram_addrb = bf_addr_q_out;
                end
            end

            ST_UNLOAD: begin
                ram_ena   = (unload_cnt < N);
                ram_wea   = 1'b0;
                ram_addra = unload_cnt[LOG2_N-1:0];
            end

            default: ;
        endcase
    end

    // Unload stream valid & last generation matching 1-cycle RAM latency
    logic unload_valid_reg;
    logic unload_last_reg;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            unload_valid_reg <= 1'b0;
            unload_last_reg  <= 1'b0;
        end else if (m_axis_tready) begin
            unload_valid_reg <= (state == ST_UNLOAD) && (unload_cnt < N);
            unload_last_reg  <= (state == ST_UNLOAD) && (unload_cnt == N - 1);
        end
    end

    assign m_axis_tvalid = unload_valid_reg;
    assign m_axis_tlast  = unload_last_reg;

endmodule: fft_controller
