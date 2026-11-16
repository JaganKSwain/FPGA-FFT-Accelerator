# Phase 7 Report: Comparative Study (N = 16, 32, 64)
**Target Platform:** AMD Alveo U50 Accelerator Card (`xcu50-fsvh2104-2-e`, UltraScale+)
**Design Constraint:** 100 MHz (Period: 10.000 ns, Out-of-Context)

---
## Table A: FPGA Hardware Resource Utilization & Timing
| FFT Size ($N$) | CLB LUTs | Registers (FF) | Block RAM (RAMB36) | DSP Slices (DSP48E2) | Post-Route WNS | Max Clock ($F_{\max}$) | Dynamic Power |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | 352 | 310 | 1 | 4 | `+6.85 ns` | **`317.5 MHz`** | 3 mW |
| **32** | 368 | 318 | 1 | 4 | `+6.78 ns` | **`310.6 MHz`** | 3.5 mW |
| **64** | 387 | 325 | 1 | 4 | `+6.71 ns` | **`303.6 MHz`** | 4 mW |

---

## Table B: Latency, Throughput & Numerical Accuracy Performance
| FFT Size ($N$) | Stages | Butterflies | Total Frame Cycles | Frame Latency (@ 100 MHz) | Transform Throughput | Tone SQNR | Random Noise SQNR | RMSE |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **16** | 4 | 32 | 105 cycles | 1.05 $\mu$s | **952,380 transforms/s** | 114.9 dB | 76.1 dB | 0.58 LSB |
| **32** | 5 | 80 | 235 cycles | 2.35 $\mu$s | **425,531 transforms/s** | 114.9 dB | 73.0 dB | 0.63 LSB |
| **64** | 6 | 192 | 543 cycles | 5.43 $\mu$s | **184,162 transforms/s** | 114.9 dB | 67.8 dB | 0.77 LSB |

---

## 3. Key Engineering Takeaways
1. **Resource Scalability:** Because the single-butterfly iterative architecture reuses the same 4-DSP complex multiplier and butterfly engine across all stages, the computational hardware footprint remains essentially constant ($< 400$ LUTs, $4$ DSPs). Only the block RAM address space and twiddle ROM depth scale with $N$.
2. **Timing Margin:** All configurations close timing with $\approx 6.7\text{ ns}$ of positive slack ($F_{\max} > 300\text{ MHz}$), providing over $3\times$ timing margin above the 100 MHz design specification.
3. **Spectral Precision:** Quantization noise accumulation across stages is remarkably low ($\le 0.77\text{ LSB}$ RMSE at $N=64$), preserving $> 67.8\text{ dB}$ SQNR on broad-spectrum noise and $> 114\text{ dB}$ on tones.
