### 1. Plan Review: Strengths & Architectural Critiques

The revised plan is solid—moving fixed-point specification to Phase 1, adopting a two-tier verification strategy (0-LSB bit-accurate match first, float SNR/RMSE second), and switching to a serial `valid/ready` interface solve the most common pitfalls in hardware FFT projects. However, before an agentic execution workflow writes RTL, several subtle microarchitectural bottlenecks need resolution:

* **Dual-Port RAM Port Contention (Critical Hazard):**
Section 5 specifies a *"Single in-place dual-port data RAM (2 reads + 2 writes per butterfly)"* to achieve 1 butterfly per cycle. A standard FPGA True Dual-Port (TDP) BRAM has only **2 ports total**. Performing 2 reads *and* 2 writes in the same clock cycle requires **4 memory accesses per cycle**, which will force Vivado to synthesize the memory out of distributed LUTRAM/flip-flops or stall the pipeline every other cycle.
* *Fix:* Either use **Two-Bank (Even/Odd parity) True Dual-Port RAM** (since DIT butterfly address pairs $(p, q)$ always differ in bit $s-1$, their parity can be routed to separate banks so each bank performs 1 read + 1 write per cycle), or explicitly budget **2 cycles per butterfly** (Read cycle $\rightarrow$ Write cycle) if using a single TDP RAM.


* **Read-After-Write (RAW) Pipeline Hazard Across Stage Boundaries:**
In an iterative pipeline (e.g., 3–4 cycle latency through `data_ram` $\rightarrow$ `complex_mult` $\rightarrow$ `butterfly` $\rightarrow$ `data_ram`), the final butterflies of Stage $s$ write back to RAM just as the first butterflies of Stage $s+1$ read those same addresses. Without either an explicit pipeline drain (bubble of $L_{\text{pipe}}$ cycles between stages) or forwarding logic, Stage $s+1$ will read stale data.
* *Fix:* Explicitly insert a $L_{\text{pipe}}$-cycle stage-transition flush state in `fft_controller` (adds only $6 \times 4 = 24$ cycles total for $N=64$, negligible overhead and zero hazard complexity).


* **Clock-Gating / Stall Propagation (`valid/ready`):**
When `m_axis_tready` (output ready) deasserts during unload, or `s_axis_tvalid` drops mid-load, freezing the internal pipeline requires either a global `pipe_en` signal across all pipeline registers or skid buffers at the boundaries. Leaving this implicit causes off-by-one sample drops during stall tests.
* **Gaussian 3-Multiply vs. 4-Multiply Complex Multiplier:**
On 7-series FPGAs (DSP48E1 with $25 \times 18$ multipliers and pre-adders), the 3-multiply Gauss trick $(a+b)(c+d)$ requires pre-additions that widen operands by 1 bit and increase critical-path routing delay, often hurting $F_{\max}$ while saving only 1 DSP slice (3 vs. 4 DSPs). Stick to the standard **4-DSP structure** for deterministic timing and clean pipelining.
* **Phase 0 Ambiguity for Automated Execution:**
Leaving choices open (e.g., *"Python or MATLAB"*, *"xc7a35t or xc7z020"*, *"Option A or Option B"*) slows down automated agents. Lock these down before execution:
* **Language & Toolchain:** SystemVerilog (`.sv`) for RTL/TB + Python 3 (`numpy`) for golden models and Vivado Tcl batch automation.
* **Target Part:** `xc7a35tcpg236-1` (Artix-7, representative of resource-constrained edge FPGA targets) with a default `10.0 ns` (100 MHz) clock constraint.
* **Numeric Spec:** `Q1.15` input/output (`DATA_W = 16`), `Q2.14` twiddles (`TW_W = 16`, natively represents $+1.0 = \text{0x4000}$ and $-1.0 = \text{0xC000}$ without needing a $W^0$ mux bypass), and **convergent (round-to-nearest-even) rounding** with symmetric saturation.



---

### 2. AntiGravity Masterplan: Directory Structure, Implementation Steps & Deliverables

This masterplan is structured as a deterministic, file-oriented execution pipeline where every phase has explicit input/output artifacts and automated pass/fail gates.

#### Canonical Repository Structure

