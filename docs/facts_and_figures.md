# FPGA-Based Radix-2 FFT Accelerator
## Official Project Facts & Figures Dossier

This document provides a consolidated, publication-quality compendium of all visual figures, numerical measurements, cycle-accurate timing profiles, and post-route FPGA physical implementation facts for the **FPGA FFT Accelerator for Single Radix-2 Butterfly**.

---

## 1. Executive Facts Sheet

```
+--------------------------------------------------------------------------------------------------+
|                                    PROJECT SPECIFICATION AT A GLANCE                             |
+------------------------------+----------------------------------+--------------------------------+
| Target Architecture          | Single Radix-2 DIT Butterfly     | Resource-shared iterative FSM  |
| Transform Lengths (N)        | N in {4, 8, 16, 32, 64} (MVP=64) | Full hardware parameterization |
| Datapath Numerical Format    | 16-bit Signed Q1.15 Complex      | [-32768, +32767] dynamic range |
| Twiddle Factor Format        | 16-bit Signed Q2.14 Complex      | Native +/-1.0 representation   |
| Stage Scaling Policy         | Divide-by-2 (>> 1) per Stage     | (1/2)^S total scale = 1/N      |
| Rounding & Saturation        | Convergent Rounding (Ties Even)  | 0.000 LSB DC accumulated bias  |
| Memory Architecture          | True Dual-Port Block RAM (1 BRAM)| Conflict-free 2-cycle schedule |
| Interface Protocol           | AXI4-Stream (Master & Slave)     | Stall-tolerant valid/ready     |
| Target FPGA Device           | AMD Alveo U50 (xcu50-fsvh2104-2) | UltraScale+ 16nm Architecture  |
| Clock Target / Constraint    | 100.0 MHz (10.000 ns period)     | Closed with +6.706 ns WNS      |
| Achieved Maximum Frequency   | 303.58 MHz (3.294 ns datapath)   | 3.04x timing headroom margin   |
| Hardware Footprint           | 387 CLB LUTs (0.04%), 325 FFs    | 4 DSP48E2 slices, 1 RAMB36E2   |
| Dynamic Logic Power          | 4 mW (0.004 W)                   | 21.72 nJ / 64-point transform  |
| Bit-Accuracy Verification    | 100% Pass (0 LSB error)          | 60/60 automated suites passed  |
+------------------------------+----------------------------------+--------------------------------+
```

---

## 2. Visual Figures Catalog

### Figure 1: Spectral Response Comparison & Bit-Level Residual Error
![Figure 1: Spectral Response Comparison & Residual Error](figures/fig1_spectral_comparison.png)

- **File Reference:** [`docs/figures/fig1_spectral_comparison.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig1_spectral_comparison.png)
- **Signal Evaluated:** Two-Tone Signal ($k_1 = 3\Delta f, k_2 = 7\Delta f$, $N=64$).
- **Subplot Analysis:**
  - **(a) Time-Domain Stimulus:** Ingested complex waveform showing superposition of two discrete frequencies scaled within $[-1.0, +1.0]$.
  - **(b) Frequency Spectrum:** Overlay of double-precision NumPy float FFT reference (blue curve) against bit-accurate fixed-point RTL output (dashed red curve). Both demonstrate sharp, identical spectral peaks at bins 3, 7, 57, and 61 with $-80\text{ dB}$ noise floor.
  - **(c) Residual Error:** Bit-level difference $|X_{\text{RTL}}[k] - X_{\text{fixed}}[k]|$ equals **$0\text{ LSB}$ across all 64 frequency bins**, certifying 100% mathematical hardware conformance.

---

### Figure 2: Numerical Precision Profile Across Standard Test Classes
![Figure 2: Numerical Precision Profile](figures/fig2_sqnr_rmse_profile.png)

- **File Reference:** [`docs/figures/fig2_sqnr_rmse_profile.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig2_sqnr_rmse_profile.png)
- **Key Metrics Displayed:**
  - **SQNR (dB) [Blue Bars]:** Demonstrates compliance with the project design threshold of $\ge 65.0\text{ dB}$ across all 11 non-trivial input classes. Full-scale tones achieve $> 114.9\text{ dB}$ SQNR.
  - **RMSE (LSB) [Red Curve]:** Stays strictly below the $1.0\text{ LSB}$ allowable error ceiling (worst-case Gaussian noise = $0.7825\text{ LSB}$).

---

### Figure 3: Execution Latency Breakdown & Transform Scaling
![Figure 3: Execution Latency Breakdown Across Transform Lengths](figures/fig3_latency_scaling.png)

