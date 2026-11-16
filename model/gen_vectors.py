"""
gen_vectors.py - Generates stimulus and bit-accurate golden response test vectors
for all 12 canonical test classes across FFT sizes N in {4, 8, 16, 32, 64}.
Outputs .mem files into tb/vectors/ for direct ingestion by SystemVerilog $readmemh.
"""

import os
import numpy as np
from fft_fixed import fft_fixed_point, clamp_s16
from fft_float import fft_float_reference, calculate_snr, calculate_rmse, calculate_max_error


def to_hex32(r, i):
    """Packs 16-bit signed real and imag into 32-bit hex word RRRR_IIII."""
    r_u16 = int(r) & 0xFFFF
    i_u16 = int(i) & 0xFFFF
    return f"{r_u16:04X}{i_u16:04X}"


def generate_test_case_signals(test_name, N):
    """
    Returns (xr, xi) in Q1.15 integers [-32768, 32767] for length N.
    """
    t = np.arange(N)
    xr = [0] * N
    xi = [0] * N
    
    if test_name == "zeros":
        pass
    elif test_name == "impulse":
        xr[0] = 32767
    elif test_name == "delayed_impulse":
        xr[1 % N] = 32767
    elif test_name == "dc":
        xr = [16384] * N
    elif test_name == "bin_centered_tone":
        k_bin = 5 % N if N > 8 else 1
        sig = 0.8 * np.cos(2.0 * np.pi * k_bin * t / N)
        xr = [clamp_s16(int(np.round(v * 32767))) for v in sig]
    elif test_name == "off_bin_tone":
        k_bin = (5.35 % N) if N > 8 else 1.35
        sig = 0.8 * np.cos(2.0 * np.pi * k_bin * t / N)
        xr = [clamp_s16(int(np.round(v * 32767))) for v in sig]
    elif test_name == "two_tone":
        k1 = 3 % N if N > 8 else 1
        k2 = 7 % N if N > 8 else (2 % N)
        sig = 0.45 * np.cos(2.0 * np.pi * k1 * t / N) + 0.45 * np.sin(2.0 * np.pi * k2 * t / N)
        xr = [clamp_s16(int(np.round(v * 32767))) for v in sig]
    elif test_name == "complex_exponential":
        k_bin = 4 % N if N > 8 else 1
        c_sig = 0.85 * np.exp(1j * 2.0 * np.pi * k_bin * t / N)
        xr = [clamp_s16(int(np.round(np.real(v) * 32767))) for v in c_sig]
        xi = [clamp_s16(int(np.round(np.imag(v) * 32767))) for v in c_sig]
    elif test_name == "uniform_random":
        np.random.seed(100 + N)
        c_rand = (np.random.uniform(-0.75, 0.75, N) + 1j * np.random.uniform(-0.75, 0.75, N))
        xr = [clamp_s16(int(np.round(np.real(v) * 32767))) for v in c_rand]
        xi = [clamp_s16(int(np.round(np.imag(v) * 32767))) for v in c_rand]
    elif test_name == "gaussian_noise":
        np.random.seed(200 + N)
        # Scaled to stay mostly within [-0.8, 0.8]
        r_noise = np.clip(np.random.normal(0, 0.25, N), -0.9, 0.9)
        i_noise = np.clip(np.random.normal(0, 0.25, N), -0.9, 0.9)
        xr = [clamp_s16(int(np.round(v * 32767))) for v in r_noise]
        xi = [clamp_s16(int(np.round(v * 32767))) for v in i_noise]
    elif test_name == "pos_full_scale":
        xr = [32767] * N
        xi = [32767] * N
    elif test_name == "neg_full_scale":
        xr = [-32768] * N
        xi = [-32768] * N
    else:
        raise ValueError(f"Unknown test case: {test_name}")
        
    return xr, xi


TEST_CLASSES = [
    "zeros",
    "impulse",
    "delayed_impulse",
    "dc",
    "bin_centered_tone",
    "off_bin_tone",
    "two_tone",
    "complex_exponential",
    "uniform_random",
    "gaussian_noise",
    "pos_full_scale",
    "neg_full_scale"
]


def generate_all_vectors(output_dir="tb/vectors"):
    os.makedirs(output_dir, exist_ok=True)
    summary_lines = []
    summary_lines.append("Test_Class,N,SQNR_dB,RMSE_LSB,Max_Error_LSB")
    
    for N in [4, 8, 16, 32, 64]:
        for tc in TEST_CLASSES:
            xr_in, xi_in = generate_test_case_signals(tc, N)
            
            # 1. Compute bit-accurate golden expected output
            xr_out, xi_out = fft_fixed_point(xr_in, xi_in, N=N)
            
            # 2. Write stimulus .mem
            stim_file = os.path.join(output_dir, f"stimulus_{tc}_N{N}.mem")
            with open(stim_file, "w") as f:
                f.write(f"// Stimulus for {tc}, N={N} (Format: [31:16] Real, [15:0] Imag)\n")
                for n in range(N):
                    f.write(f"{to_hex32(xr_in[n], xi_in[n])}\n")
                    
            # 3. Write expected .mem
            exp_file = os.path.join(output_dir, f"expected_{tc}_N{N}.mem")
            with open(exp_file, "w") as f:
                f.write(f"// Expected golden output for {tc}, N={N} (Format: [31:16] Real, [15:0] Imag)\n")
                for n in range(N):
                    f.write(f"{to_hex32(xr_out[n], xi_out[n])}\n")
                    
            # 4. Compare with float reference
            x_float = (np.array(xr_in) + 1j * np.array(xi_in)) / 32767.0
            float_ref = fft_float_reference(x_float, scale_per_stage=True) * 32767.0
            fixed_c = np.array(xr_out) + 1j * np.array(xi_out)
            
            snr = calculate_snr(float_ref, fixed_c)
            rmse = calculate_rmse(float_ref, fixed_c)
            max_err = calculate_max_error(float_ref, fixed_c)
            
            summary_lines.append(f"{tc},{N},{snr:.2f},{rmse:.3f},{max_err:.1f}")
            
    summary_path = "docs/error_analysis_all_vectors.csv"
    with open(summary_path, "w") as f:
        f.write("\n".join(summary_lines) + "\n")
        
    print(f"Generated test vectors for all 12 classes across N={{4, 8, 16, 32, 64}} in {output_dir}/.")
    print(f"Spectral quality summary written to {summary_path}.")


if __name__ == "__main__":
    generate_all_vectors()
