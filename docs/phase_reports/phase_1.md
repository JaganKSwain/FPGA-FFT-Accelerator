# Phase 1 Report: Golden Software Models & Numeric Specification

**Date:** 2026-11-16  
**Status:** COMPLETE  
**Milestone:** Floating-Point Reference, Bit-Accurate Fixed-Point Model, Scaling Precision Sweep, and Test Vector Generation

---

## 1. Summary of Completed Actions

1. **Floating-Point Reference Model** ([`model/fft_float.py`](../../model/fft_float.py)):
   - Implemented standard double-precision Radix-2 DIT FFT reference using NumPy.
   - Built spectral evaluation utilities: SQNR (dB), RMSE (LSB), and Maximum Absolute Error (LSB).
   - Modeled exact $1/N$ ($1/2$ per-stage) stage scaling matching the hardware pipeline.

2. **Bit-Accurate Fixed-Point Reference Model** ([`model/fft_fixed.py`](../../model/fft_fixed.py)):
   - Exact `Q1.15` signed data representation (`DATA_W = 16`, dynamic range $[-32768, +32767]$).
   - Exact `Q2.14` signed twiddle factor representation (`TW_W = 16`, $1.0 = \text{0x4000}$, $-1.0 = \text{0xC000}$).
   - Convergent rounding (`round-to-nearest-even` tie breaking) on all division/shift operations.
   - Symmetric saturation clamping on every butterfly accumulation.
   - Pipelined complex multiplier model ($4$ real multiplications, subtract/add, 14-bit convergent rounding).

3. **Precision & Scaling Policy Sweep** ([`model/sweep_precision.py`](../../model/sweep_precision.py)):
   - Simulated Option A ($16$-bit datapath with $1/2$ shift per stage) vs Option B ($22$-bit datapath with $6$ guard bits).
   - Verified that Option A achieves $> 67.8\text{ dB}$ SQNR on uniform random noise and $> 82\text{ dB}$ on tones for $N=64$, with RMSE $< 0.8\text{ LSB}$.
   - **Conclusion:** Option A meets all spectral accuracy criteria while keeping internal RAM width at 16 bits and avoiding doubling BRAM/DSP resource consumption. Frozen in [`config/project_spec.json`](../../config/project_spec.json).
   - Full results logged in [`docs/numeric_spec_sweep.csv`](../../docs/numeric_spec_sweep.csv).

4. **Twiddle Factor & Test Vector Generation** ([`model/gen_twiddles.py`](../../model/gen_twiddles.py), [`model/gen_vectors.py`](../../model/gen_vectors.py)):
   - Generated ROM tables for $N \in \{4, 8, 16, 32, 64\}$ in standard `$readmemh` format: [`tb/vectors/twiddle_rom_*.mem`](../../tb/vectors/).
   - Generated stimulus and bit-accurate golden expected output `.mem` files for all **12 canonical test classes**:
     1. `zeros`
     2. `impulse`
     3. `delayed_impulse`
     4. `dc`
     5. `bin_centered_tone`
     6. `off_bin_tone`
     7. `two_tone`
     8. `complex_exponential`
     9. `uniform_random`
     10. `gaussian_noise`
     11. `pos_full_scale` ($+32767$)
     12. `neg_full_scale` ($-32768$, two's-complement boundary stress test)

---

## 2. Key Numeric Results (64-Point FFT)

| Test Signal Class | SQNR (dB) | RMSE (LSBs) | Max Error (LSBs) |
| :--- | :--- | :--- | :--- |
| **Bin-Centered Tone** | 114.92 dB | 0.006 | 0.0 |
| **Two-Tone Signal** | 82.16 dB | 0.203 | 1.0 |
| **Uniform Random Noise** | 67.85 dB | 0.773 | 2.0 |
| **Impulse ($x[0] = 32767$)**| 114.92 dB | 0.000 | 0.0 |
| **DC ($x[n] = 16384$)** | 114.92 dB | 0.000 | 0.0 |
| **Negative Full Scale ($-32768$)** | 114.92 dB | 0.000 | 0.0 |

*All results recorded in [`docs/error_analysis_all_vectors.csv`](../../docs/error_analysis_all_vectors.csv).*

---

## 3. Phase 1 Deliverables Checklist

- [x] `model/fft_float.py` implemented and verified.
- [x] `model/fft_fixed.py` bit-accurate model implemented with convergent rounding.
- [x] `model/sweep_precision.py` executed and `docs/numeric_spec_sweep.csv` generated.
- [x] `model/gen_twiddles.py` executed, generating 5 twiddle ROM `.mem` tables.
- [x] `model/gen_vectors.py` executed, generating 120 stimulus/expected vector `.mem` files.
- [x] Phase 1 documentation logged.