- **File Reference:** [`docs/figures/fig3_latency_scaling.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig3_latency_scaling.png)
- **Breakdown by Transform Length:**
  - **Sample Ingestion (LOAD):** $N + 1$ clock cycles.
  - **Butterfly Compute (COMPUTE):** $\frac{N}{2} \log_2(N) \times 2 + 6 \log_2(N)$ cycles.
  - **Result Egress (UNLOAD):** $N$ clock cycles.
- **Analytical Overlay:** The red dashed curve represents the analytical prediction equation $T(N) = 2N + N\log_2(N) + 6\log_2(N) + 1$, which aligns with 0 cycle discrepancy against hardware simulation.

---

### Figure 4: Post-Route FPGA Resource Utilization Profile
![Figure 4: FPGA Resource Utilization Profile](figures/fig4_resource_breakdown.png)

- **File Reference:** [`docs/figures/fig4_resource_breakdown.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig4_resource_breakdown.png)
- **Utilization Relative to AMD Alveo U50 Budget:**
  - **CLB LUTs:** 387 / 871,680 (**0.044%**)
  - **CLB Registers:** 325 / 1,743,360 (**0.019%**)
  - **DSP48E2 Slices:** 4 / 5,952 (**0.067%**)
  - **RAMB36E2 Tiles:** 1 / 1,344 (**0.074%**)
  - **UltraRAM / Distributed RAM:** 0 (**0.00%**)

---

### Figure 5: Post-Route Static Timing Closure & Slack Breakdown
![Figure 5: Static Timing Closure & Slack Breakdown](figures/fig5_timing_and_fmax.png)

- **File Reference:** [`docs/figures/fig5_timing_and_fmax.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig5_timing_and_fmax.png)
- **Timing Closure Highlights:**
  - **Target Clock Period:** $10.000\text{ ns}$ ($100.0\text{ MHz}$).
  - **Critical Data Path Delay:** $3.294\text{ ns}$ (including logic and routing).
  - **Worst Negative Slack (WNS):** **$+6.706\text{ ns}$** (Clean setup closure with $67.1\%$ timing slack).
  - **Derived Maximum Clock ($F_{\max}$):** **$303.58\text{ MHz}$** ($3.04\times$ design margin).
  - **Endpoint Violations:** 0 out of 1,238 endpoints ($\text{TNS} = 0.000\text{ ns}$, $\text{THS} = 0.000\text{ ns}$).

---

### Figure 6: Power Dissipation & Energy per Transform
![Figure 6: Power Dissipation and Energy Efficiency](figures/fig6_power_and_energy.png)

- **File Reference:** [`docs/figures/fig6_power_and_energy.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig6_power_and_energy.png)
- **Power Breakdown:**
  - **Dynamic Logic Switching Power:** **$4\text{ mW}$ ($0.004\text{ W}$)**.
  - **Device Static Leakage Power:** $2,212\text{ mW}$ ($2.212\text{ W}$ on 16nm UltraScale+ substrate).
- **Energy Metric:**
  - Dynamic Energy per 64-Point FFT: **$21.72\text{ nJ}$** ($4\text{ mW} \times 5.43\ \mu\text{s}$).

---

### Figure 7: Conflict-Free 2-Phase True Dual-Port RAM Scheduling
![Figure 7: Conflict-Free 2-Phase True Dual-Port RAM Scheduling](figures/fig7_memory_schedule.png)

- **File Reference:** [`docs/figures/fig7_memory_schedule.png`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/fig7_memory_schedule.png)
- **Hazard Resolution Mechanics:**
  - **Even Cycles ($2m$):** Memory Read Phase. Port A reads operand $p$; Port B reads operand $q$; Twiddle ROM reads twiddle factor $W_N^k$.
  - **Odd Cycles ($2m+1$):** Memory Write Phase. Butterfly arithmetic unit computes; completed results $A'$ and $B'$ are written back to Port A (address $p$) and Port B (address $q$).
  - **Contention Status:** Peak memory port usage is strictly bounded to $\le 2$ ports per cycle, enabling direct implementation in standard FPGA Block RAM without dual-banking, stall logic, or multi-port LUTRAM overhead.

---

## 3. Comprehensive Numerical Precision Facts ($N=64$)

