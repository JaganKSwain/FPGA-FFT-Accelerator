# Phase 2 Report: Arithmetic Units & 4-Point RTL Prototype

**Date:** 2026-11-16  
**Status:** COMPLETE  
**Milestone:** Fixed-Point RTL Arithmetic, Pipelined Multiplier, Radix-2 Butterfly, and 4-Point System Baseline

---

## 1. Summary of Completed Deliverables

1. **Fixed-Point Arithmetic Package** ([`rtl/fixed_point_pkg.sv`](../../rtl/fixed_point_pkg.sv)):
   - Defines complex structures `cplx_data_t` (Q1.15) and `cplx_tw_t` (Q2.14).
   - Implements hardware-accurate convergent rounding (`round_and_sat_cmult` for 33-to-16 bit truncation with 14-bit drop, and `round_and_sat_bf` for 17-to-16 bit truncation with 1-bit drop).
   - Fully synthesizable in AMD/Xilinx Vivado 2026.1 without non-standard construct errors.

2. **3-Stage Pipelined 4-DSP Complex Multiplier** ([`rtl/complex_mult.sv`](../../rtl/complex_mult.sv)):
   - Stage 1: 4 real DSP multiplications ($16 \times 16 \rightarrow 32$ bits).
   - Stage 2: 33-bit real subtraction ($P_{rr} - P_{ii}$) and imaginary addition ($P_{ri} + P_{ir}$).
   - Stage 3: Convergent rounding & symmetric saturation clamp to $[-32768, +32767]$.
   - **Simulation Result:** Self-checking testbench [`tb/tb_complex_mult.sv`](../../tb/tb_complex_mult.sv) passed with **0 LSB mismatch across all 57 tests** (including $W^0$, $-j$, $W_8^1$, full-scale negative $-32768 \times -32768$, and randomized vectors).

3. **4-Stage Pipelined Radix-2 DIT Butterfly Unit** ([`rtl/butterfly.sv`](../../rtl/butterfly.sv)):
   - Integrates 3-stage `complex_mult` with operand $A$ delay matching.
   - Stage 4: Add / subtract with $1/2$ stage scaling using 1-bit convergent rounding.
   - Address and metadata tagging automatically pipelined through all 4 cycles.
   - **Simulation Result:** Self-checking testbench [`tb/tb_butterfly.sv`](../../tb/tb_butterfly.sv) passed with **0 LSB mismatch across all 54 tests**.

4. **Synchronous Memory and Top-Level Architecture** ([`rtl/twiddle_rom.sv`](../../rtl/twiddle_rom.sv), [`rtl/data_ram.sv`](../../rtl/data_ram.sv), [`rtl/fft_controller.sv`](../../rtl/fft_controller.sv), [`rtl/fft_top.sv`](../../rtl/fft_top.sv)):
   - True Dual-Port Block RAM inferred on Xilinx 7-series.
   - Conflict-free 2-cycle butterfly schedule: Port A and B read on even phases, write back on odd phases.
   - Bit-reversed writing directly on incoming AXI-Stream stream during `LOAD`.
   - Natural order sequential readout on AXI-Stream `m_axis_*` during `UNLOAD`.
   - **Simulation Result:** Simulated $N=4$ baseline in Vivado Simulator v2026.1 ([`tb/tb_fft_top_n4.sv`](../../tb/tb_fft_top_n4.sv)) against golden test vectors:
     - `impulse`: **0 LSB Mismatch (PASS)**
     - `dc`: **0 LSB Mismatch (PASS)**
     - `bin_centered_tone`: **0 LSB Mismatch (PASS)**
     - `two_tone`: **0 LSB Mismatch (PASS)**
     - `pos_full_scale`: **0 LSB Mismatch (PASS)**
     - `neg_full_scale`: **0 LSB Mismatch (PASS)**

---

## 2. Phase 2 Deliverables Checklist

- [x] `rtl/fixed_point_pkg.sv` implemented and verified.
- [x] `rtl/complex_mult.sv` implemented (3-stage latency, 4-DSP).
- [x] `rtl/butterfly.sv` implemented (4-stage latency, stage scaling).
- [x] `tb/tb_complex_mult.sv` compiled and simulated in Vivado xsim (100% PASS, 0 LSB diff).
- [x] `tb/tb_butterfly.sv` compiled and simulated in Vivado xsim (100% PASS, 0 LSB diff).
- [x] `rtl/twiddle_rom.sv`, `rtl/data_ram.sv`, `rtl/fft_controller.sv`, `rtl/fft_top.sv` implemented.
- [x] `tb/tb_fft_top_n4.sv` simulated in Vivado xsim (100% PASS, 0 LSB diff).
- [x] Phase 2 documentation logged.
