// ==============================================================================
// fixed_point_pkg.sv - SystemVerilog Package for Fixed-Point FFT Arithmetic
// Specifications:
//   Data: Q1.15 signed (16 bits)
//   Twiddle: Q2.14 signed (16 bits, 1.0 = 0x4000)
//   Rounding: Convergent (Round-to-Nearest-Even)
//   Saturation: Symmetric Clamping [-32768, 32767]
// ==============================================================================

package fixed_point_pkg;

    localparam int DATA_W      = 16;
    localparam int DATA_FRAC   = 15;
    localparam int TW_W        = 16;
    localparam int TW_FRAC     = 14;
    localparam int PROD_W      = DATA_W + TW_W; // 32 bits

    // Complex data type
    typedef struct packed signed {
        logic signed [DATA_W-1:0] r;
        logic signed [DATA_W-1:0] i;
    } cplx_data_t;

    // Complex twiddle type
    typedef struct packed signed {
        logic signed [TW_W-1:0] r;
        logic signed [TW_W-1:0] i;
    } cplx_tw_t;

    // Convergent Rounding & Saturation for Complex Multiplier
    // Input: 33-bit signed accumulator product
    // Drops: 14 fractional bits
    // Output: 16-bit signed Q1.15 [-32768, 32767]
    function automatic logic signed [15:0] round_and_sat_cmult(
        input logic signed [32:0] val
    );
        logic signed [18:0] q;
        logic [13:0]        rem;
        logic [13:0]        half;
        logic signed [19:0] q_rounded;

        q    = val >>> 14;
        rem  = val[13:0];
        half = 14'h2000; // 1 << 13

        if (rem > half) begin
            q_rounded = q + 1;
        end else if (rem < half) begin
            q_rounded = q;
        end else begin
            // Tie case: round to nearest even (check LSB of quotient q)
            q_rounded = q[0] ? (q + 1) : q;
        end

        // Symmetric Saturation to 16-bit signed range [-32768, 32767]
        if (q_rounded > 32767) begin
            return 16'sh7FFF;
        end else if (q_rounded < -32768) begin
            return 16'sh8000;
        end else begin
            return q_rounded[15:0];
        end
    endfunction

    // Convergent Rounding & Saturation for Butterfly Stage Scaling (Divide-by-2)
    // Input: 17-bit signed sum/diff
    // Drops: 1 fractional bit
    // Output: 16-bit signed Q1.15 [-32768, 32767]
    function automatic logic signed [15:0] round_and_sat_bf(
        input logic signed [16:0] val
    );
        logic signed [15:0] q;
        logic               rem;
        logic               half;
        logic signed [16:0] q_rounded;

        q    = val >>> 1;
        rem  = val[0];
        half = 1'b1;

        if (rem == half) begin
            // Tie case: round to nearest even (check LSB of quotient q)
            q_rounded = q[0] ? (q + 1) : q;
        end else begin
            q_rounded = q;
        end

        // Symmetric Saturation to 16-bit signed range [-32768, 32767]
        if (q_rounded > 32767) begin
            return 16'sh7FFF;
        end else if (q_rounded < -32768) begin
            return 16'sh8000;
        end else begin
            return q_rounded[15:0];
        end
    endfunction

endpackage: fixed_point_pkg