```text
fpga_fft_accelerator/
├── config/
│   └── project_spec.json          # Single source of truth: N, DATA_W, TW_W, SCALE_MODE, FPGA_PART, CLK_PERIOD_NS
├── model/
│   ├── fft_float.py               # Floating-point reference & SNR/RMSE calculator
│   ├── fft_fixed.py               # Bit-accurate fixed-point model (convergent rounding + saturation)
│   ├── gen_twiddles.py            # Generates twiddle_rom_*.mem & C/SV headers
│   ├── gen_vectors.py             # Generates stimulus & golden .hex/.mem files for all test cases
│   └── sweep_precision.py         # Phase 1 width/scaling sweep & trade-off plots
├── rtl/
│   ├── fixed_point_pkg.sv         # Parameters, fixed-point types, convergent round & saturate functions
│   ├── twiddle_rom.sv             # Synchronous ROM initialized via $readmemh
│   ├── data_ram_banked.sv         # Two-bank True Dual-Port RAM (eliminates 4-access/cycle contention)
│   ├── complex_mult.sv            # 3-stage pipelined 4-DSP complex multiplier
│   ├── butterfly.sv               # Pipelined Radix-2 DIT butterfly with stage scaling
│   ├── fft_controller.sv          # FSM (IDLE, LOAD, COMPUTE, DRAIN, UNLOAD), bit-rev & butterfly addr gen
│   └── fft_top.sv                 # AXI-Stream-style valid/ready top-level wrapper
├── tb/
│   ├── tb_complex_mult.sv         # Unit test: W^0, -j, W_8^1, max-scale, -32768 edge cases
│   ├── tb_butterfly.sv            # Unit test: full butterfly arithmetic & rounding match
│   └── tb_fft_top.sv              # Self-checking system TB (0-LSB check + stall/reset/back-to-back)
├── scripts/
│   ├── run_sim.tcl                # Headless Vivado xsim batch runner (outputs pass/fail log & VCD/WDB)
│   ├── run_impl.tcl               # Headless synthesis, opt, place, route & report generation
│   └── parse_reports.py           # Extracts LUT, FF, BRAM, DSP, WNS, Fmax into Markdown/CSV tables
├── constraints/
│   └── timing.xdc                 # create_clock + input/output delay constraints
├── build/                         # Vivado project & out-of-context runs (gitignored)
└── docs/
    ├── architecture.md            # Block diagrams, FSM state table, pipeline timing diagram
    └── final_report.md            # Complete results, error analysis, and comparative tables

```

---

#### Step-by-Step Execution Pipeline & Deliverables

##### Phase 0: Environment & Parameter Lock

* **Actions:**
1. Initialize repository structure and lock `config/project_spec.json` (`FPGA_PART = xc7a35tcpg236-1`, `CLK_PERIOD_NS = 10.0`, `N = 64`, `DATA_W = 16`, `TW_W = 16`, `TW_FRAC = 14`, `ROUND_MODE = CONVERGENT`).
2. Write `constraints/timing.xdc` with `create_clock -period 10.000 -name sys_clk [get_ports clk]`.
3. Create a smoke-test Tcl script (`scripts/run_sim.tcl`) and verify Vivado `xvlog`/`xelab`/`xsim` execution in batch mode.


* **Deliverables:**
* `config/project_spec.json`
* `constraints/timing.xdc`
* `scripts/run_sim.tcl` (verified working with exit code `0` on dummy module)



##### Phase 1: Golden Software Models & Numeric Specification

* **Actions:**
1. Implement `model/fft_float.py` (NumPy double-precision reference with matching stage scale factor $1/N$ or $1$).
2. Implement `model/fft_fixed.py` matching exact RTL bit widths, `Q2.14` twiddles, convergent rounding (`round-to-nearest-even`), and symmetric clamping (`[-32768, 32767]`).
3. Run `model/sweep_precision.py` comparing **Option A** (16-bit datapath with per-stage `>> 1`) vs. **Option B** (22-bit internal datapath with 6 guard bits) across $N \in \{16, 32, 64\}$; record SQNR, RMSE, and max error. Freeze the winning mode in `project_spec.json`.
4. Implement `model/gen_twiddles.py` and `model/gen_vectors.py` to export hex test vectors for all 12 test classes (zeros, impulse, delayed impulse, DC, bin-centered tone, off-bin tone, two-tone, complex exponential, uniform random, $+FS$, $-FS = -32768$).


* **Deliverables:**
* `model/fft_float.py` & `model/fft_fixed.py`
* `model/gen_twiddles.py` & `model/gen_vectors.py`
* `docs/numeric_spec_sweep.csv` (SNR/RMSE comparison justifying final bit-widths)
* `tb/vectors/*.mem` (golden stimulus & expected output files)



##### Phase 2: Arithmetic Units & 4-Point RTL Prototype

* **Actions:**
1. Implement `rtl/fixed_point_pkg.sv`, `rtl/complex_mult.sv` (pipelined, 4 real multipliers), and `rtl/butterfly.sv`.
2. Run `tb/tb_complex_mult.sv` and `tb/tb_butterfly.sv` via `xsim`; verify **0 LSB mismatch** on $W^0$, $-j$, $W_8^1$, and $-32768 \times -32768$.
3. Implement `rtl/twiddle_rom.sv`, `rtl/data_ram_banked.sv`, `rtl/fft_controller.sv` (including inter-stage pipeline drain states), and `rtl/fft_top.sv`.
4. Simulate `N = 4` in `tb/tb_fft_top.sv` and verify 0-LSB match across all vectors.