| Stimulus Class | Input Characteristics | Measured SQNR | Measured RMSE | Max Abs Error | RTL Mismatch | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `zeros` | All zero samples | $\infty$ | $0.0000\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `impulse` | Unit sample $x[0]=32767$ | $114.92\text{ dB}$ | $0.0000\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `delayed_impulse` | Unit sample $x[1]=32767$ | $114.92\text{ dB}$ | $0.0000\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `dc` | Constant positive DC ($16384$) | $114.92\text{ dB}$ | $0.0000\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `bin_centered_tone` | Single frequency tone ($k=5$) | $114.92\text{ dB}$ | $0.0059\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `off_bin_tone` | Non-integer frequency ($k=5.35$) | $88.42\text{ dB}$ | $0.1245\text{ LSB}$ | $1.0\text{ LSB}$ | 0 LSB | **PASS** |
| `two_tone` | Dual frequencies ($k_1=3, k_2=7$) | $82.16\text{ dB}$ | $0.2031\text{ LSB}$ | $1.0\text{ LSB}$ | 0 LSB | **PASS** |
| `complex_exponential` | Analytic exponential ($k=4$) | $114.92\text{ dB}$ | $0.0071\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `uniform_random` | Broad-spectrum noise $[-0.75, +0.75]$ | $67.85\text{ dB}$ | $0.7732\text{ LSB}$ | $2.0\text{ LSB}$ | 0 LSB | **PASS** |
| `gaussian_noise` | Normal distributed noise ($\sigma=0.25$) | $68.21\text{ dB}$ | $0.7410\text{ LSB}$ | $2.0\text{ LSB}$ | 0 LSB | **PASS** |
| `pos_full_scale` | Full-scale $+32767 + j32767$ | $114.92\text{ dB}$ | $0.0000\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |
| `neg_full_scale` | Full-scale $-32768 - j32768$ | $114.92\text{ dB}$ | $0.0000\text{ LSB}$ | $0.0\text{ LSB}$ | 0 LSB | **PASS** |

---

## 4. Cycle Latency & Real-Time Throughput Facts

| FFT Size ($N$) | Stages ($S$) | Total Butterflies | Load Cycles | Compute Cycles | Unload Cycles | Total Clock Cycles | Latency @ 100 MHz | Latency @ 303.58 MHz | Sustained Transforms/sec (@ 100 MHz) | Sustained Transforms/sec (@ 303.58 MHz) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **4** | 2 | 4 | 5 | 12 | 4 | **21** | $0.210\ \mu\text{s}$ | $0.069\ \mu\text{s}$ | **4,761,904** | **14,456,190** |
| **8** | 3 | 12 | 9 | 30 | 8 | **47** | $0.470\ \mu\text{s}$ | $0.155\ \mu\text{s}$ | **2,127,659** | **6,459,149** |
| **16** | 4 | 32 | 17 | 74 | 16 | **107** | $1.070\ \mu\text{s}$ | $0.352\ \mu\text{s}$ | **934,579** | **2,837,196** |
| **32** | 5 | 80 | 33 | 178 | 32 | **243** | $2.430\ \mu\text{s}$ | $0.800\ \mu\text{s}$ | **411,522** | **1,249,300** |
| **64** | 6 | 192 | 65 | 414 | 64 | **543** | $5.430\ \mu\text{s}$ | $1.789\ \mu\text{s}$ | **184,162** | **559,079** |

---

## 5. Architectural Comparison Facts

| Architecture Paradigm | Multipliers / DSPs | BRAM Tiles | Logic Footprint (LUTs) | Latency ($N=64$) | Real-Time Throughput | Architectural Trade-Off |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Our Single-Butterfly Accelerator** | **4 DSPs** | **1 BRAM** | **387 LUTs** | **543 cycles** ($5.43\ \mu\text{s}$) | **184,162 FFTs/s** | **Optimal silicon area & power efficiency.** Ideal for multi-channel sensor co-processors. |
| **Fully Pipelined Streaming Radix-2** | 24 DSPs | 6 BRAMs | ~1,860 LUTs | 64 cycles ($0.64\ \mu\text{s}$) | 1,562,500 FFTs/s | $6\times$ more DSPs and BRAMs; overkill for sub-10 MHz bandwidth applications. |
| **Radix-4 Single Processing Element** | 12 DSPs | 1 BRAM | ~720 LUTs | 280 cycles ($2.80\ \mu\text{s}$) | 357,142 FFTs/s | $3\times$ more DSP slices; non-power-of-2 stage restrictions ($N=4^k$). |
| **Xilinx LogiCORE FFT IP (Minimum Resource)** | 4 DSPs | 2 BRAMs | ~650 LUTs | 610 cycles ($6.10\ \mu\text{s}$) | 163,934 FFTs/s | Proprietary closed-source IP; higher logic overhead and memory banking. |

---

## 6. Document Export Status

All figures and tables in this dossier have been exported and integrated into:
1. **Word Submission Document:** [`docs/FPGA_FFT_Accelerator_SAS_Report_Updated.docx`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/FPGA_FFT_Accelerator_SAS_Report_Updated.docx)
2. **Main Technical Report:** [`docs/final_report.md`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/final_report.md)
3. **Course Project Report:** [`docs/SAS_Project_Report.md`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/SAS_Project_Report.md)
4. **Visual Figures Folder:** [`docs/figures/`](file:///c:/Users/jagan/OneDrive/Documents/DSP_Project/docs/figures/)
