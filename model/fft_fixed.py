"""
fft_fixed.py - Bit-accurate fixed-point Radix-2 DIT FFT model.
Implements exact convergent rounding (round-to-nearest-even) and symmetric clamping
matching the SystemVerilog RTL architecture.
"""

import numpy as np


def convergent_round(val, drop_bits):
    """
    Applies convergent rounding (round-to-nearest-even) when truncating drop_bits.
    
    Args:
        val: Integer value (can be negative or positive).
        drop_bits: Number of LSBs to drop.
    Returns:
        Rounded integer quotient.
    """
    if drop_bits == 0:
        return int(val)
    
    # Python's >> on negative numbers performs arithmetic shift
    q = val >> drop_bits
    mask = (1 << drop_bits) - 1
    rem = val & mask
    half = 1 << (drop_bits - 1)
    
    if rem > half:
        return q + 1
    elif rem < half:
        return q
    else:
        # Tie case: round to nearest even (check LSB of q)
        return q + 1 if (q & 1) else q


def clamp_s16(val):
    """
    Symmetric saturation clamp to 16-bit signed integer [-32768, 32767].
    """
    if val > 32767:
        return 32767
    elif val < -32768:
        return -32768
    return int(val)


def get_twiddle_q2_14(k, N):
    """
    Computes twiddle factor W_N^k = exp(-j * 2 * pi * k / N) in Q2.14 format.
    Returns:
        (tw_real, tw_imag) as 16-bit signed integers.
        Range: [-32768, 32767], where 1.0 = 16384 (0x4000).
    """
    theta = -2.0 * np.pi * k / N
    # Round to nearest integer with standard round
    # For exact half cases, round-to-even
    r_val = np.cos(theta) * 16384.0
    i_val = np.sin(theta) * 16384.0
    
    # Precise rounding
    tw_r = int(np.round(r_val))
    tw_i = int(np.round(i_val))
    
    return clamp_s16(tw_r), clamp_s16(tw_i)


def complex_mult_fixed(br, bi, wr, wi):
    """
    Pipelined 4-DSP complex multiplier: T = B * W
    B is Q1.15 (15 frac bits), W is Q2.14 (14 frac bits).
    Product has 29 frac bits. Round 14 frac bits to return to Q1.15.
    """
    prr = br * wr
    pii = bi * wi
    pri = br * wi
    pir = bi * wr
    
    t_r_raw = prr - pii
    t_i_raw = pri + pir
    
    t_r = clamp_s16(convergent_round(t_r_raw, 14))
    t_i = clamp_s16(convergent_round(t_i_raw, 14))
    
    return t_r, t_i


def butterfly_fixed(ar, ai, br, bi, wr, wi):
    """
    Radix-2 DIT Butterfly with 1/2 stage scaling:
      T = B * W
      A' = (A + T) / 2
      B' = (A - T) / 2
    Scale by 1/2 is performed via 1-bit convergent rounding.
    """
    tr, ti = complex_mult_fixed(br, bi, wr, wi)
    
    sum_r = ar + tr
    sum_i = ai + ti
    diff_r = ar - tr
    diff_i = ai - ti
    
    out_ar = clamp_s16(convergent_round(sum_r, 1))
    out_ai = clamp_s16(convergent_round(sum_i, 1))
    out_br = clamp_s16(convergent_round(diff_r, 1))
    out_bi = clamp_s16(convergent_round(diff_i, 1))
    
    return (out_ar, out_ai), (out_br, out_bi)


def bit_reverse(val, bits):
    """Bit-reversal of val given number of bits."""
    rev = 0
    for _ in range(bits):
        rev = (rev << 1) | (val & 1)
        val >>= 1
    return rev


def fft_fixed_point(xr_in, xi_in, N=64):
    """
    Executes complete bit-accurate N-point Radix-2 DIT FFT in fixed-point.
    
    Args:
        xr_in: Real components (integers in [-32768, 32767])
        xi_in: Imag components (integers in [-32768, 32767])
        N: FFT size (power of 2)
    Returns:
        xr_out, xi_out: Output bins in natural order as lists of signed integers.
    """
    assert len(xr_in) == N and len(xi_in) == N
    log2_n = int(np.log2(N))
    assert (1 << log2_n) == N, "N must be power of 2."
    
    # 1. Bit-reversal permutation at input
    xr = [0] * N
    xi = [0] * N
    for i in range(N):
        rev_i = bit_reverse(i, log2_n)
        xr[rev_i] = clamp_s16(int(xr_in[i]))
        xi[rev_i] = clamp_s16(int(xi_in[i]))
        
    # 2. Iterative Cooley-Tukey DIT stages
    for s in range(1, log2_n + 1):
        half_len = 1 << (s - 1)  # L
        step = 1 << s           # 2L
        tw_step = N // step
        
        for group in range(0, N, step):
            for j in range(half_len):
                p = group + j
                q = p + half_len
                k = j * tw_step
                wr, wi = get_twiddle_q2_14(k, N)
                
                (xr[p], xi[p]), (xr[q], xi[q]) = butterfly_fixed(
                    xr[p], xi[p], xr[q], xi[q], wr, wi
                )
                
    return xr, xi


if __name__ == "__main__":
    N = 64
    # Test impulse input: x[0] = 32767, rest 0
    xr_in = [0] * N
    xi_in = [0] * N
    xr_in[0] = 32767
    
    xr_out, xi_out = fft_fixed_point(xr_in, xi_in, N=N)
    print("Fixed-point model run successfully.")
    print(f"DC bin output: ({xr_out[0]}, {xi_out[0]}), expected ~ 32767 / 64 = {32767 // 64}")
