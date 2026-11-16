"""
gen_twiddles.py - Generates twiddle factor ROM tables in hexadecimal .mem format
and SystemVerilog package constants.
Twiddle format: 16-bit Q2.14, range [-32768, 32767], with 1.0 = 16384 (0x4000).
Packed word format: [31:16] = Real, [15:0] = Imag.
"""

import os
import numpy as np
from fft_fixed import get_twiddle_q2_14


def to_hex16(val):
    """Converts a signed 16-bit integer to 4-character uppercase hex."""
    val_u16 = val & 0xFFFF
    return f"{val_u16:04X}"


def generate_twiddle_mem(N=64, output_dir="tb/vectors"):
    """
    Generates ROM initialization .mem file for N-point FFT.
    Table depth is N/2 entries (k = 0 .. N/2 - 1).
    """
    os.makedirs(output_dir, exist_ok=True)
    num_entries = N // 2
    mem_filename = os.path.join(output_dir, f"twiddle_rom_{N}.mem")
    
    lines = []
    lines.append(f"// Twiddle ROM for N={N} (Q2.14 signed, 1.0 = 0x4000)")
    lines.append(f"// Format: [31:16] Real, [15:0] Imag")
    lines.append(f"// Total entries: {num_entries}")
    
    for k in range(num_entries):
        wr, wi = get_twiddle_q2_14(k, N)
        hex_r = to_hex16(wr)
        hex_i = to_hex16(wi)
        lines.append(f"{hex_r}{hex_i} // k={k:2d}: W_{N}^{k} = ({wr}, {wi})")
        
    with open(mem_filename, "w") as f:
        f.write("\n".join(lines) + "\n")
        
    print(f"Generated {mem_filename} with {num_entries} entries.")
    return mem_filename


def generate_all_twiddles():
    for N in [4, 8, 16, 32, 64]:
        generate_twiddle_mem(N)


if __name__ == "__main__":
    generate_all_twiddles()
