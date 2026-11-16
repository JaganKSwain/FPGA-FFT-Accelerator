# Phase 0 Report: Environment & Parameter Lock

**Date:** 2026-11-16  
**Status:** COMPLETE  
**Milestone:** Repository Initialization, Parameter Lock, and Toolchain Configuration

---

## 1. Locked System Specifications

All parameters are centrally locked in [`config/project_spec.json`](../../config/project_spec.json).

| Category | Parameter | Locked Value | Technical Rationale |
| :--- | :--- | :--- | :--- |
| **Target FPGA** | Part Number | `xc7a35tcpg236-1` (Artix-7) | Industry-standard resource-constrained edge FPGA target. |
| **Clocking** | Clock Period | `10.000 ns` (100.0 MHz) | Well-balanced frequency for 7-series DSP48E1 / distributed BRAM logic. |
| **Clock/Reset** | Ports | `clk`, `rst_n` (active-low) | Synchronous reset, active-low standard for AXI-Stream interfaces. |
| **FFT Algorithm** | Type | Radix-2 Decimation-in-Time (DIT) | Canonical Cooley-Tukey butterfly algorithm. |
| **FFT Sizes** | Supported $N$ | 4, 8, 16, 32, 64 (MVP = 64) | Parameterized architecture supporting powers of 2 up to 64. |
| **Data Format** | Width & Type | 16-bit Signed `Q1.15` | $[-1.0, +1.0 - 2^{-15}]$, range $[-32768, 32767]$. |
| **Twiddle Format**| Width & Type | 16-bit Signed `Q2.14` | Range $[-2.0, +2.0 - 2^{-14}]$; natively represents $+1.0$ (`0x4000`) and $-1.0$ (`0xC000`). |
| **Rounding** | Mode | Convergent (Round-to-Nearest-Even) | Eliminates positive DC accumulation bias across consecutive stages. |
| **Saturation** | Mode | Symmetric Clamping `[-32768, +32767]` | Prevents two's-complement overflow wrap-around limit cycles. |
| **Multiplier** | Architecture | 4-DSP Pipelined (3 stages) | Deterministic timing, eliminates wide pre-adder critical paths of 3-mult trick. |
| **Memory** | Structure | 2-Bank True Dual-Port RAM | Resolves 4-access/cycle contention between butterfly reads and writes. |
| **Pipeline Drain**| Inter-stage flush | 4 clock cycles | Fully clears arithmetic pipeline latency between FFT stages, avoiding RAW hazards. |
| **Interface** | Protocol | AXI4-Stream `valid`/`ready` handshaking | Backpressure and stall-tolerant streaming interfaces. |

---

## 2. Timing Constraints Summary

The timing constraint file [`constraints/timing.xdc`](../../constraints/timing.xdc) specifies:
- Primary clock: `sys_clk` on port `clk` with period `10.000 ns` (50% duty cycle).
- Input delay budget: `2.0 ns` max / `0.5 ns` min for input stream ports (`s_axis_*`).
- Output delay budget: `2.0 ns` max / `0.5 ns` min for output stream ports (`m_axis_*`).

---

## 3. Automation Scripts

1. **Simulation Runner** ([`scripts/run_sim.tcl`](../../scripts/run_sim.tcl)):
   - Automated compilation via `xvlog -sv`.
   - Elaboration via `xelab -debug typical`.
   - Execution via `xsim -R` with automated log capture and non-zero exit code on failure.
2. **Implementation Runner** ([`scripts/run_impl.tcl`](../../scripts/run_impl.tcl)):
   - Out-of-context synthesis for module `fft_top`.
   - Placement and routing (`opt_design`, `place_design`, `route_design`).
   - Automated report generation for utilization, timing summary, and power.

---

## 4. Phase 0 Deliverables Checklist

- [x] `config/project_spec.json` created and locked.
- [x] `constraints/timing.xdc` created with Artix-7 constraints.
- [x] `scripts/run_sim.tcl` batch simulation runner created.
- [x] `scripts/run_impl.tcl` batch implementation runner created.
- [x] Phase 0 documentation logged.
