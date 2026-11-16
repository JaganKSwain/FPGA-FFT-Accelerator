# Phase 3 & 4 Report: Parameterized Scaling & 64-Point Protocol Stress-Testing

**Date:** 2026-11-16  
**Status:** COMPLETE  
**Milestone:** Full Parameterized Scaling across $N \in \{4, 8, 16, 32, 64\}$, 100% 0-LSB Match, Protocol Stress Verification, and Latency Profiling

---

## 1. Summary of Actions & Deliverables

1. **Parameterized Architecture Validation** ([`rtl/fft_controller.sv`](../../rtl/fft_controller.sv), [`rtl/twiddle_rom.sv`](../../rtl/twiddle_rom.sv)):
   - Evaluated dynamic bit-reversal address generation, variable stage scaling loop counts, and ROM depths across all standard powers-of-two.
   - Fixed signed struct bit-slicing and integer literal signedness (`1` vs `1'b1`) to eliminate unsigned arithmetic truncation hazards on negative butterfly products.

2. **Automated Regression Across All Sizes & Test Classes** ([`scripts/run_regression.py`](../../scripts/run_regression.py)):
   - Executed automated compilation, elaboration, and simulation on Vivado Simulator v2026.1 across all 5 FFT sizes ($N=4, 8, 16, 32, 64$) and all 12 test classes:
     - `zeros`, `impulse`, `delayed_impulse`, `dc`, `bin_centered_tone`, `off_bin_tone`, `two_tone`, `complex_exponential`, `uniform_random`, `gaussian_noise`, `pos_full_scale`, `neg_full_scale`.
   - **Result:** **100% PASS (60/60 test suites, 0 LSB mismatch across all frequency bins)**.

| FFT Size ($N$) | Stages ($\log_2 N$) | Total Butterflies | Tests Run | Mismatches | Vivado Sim Status |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **4**  | 2 | 4   | 12 | 0 | **PASS (0 LSB)** |
| **8**  | 3 | 12  | 12 | 0 | **PASS (0 LSB)** |
| **16** | 4 | 32  | 12 | 0 | **PASS (0 LSB)** |
| **32** | 5 | 80  | 12 | 0 | **PASS (0 LSB)** |
| **64** | 6 | 192 | 12 | 0 | **PASS (0 LSB)** |

3. **Protocol Stress-Testing & Cycle Profiling** ([`tb/tb_fft_protocol_stress.sv`](../../tb/tb_fft_protocol_stress.sv)):
   - **Randomized Input Bubbles:** Injected random deassertions of `s_axis_tvalid` during sample ingestion $\rightarrow$ **PASS (0 LSB error)**.
   - **Downstream Backpressure:** Injected random deassertions of `m_axis_tready` during egress streaming $\rightarrow$ **PASS (0 LSB error)**.
   - **Contiguous Streaming:** Injected 3 back-to-back continuous 64-point frames without idle gaps $\rightarrow$ **PASS (0 LSB error)**.
   - **Mid-Frame Synchronous Reset:** Asserted `rst_n = 0` mid-computation and verified clean recovery on subsequent frame $\rightarrow$ **PASS (0 LSB error)**.

---

## 2. 64-Point FFT Latency & Throughput Profile (@ 100 MHz / 10.0 ns)

| Pipeline Phase | Clock Cycles | Real-Time Latency |
| :--- | :---: | :---: |
| **Input Streaming (LOAD)** | 65 cycles | $0.65\ \mu\text{s}$ |
| **Butterfly Execution + Inter-Stage Drains (COMPUTE)** | 414 cycles | $4.14\ \mu\text{s}$ |
| **Output Streaming (UNLOAD)** | 64 cycles | $0.64\ \mu\text{s}$ |
| **Total Frame Latency** | **543 cycles** | **$5.43\ \mu\text{s}$** |
| **Maximum Transform Rate** | **~184,162 transforms / sec** | — |

---

## 3. Checklist of Deliverables

- [x] Parameterized SystemVerilog codebase frozen (`rtl/*.sv`).
- [x] Testbench wrappers for $N \in \{4, 8, 16, 32, 64\}$ created (`tb/tb_fft_top_n*.sv`).
- [x] `scripts/run_regression.py` created and passed (0 LSB mismatch across all 60 tests).
- [x] `tb/tb_fft_protocol_stress.sv` created and verified in Vivado xsim.
- [x] Cycle-accurate latency benchmarks logged.
