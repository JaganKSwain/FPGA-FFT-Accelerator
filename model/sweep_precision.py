"""
sweep_precision.py - Comprehensive precision & scaling policy comparison.
Compares Option A (16-bit datapath with per-stage >> 1) vs Option B (22-bit datapath with 6 guard bits).
Evaluates SQNR, RMSE, and Max Error across N in {16, 32, 64} on representative signals.
Outputs summary to docs/numeric_spec_sweep.csv.
"""

import os
import csv
import numpy as np
from fft_float import fft_float_reference, calculate_snr, calculate_rmse, calculate_max_error
from fft_fixed import (
    convergent_round, clamp_s16, get_twiddle_q2_14,
    complex_mult_fixed, bit_reverse
)


def butterfly_guard_bits(ar, ai, br, bi, wr, wi):
    """
    Butterfly for Option B: 22-bit datapath, no stage scaling (guard bits prevent overflow).
    Multiplication rounds 14 frac bits of twiddle, keeping integer precision intact.
    """
    prr = br * wr
    pii = bi * wi
    pri = br * wi
    pir = bi * wr
    
    tr_raw = prr - pii
    ti_raw = pri + pir
    
    # Drop twiddle fractional bits (14 bits)
    tr = convergent_round(tr_raw, 14)
    ti = convergent_round(ti_raw, 14)
    
    # Butterfly adds without division by 2
    out_ar = ar + tr
    out_ai = ai + ti
    out_br = ar - tr
    out_bi = ai - ti
    
    return (out_ar, out_ai), (out_br, out_bi)


def fft_option_b_guard_bits(xr_in, xi_in, N=64):
    """
    Option B FFT: Internal datapath expands by up to log2(N) bits.
    Final output is scaled by 1/N to match Q1.15 output range.
    """
    log2_n = int(np.log2(N))
    xr = [0] * N
    xi = [0] * N
    for i in range(N):
        rev_i = bit_reverse(i, log2_n)
        xr[rev_i] = int(xr_in[i])
        xi[rev_i] = int(xi_in[i])
        
    for s in range(1, log2_n + 1):
        half_len = 1 << (s - 1)
        step = 1 << s
        tw_step = N // step
        for group in range(0, N, step):
            for j in range(half_len):
                p = group + j
                q = p + half_len
                k = j * tw_step
                wr, wi = get_twiddle_q2_14(k, N)
                (xr[p], xi[p]), (xr[q], xi[q]) = butterfly_guard_bits(
                    xr[p], xi[p], xr[q], xi[q], wr, wi
                )
                
    # Final scaling by 1/N = >> log2_n with convergent rounding
    out_r = [clamp_s16(convergent_round(val, log2_n)) for val in xr]
    out_i = [clamp_s16(convergent_round(val, log2_n)) for val in xi]
    return out_r, out_i


def run_precision_sweep():
    from fft_fixed import fft_fixed_point
    
    test_signals = ["Tone_Bin5", "Two_Tone", "Random_Uniform"]
    fft_sizes = [16, 32, 64]
    results = []
    
    np.random.seed(42)
    
    for N in fft_sizes:
        for sig_name in test_signals:
            t = np.arange(N)
            if sig_name == "Tone_Bin5":
                # Full scale single-tone
                x_float = 0.85 * np.exp(1j * 2 * np.pi * (5 % N) * t / N)
            elif sig_name == "Two_Tone":
                # Two tones
                x_float = 0.45 * np.exp(1j * 2 * np.pi * 3 * t / N) + 0.45 * np.exp(1j * 2 * np.pi * 7 * t / N)
            else:
                # Random uniform [-0.8, 0.8]
                x_float = (np.random.uniform(-0.8, 0.8, N) + 1j * np.random.uniform(-0.8, 0.8, N)) / np.sqrt(2)
                
            xr_in = [int(np.round(np.real(val) * 32767.0)) for val in x_float]
            xi_in = [int(np.round(np.imag(val) * 32767.0)) for val in x_float]
            
            # Float reference with 1/N scaling
            ref_scaled = fft_float_reference(x_float, scale_per_stage=True)
            # Normalized back to Q1.15 integer domain
            ref_int = ref_scaled * 32767.0
            
            # Option A (16-bit datapath, >>1 per stage)
            opt_a_r, opt_a_i = fft_fixed_point(xr_in, xi_in, N=N)
            opt_a_c = np.array(opt_a_r) + 1j * np.array(opt_a_i)
            
            snr_a = calculate_snr(ref_int, opt_a_c)
            rmse_a = calculate_rmse(ref_int, opt_a_c)
            max_err_a = calculate_max_error(ref_int, opt_a_c)
            
            # Option B (22-bit datapath, guard bits)
            opt_b_r, opt_b_i = fft_option_b_guard_bits(xr_in, xi_in, N=N)
            opt_b_c = np.array(opt_b_r) + 1j * np.array(opt_b_i)
            
            snr_b = calculate_snr(ref_int, opt_b_c)
            rmse_b = calculate_rmse(ref_int, opt_b_c)
            max_err_b = calculate_max_error(ref_int, opt_b_c)
            
            results.append({
                "N": N,
                "Signal": sig_name,
                "Option_A_SQNR_dB": f"{snr_a:.2f}",
                "Option_A_RMSE_LSB": f"{rmse_a:.3f}",
                "Option_A_MaxErr_LSB": f"{max_err_a:.1f}",
                "Option_B_SQNR_dB": f"{snr_b:.2f}",
                "Option_B_RMSE_LSB": f"{rmse_b:.3f}",
                "Option_B_MaxErr_LSB": f"{max_err_b:.1f}",
            })
            
    # Write CSV
    os.makedirs("docs", exist_ok=True)
    csv_path = "docs/numeric_spec_sweep.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Precision sweep complete. Results written to {csv_path}.")
    for r in results:
        print(f"N={r['N']:2d} | {r['Signal']:14s} | Opt A SQNR: {r['Option_A_SQNR_dB']} dB (RMSE: {r['Option_A_RMSE_LSB']}) | Opt B SQNR: {r['Option_B_SQNR_dB']} dB")


if __name__ == "__main__":
    run_precision_sweep()