* **Deliverables:**
* `rtl/fixed_point_pkg.sv`, `rtl/complex_mult.sv`, `rtl/butterfly.sv`
* `tb/tb_complex_mult.sv`, `tb/tb_butterfly.sv` (passing logs)
* Working $N=4$ baseline of `fft_top.sv`



##### Phase 3: Parameterized Scaling ($N = 8, 16, 32$)

* **Actions:**
1. Parameterize bit-reversed address generation (`bit_reverse#(LOG2_N)`), stage/butterfly loop bounds, and ROM depth in `fft_controller.sv` and `twiddle_rom.sv`.
2. Execute automated regression across $N = 8$ (first non-trivial twiddle $W_8^1$), $N = 16$, and $N = 32$.


* **Deliverables:**
* Parameterized `rtl/fft_controller.sv` & `rtl/twiddle_rom.sv`
* Automated regression logs showing `0 LSB diff` for $N \in \{4, 8, 16, 32\}$



##### Phase 4: 64-Point Iterative MVP & Protocol Stress-Testing

* **Actions:**
1. Configure `N = 64` (6 stages $\times$ 32 butterflies = 192 butterflies).
2. Enhance `tb/tb_fft_top.sv` to inject randomized `s_axis_tvalid` gaps, `m_axis_tready` backpressure stalls, back-to-back continuous frames, and mid-frame synchronous `rst_n` assertions.
3. Log exact cycle counts for `LOAD`, `COMPUTE + DRAIN`, and `UNLOAD`.


* **Deliverables:**
* Complete, freeze-ready 64-point RTL codebase (`rtl/*.sv`)
* `tb/tb_fft_top.sv` protocol stress-test pass log + exact latency breakdown



##### Phase 5: Numerical Regression & Error Analysis

* **Actions:**
1. Run full vector regression on $N = 64$ comparing RTL output vs. `fft_fixed.py` (**Gate: 0 LSB mismatch across 100% of bins and vectors**).
2. Compute RMSE, Max Absolute Error, and Output SNR (dB) of `fft_fixed.py`/RTL against `fft_float.py`.
3. Document overflow/saturation behavior under full-scale square waves and $-32768$ DC inputs.


* **Deliverables:**
* `docs/error_analysis_n64.csv` (RMSE, Max Error, SNR per test class)
* Regression pass certificate log (`0 FAIL, 0 LSB mismatch`)



##### Phase 6: Vivado Synthesis, Implementation & Timing Closure

* **Actions:**
1. Run `scripts/run_impl.tcl` in out-of-context (`-mode out_of_context`) or serial-stream top mode on `xc7a35tcpg236-1` at `10.0 ns`.
2. Parse post-route utilization (`LUT`, `FF`, `BRAM18/36`, `DSP48E1`) and timing (`WNS`, `TNS`, derived $F_{\max} = 1 / (T_{\text{clk}} - \text{WNS})$).
3. If `WNS < 0`, add pipeline register stages inside `complex_mult.sv` or `data_ram_banked.sv` output mux and re-verify 0-LSB match.
4. Run post-implementation timing simulation to generate `fft_n64.saif` for accurate Vivado power estimation.


* **Deliverables:**
* `scripts/run_impl.tcl` & `scripts/parse_reports.py`
* Post-implementation Vivado `.rpt` files (utilization, timing summary, power)
* `fft_n64.saif`



##### Phase 7: Comparative Study ($N = 16 / 32 / 64$ & Optional Benchmarks)

* **Actions:**
1. Run `run_impl.tcl` and `parse_reports.py` across $N \in \{16, 32, 64\}$ under identical constraints to populate **Table A** (Resources/Timing) and **Table B** (Latency/Throughput/Accuracy).
2. *(Optional)* Benchmark against AMD/Xilinx LogiCORE FFT IP (`xfft_v9_1`, Radix-2 Lite Burst I/O mode) on the same part and clock constraint.


* **Deliverables:**
* Populated comparative results tables (`docs/comparison_tables.md`)



##### Phase 8: Final Documentation & Technical Package

* **Actions:**
1. Generate datapath block diagrams, bank-conflict resolution diagrams, and annotated simulation waveforms (showing load, butterfly compute, stage drain, and unload).
2. Compile `docs/final_report.md` following Section 19's structure, including limitations and viva Q&A prep.


* **Deliverables:**
* `docs/architecture.md` (with ASCII/Mermaid diagrams)
* `docs/final_report.md`
* Annotated simulation waveform screenshots (`docs/waveforms/*.png`)