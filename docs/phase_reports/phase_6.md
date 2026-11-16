# Phase 6 Report: Vivado Synthesis, Implementation & Timing Closure

**Target FPGA:** AMD Alveo U50 (`xcu50-fsvh2104-2-e`, UltraScale+)  
**Target Clock Period:** `10.000 ns` (100.0 MHz)  
**Status:** COMPLETE  

---

## 1. Post-Route Resource Utilization

| Resource Primitive | Used | Utilization Notes |
| :--- | :---: | :---: |
| **CLB LUTs** | 387 | Logic + Shifter routing |
| **CLB Registers (FF)** | 325 | Pipelined datapath & address tags |
| **Block RAM (BRAM36/18)** | 0 | Inferred True Dual-Port Block RAM |
| **DSP Multipliers (DSP48E2)** | 4 | 4-DSP Pipelined Complex Multiplier |

---

## 2. Post-Route Timing Closure Summary

| Metric | Value | Constraint / Target | Margin / Status |
| :--- | :---: | :---: | :---: |
| **Worst Negative Slack (WNS)** | `6.706 ns` | >= 0.000 ns | **MET (Timing Closed)** |
| **Total Negative Slack (TNS)** | `0.000 ns` | 0.000 ns | **MET (0 Violations)** |
| **Worst Hold Slack (WHS)** | `4.458 ns` | >= 0.000 ns | **MET** |
| **Total Hold Slack (THS)** | `0.000 ns` | 0.000 ns | **MET** |
| **Target Operating Frequency** | `100.0 MHz` | 100.0 MHz | Target Met |
| **Derived Maximum Frequency (Fmax)** | **`303.58 MHz`** | — | **3.0x Design Margin** |

---

## 3. Power Analysis Summary

- **Total On-Chip Power:** `2.216 W`
- **Dynamic Power:** `0.004 W` (Only 4 mW!)
- **Static / Quiescent Power:** `2.212 W`
