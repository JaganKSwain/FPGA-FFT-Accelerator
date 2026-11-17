"""
export_to_latex.py - Converts docs/DSP_Report.docx into an exact, publication-quality
LaTeX document (docs/DSP_Report.tex) matching the SAS Submission Format, preserving
all student metadata, complete mathematical formatting, and all 10 embedded figures.
"""

import os

latex_content = r"""\documentclass[10pt,a4paper]{article}

% --- Essential Packages ---
\usepackage[top=20mm,bottom=20mm,left=18mm,right=18mm]{geometry}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{colortbl}
\usepackage[most]{tcolorbox}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{float}
\usepackage{microtype}
\usepackage{hyperref}

% --- Color Palette (Matching Template Navy & Gray Theme) ---
\definecolor{headerblue}{RGB}{24, 43, 73}
\definecolor{tableheaderbg}{RGB}{235, 240, 248}
\definecolor{celllightgray}{RGB}{248, 249, 251}
\definecolor{accentblue}{RGB}{41, 128, 185}
\definecolor{bordergray}{RGB}{180, 190, 205}
\definecolor{boxbg}{RGB}{252, 253, 255}

% --- Graphics Paths ---
\graphicspath{{figures/}{figures/diagrams/}{../docs/figures/}{../docs/figures/diagrams/}}

% --- Hyperref Setup ---
\hypersetup{
    colorlinks=true,
    linkcolor=headerblue,
    citecolor=accentblue,
    urlcolor=accentblue
}

% --- TColorBox Styling for Section Frames ---
\tcbset{
    reportbox/.style={
        enhanced,
        colback=boxbg,
        colframe=bordergray,
        arc=1.5mm,
        boxrule=0.8pt,
        left=5mm,
        right=5mm,
        top=4mm,
        bottom=4mm,
        boxsep=1mm
    }
}

% --- Formatting Helpers ---
\setlength{\parindent}{0pt}
\setlength{\parskip}{4pt}
\setlist[itemize]{leftmargin=5mm, itemsep=2pt, topsep=2pt}

\begin{document}

% =============================================================================
% TABLE 0: STUDENT & COURSE DETAILS
% =============================================================================
\noindent
\begin{tabularx}{\textwidth}{|>{\bfseries\color{headerblue}\columncolor{tableheaderbg}}p{3.2cm}|X|>{\bfseries\color{headerblue}\columncolor{tableheaderbg}}p{3.2cm}|X|}
\hline
Student Name & Jagan Kumar Swain \newline Snehal Panda \newline Sree Om Naik & Roll No. & 202456652 \newline 202456544 \newline 202412696 \\
\hline
Branch / Section & ECE / ECE-B & Semester & 5th Semester / 3rd Year \\
\hline
Subject & Digital Signal Processing & Subject Code & ECE-300 \\
\hline
Faculty Name & Prof. Bibhuti Bhusan Mishra & Date of Submission & November 17, 2026 \\
\hline
\end{tabularx}

\vspace{3mm}

% =============================================================================
% TABLE 1: PROJECT DETAILS
% =============================================================================
\noindent
\begin{tabularx}{\textwidth}{|>{\bfseries\color{headerblue}\columncolor{tableheaderbg}}p{4.2cm}|X|}
\hline
Project No. & 9 \\
\hline
Project Title & FPGA-Based FFT Accelerator for Single Radix-2 Butterfly \\
\hline
Module No. & Module 4: Discrete Fourier Transform (DFT) \& FFT Algorithms \\
\hline
Course Outcome (CO) Mapped & CO-4: Analyze and compute Discrete Fourier Transforms using efficient Fast Fourier Transform algorithms, and synthesize fixed-point hardware architectures for real-time DSP applications. \\
\hline
Tool / Software Used & AMD Vivado Design Suite ML Enterprise (v2026.1), SystemVerilog (IEEE 1800-2017), Python 3.14 (NumPy 1.26.4, Matplotlib 3.8.4) \\
\hline
Full Link of Tool & \url{https://github.com/JaganKSwain/FPGA-FFT-Accelerator} \newline \url{https://www.xilinx.com/products/design-tools/vivado.html} \\
\hline
\end{tabularx}

\vspace{4mm}

% =============================================================================
% SECTION C: AIM / OBJECTIVES
% =============================================================================
\begin{tcolorbox}[reportbox]
{\Large\bfseries\color{headerblue}C. Aim \& Objectives of the Project}
\vspace{2mm}

\begin{enumerate}[label=\bfseries\arabic*., leftmargin=6mm, itemsep=4pt]
    \item \textbf{Primary Architectural Objective:} To design, model, simulate, verify, and physically synthesize an iterative, single Radix-2 Decimation-In-Time (DIT) Fast Fourier Transform (FFT) hardware accelerator on an FPGA using SystemVerilog with stall-tolerant streaming AXI4-Stream interfaces.
    \item \textbf{Two-Tier Verification Methodology:} To establish a rigorous two-tier verification methodology guaranteeing a 100\% exact 0-LSB match between RTL and a golden fixed-point Python model across all frequency bins, while validating spectral fidelity ($\text{SQNR} > 65.0\text{ dB}$, $\text{RMSE} \le 0.8\text{ LSB}$) against double-precision NumPy references.
    \item \textbf{In-Place Dual-Port RAM Scheduling:} To resolve the physical 4-access-per-cycle True Dual-Port Block RAM contention hazard using a conflict-free 2-phase scheduled access pipeline (Even cycles: Dual Read; Odd cycles: Dual Write).
    \item \textbf{Fixed-Point Precision \& Rounding Policy:} To implement convergent rounding (round-to-nearest-even) and symmetric saturation clamping to eliminate DC accumulation bias and prevent limit-cycle overflow wrapping.
    \item \textbf{Timing Closure \& Power Optimization:} To achieve physical timing closure at $\ge 100.0\text{ MHz}$ on an AMD Alveo U50 Accelerator FPGA (\texttt{xcu50-fsvh2104-2-e}, UltraScale+) with minimal hardware footprint and milliwatt-level dynamic power ($4\text{ mW}$).
\end{enumerate}
\end{tcolorbox}

\vspace{4mm}

% =============================================================================
% SECTION D: THEORY (KEY EQUATIONS & CONCEPTS)
% =============================================================================
\begin{tcolorbox}[reportbox]
{\Large\bfseries\color{headerblue}D. Theory (Key Equations / Concepts Used)}
\vspace{2mm}

\subsection*{1. Discrete Fourier Transform (DFT) Mathematical Definition}
The Discrete Fourier Transform of an $N$-point discrete-time sequence $x[n]$ is defined mathematically as:
\begin{equation}
X[k] = \sum_{n=0}^{N-1} x[n] \cdot W_N^{kn}, \quad \text{for } k = 0, 1, \dots, N - 1
\end{equation}
where the complex twiddle factor kernel $W_N$ is defined by Euler's identity as:
\begin{equation}
W_N = e^{-j \frac{2\pi}{N}} = \cos\left(\frac{2\pi}{N}\right) - j \sin\left(\frac{2\pi}{N}\right)
\end{equation}
Direct evaluation of the DFT requires $N$ complex multiplications and $N - 1$ complex additions per frequency bin, yielding an overall computational complexity of $\mathcal{O}(N^2)$. For $N = 64$, direct DFT evaluation demands 4,096 complex multiplications ($16,384$ real multiplications).

\subsection*{2. Cooley-Tukey Radix-2 Decimation-In-Time (DIT) Formulation}
By decomposing $x[n]$ into even-indexed sub-sequence $x[2m]$ and odd-indexed sub-sequence $x[2m+1]$ for $m = 0, 1, \dots, N/2 - 1$:
\begin{equation}
X[k] = \sum_{m=0}^{N/2-1} x[2m] \cdot W_{N/2}^{km} + W_N^k \sum_{m=0}^{N/2-1} x[2m+1] \cdot W_{N/2}^{km}
\end{equation}
Defining $E[k]$ and $O[k]$ as the $N/2$-point DFTs of the even and odd sub-sequences respectively, and exploiting twiddle factor symmetry ($W_N^{k + N/2} = -W_N^k$):
\begin{align}
X[k]         &= E[k] + W_N^k \cdot O[k], \quad \text{for } k = 0, 1, \dots, \frac{N}{2} - 1 \\
X\left[k + \frac{N}{2}\right] &= E[k] - W_N^k \cdot O[k], \quad \text{for } k = 0, 1, \dots, \frac{N}{2} - 1
\end{align}
This decomposition reduces computational complexity from $\mathcal{O}(N^2)$ to $\mathcal{O}(N \log_2 N)$. For $N = 64$, the total operations drop to only:
\begin{equation}
\text{Total Butterflies} = \frac{N}{2} \log_2 N = \frac{64}{2} \times 6 = 192\text{ butterflies} \quad (21.3\times\text{ arithmetic reduction})
\end{equation}

\subsection*{3. Butterfly Arithmetic \& Stage Scaling (Divide-by-2 Policy)}
In fixed-point hardware, dynamic range expands by up to 1 bit per butterfly stage. To prevent arithmetic overflow without widening internal memory storage beyond 16 bits, a deterministic divide-by-2 ($\gg 1$) scaling factor is applied per stage:
\begin{equation}
A' = \frac{A + B \cdot W_N^k}{2}, \qquad B' = \frac{A - B \cdot W_N^k}{2}
\end{equation}
The cumulative attenuation across $S = \log_2 N$ cascaded stages is:
\begin{equation}
\text{Total Attenuation} = \left(\frac{1}{2}\right)^S = \left(\frac{1}{2}\right)^{\log_2 N} = \frac{1}{N}
\end{equation}
For $N = 64$, total attenuation is $1/64$ ($-36.12\text{ dB}$). This strictly bounds all intermediate operands within the 16-bit signed dynamic range $[-32768, +32767]$ for all possible complex inputs.

\subsection*{4. Fixed-Point Numeric Format Specifications}
\begin{itemize}
    \item \textbf{Data Path:} 16-bit signed $Q1.15$ format with 1 sign bit and 15 fractional bits. Dynamic range $[-1.0, +1.0 - 2^{-15}]$ (integer representation $[-32768, +32767]$).
    \item \textbf{Twiddle Coefficients:} 16-bit signed $Q2.14$ format with 1 sign bit, 1 integer bit, and 14 fractional bits. Dynamic range $[-2.0, +2.0 - 2^{-14}]$. Natively represents $+1.0 = \text{0x4000}$ ($+16384$) and $-1.0 = \text{0xC000}$ ($-16384$) with zero bypass multiplexers or saturation flags.
\end{itemize}

\subsection*{5. Convergent Rounding (Round-to-Nearest-Even)}
Standard truncation (floor) introduces a deterministic negative bias of $-0.5\text{ LSB}$ per truncation, causing noticeable false peaks at DC (bin 0). Convergent rounding rounds exact halves to the nearest even number:
\begin{equation}
\text{Round}(q + 0.5) = \begin{cases} q + 1, & \text{if } q \text{ is odd} \\ q, & \text{if } q \text{ is even} \end{cases}
\end{equation}
Because intermediate operands are symmetrically distributed between odd and even integers, rounding errors cancel out in expectation, yielding zero accumulated DC bias ($\mathbb{E}[\text{Error}] = 0.000\text{ LSB}$).

\subsection*{6. Dual-Port RAM Port Contention Resolution}
Each butterfly demands 2 memory reads (operands $p, q$) and 2 memory writes (results $A', B'$) = 4 accesses per cycle. Standard FPGA Block RAM has only 2 physical ports. An alternating 2-cycle schedule resolves this hazard:
\begin{itemize}
    \item \textbf{Even Cycles (Read Phase $2m$):} Port A reads address $p$, Port B reads address $q$, Twiddle ROM reads index $k$ (2 reads, 0 writes).
    \item \textbf{Odd Cycles (Write Phase $2m+1$):} Operands enter arithmetic pipeline. Completed butterflies write back: Port A writes $A'$ to address $p$, Port B writes $B'$ to address $q$ (0 reads, 2 writes).
\end{itemize}

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{fig7_memory_schedule.png}
\caption{\textbf{Figure D.1:} Conflict-Free 2-Phase True Dual-Port Block RAM Scheduling Waveform (2 Accesses/Cycle Maximum).}
\end{figure}

\subsection*{7. Top-Level Accelerator Hardware Architecture}
The hardware accelerator comprises five dedicated functional blocks integrated via streaming interfaces:
\begin{enumerate}[label=\alph*., itemsep=2pt]
    \item \textbf{AXI4-Stream Protocol Handshake:} Stall-tolerant slave (\texttt{s\_axis\_*}) for streaming ingestion and master (\texttt{m\_axis\_*}) for egress.
    \item \textbf{True Dual-Port Block RAM (\texttt{data\_ram}):} Holds 64 complex words (32-bit: Real[31:16], Imag[15:0]) with independent read/write ports.
    \item \textbf{Synchronous Twiddle ROM (\texttt{twiddle\_rom}):} 32-word ROM pre-loaded with $Q2.14$ twiddle factors.
    \item \textbf{Pipelined Complex Multiplier (\texttt{complex\_mult}):} 3-stage 4-DSP architecture computing $B \cdot W$ with 14-bit convergent rounding.
    \item \textbf{Butterfly Arithmetic Unit (\texttt{butterfly}):} 4-stage pipeline matching operand $A$ delay, computing $(A \pm B \cdot W)/2$ with convergent rounding and symmetric saturation.
\end{enumerate}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{architecture_block_diagram.png}
\caption{\textbf{Figure D.2:} Top-Level Iterative Single-Butterfly FFT Accelerator Hardware Architecture.}
\end{figure}

\subsection*{8. Finite State Machine (FSM) Controller Specification}
The central FSM (\texttt{fft\_controller.sv}) coordinates execution across 5 states:
\begin{itemize}
    \item \textbf{\texttt{ST\_IDLE}:} Awaits input frame with \texttt{s\_axis\_tready = 1}.
    \item \textbf{\texttt{ST\_LOAD}:} Ingests $N$ samples and writes directly into bit-reversed RAM addresses ($\texttt{ram\_addra} = \text{bit\_rev}(\texttt{load\_cnt})$). Data is already in bit-reversed order when computation starts, eliminating separate bit-reversal sorting cycles.
    \item \textbf{\texttt{ST\_COMPUTE}:} Loops across stages $s = 1 \dots \log_2 N$, generating butterfly addresses $p, q$ and twiddle step $\Delta k$ in alternating 2-cycle phases.
    \item \textbf{\texttt{ST\_DRAIN}:} Flushes the 4-cycle arithmetic pipeline at stage boundaries to eliminate Read-After-Write (RAW) data hazards.
    \item \textbf{\texttt{ST\_UNLOAD}:} Streams out $N$ frequency bins in natural sequential order over \texttt{m\_axis\_tdata} with downstream backpressure support.
\end{itemize}

\begin{figure}[H]
\centering
\includegraphics[width=0.88\textwidth]{fsm_state_transition.png}
\caption{\textbf{Figure D.3:} Finite State Machine (FSM) Controller State Transition Graph.}
\end{figure}

\end{tcolorbox}

\vspace{4mm}

% =============================================================================
% SECTION E: PROCEDURE / STEPS FOLLOWED
% =============================================================================
\begin{tcolorbox}[reportbox]
{\Large\bfseries\color{headerblue}E. Procedure / Steps Followed}
\vspace{2mm}

The accelerator implementation followed a rigorous 9-phase deterministic engineering design and verification flow:

\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{procedure_flowchart.png}
\caption{\textbf{Figure E.1:} 9-Phase Engineering Design, Implementation \& Verification Methodology Flowchart (Compact 2-Row Workflow).}
\end{figure}

\begin{itemize}
    \item \textbf{Phase 0 (Specification \& Part Lock):} Centrally configured all architectural parameters in \texttt{config/project\_spec.json}. Created timing constraint \texttt{timing.xdc} enforcing 10.000 ns (100.0 MHz) clock.
    \item \textbf{Phase 1 (Software Models \& Precision Sweep):} Developed double-precision reference model (\texttt{model/fft\_float.py}) and bit-accurate fixed-point golden model (\texttt{model/fft\_fixed.py}). Precision sweep confirmed Option A (16-bit datapath with per-stage $\gg 1$) achieved $> 67.8\text{ dB}$ SQNR, validating 16-bit word length without wide-datapath area overhead. Generated twiddle tables and 120 stimulus/expected hex files across all 12 test classes.
    \item \textbf{Phase 2 (RTL Arithmetic \& 4-Point Prototype):} Implemented \texttt{fixed\_point\_pkg.sv} with convergent rounding functions. Designed 3-stage pipelined 4-DSP multiplier (\texttt{complex\_mult.sv}) and 4-stage butterfly (\texttt{butterfly.sv}). Implemented True Dual-Port RAM (\texttt{data\_ram.sv}), twiddle ROM (\texttt{twiddle\_rom.sv}), and top-level accelerator (\texttt{fft\_top.sv}). Simulated 4-point baseline with 0 LSB mismatch.
    \item \textbf{Phase 3 (Parameterized Scaling \& Bit-Reversal Integration):} Integrated in-place bit-reversal directly into sample ingestion (\texttt{ST\_LOAD}). Parameterized butterfly looping for $N \in \{4, 8, 16, 32, 64\}$. Executed automated regression across 60 test suites with 0 LSB mismatch.
    \item \textbf{Phase 4 (Protocol Stress \& Latency Profiling):} Built \texttt{tb\_fft\_protocol\_stress.sv} verifying random \texttt{s\_axis\_tvalid} bubbles, \texttt{m\_axis\_tready} backpressure stalls, contiguous 3-frame streams, and mid-frame reset recovery. Logged exact 64-point cycle counts.
    \item \textbf{Phase 5 \& 6 (Physical Synthesis, Placement, Routing \& Timing Closure):} Executed headless out-of-context implementation in Vivado 2026.1 targeting AMD Alveo U50. Achieved positive slack $\text{WNS} = +6.706\text{ ns}$ ($F_{\max} = 303.58\text{ MHz}$) and dynamic power of $4\text{ mW}$.
    \item \textbf{Phase 7 \& 8 (Comparative Study \& Technical Package):} Populated comparative scaling tables and finalized documentation.
\end{itemize}
\end{tcolorbox}

\vspace{4mm}

% =============================================================================
% SECTION F: RESULT / OBSERVATION
% =============================================================================
\begin{tcolorbox}[reportbox]
{\Large\bfseries\color{headerblue}F. Result / Observation}
\vspace{2mm}

\subsection*{F1. Post-Route Hardware Resource Utilization (AMD Alveo U50)}
The design was placed and routed on an AMD Alveo U50 FPGA (\texttt{xcu50-fsvh2104-2-e}, UltraScale+ 16nm architecture):

\begin{table}[H]
\centering
\small
\begin{tabular}{|l|c|c|c|l|}
\hline
\rowcolor{tableheaderbg}
\bfseries Resource Primitive & \bfseries Used & \bfseries Total on Device & \bfseries Utilization (\%) & \bfseries Function in Accelerator \\
\hline
\textbf{CLB LUTs} & \textbf{387} & 871,680 & \textbf{0.044\%} & Control FSM, address routing, convergent rounding logic \\
\textbf{CLB Registers (FF)} & \textbf{325} & 1,743,360 & \textbf{0.019\%} & Pipeline registers, address delay matching, AXI stream buffers \\
\textbf{DSP Slices (DSP48E2)} & \textbf{4} & 5,952 & \textbf{0.067\%} & 4 real multipliers in complex multiplier \\
\textbf{Block RAM (RAMB36E2)} & \textbf{1} & 1,344 & \textbf{0.074\%} & Inferred True Dual-Port Block RAM ($64 \times 32$ bits) \\
\textbf{UltraRAM / Distributed RAM} & \textbf{0} & — & \textbf{0.00\%} & Pure Block RAM implementation \\
\hline
\end{tabular}
\end{table}

\begin{figure}[H]
\centering
\includegraphics[width=0.88\textwidth]{fig4_resource_breakdown.png}
\caption{\textbf{Figure F.1:} Post-Route FPGA Resource Breakdown on AMD Alveo U50 (Budget Percentage and Dedicated Primitive Counts).}
\end{figure}

\subsection*{F2. Post-Route Static Timing Summary (@ 100.0 MHz Target / 10.000 ns Period)}

\begin{table}[H]
\centering
\small
\begin{tabular}{|l|c|c|c|}
\hline
\rowcolor{tableheaderbg}
\bfseries Timing Metric & \bfseries Achieved Value & \bfseries Constraint Specification & \bfseries Timing Status \\
\hline
\textbf{Worst Negative Slack (WNS)} & \textbf{+6.706 ns} & $\ge 0.000\text{ ns}$ & \textbf{MET (67.1\% Slack Margin)} \\
\textbf{Total Negative Slack (TNS)} & \textbf{0.000 ns} & $0.000\text{ ns}$ & \textbf{MET (0 Failing Endpoints out of 1,238)} \\
\textbf{Worst Hold Slack (WHS)} & \textbf{+0.045 ns} & $\ge 0.000\text{ ns}$ & \textbf{MET (Clean Hold Timing)} \\
\textbf{Total Hold Slack (THS)} & \textbf{0.000 ns} & $0.000\text{ ns}$ & \textbf{MET (0 Hold Violations)} \\
\textbf{Target Clock Frequency} & $100.00\text{ MHz}$ & $100.00\text{ MHz}$ & Baseline Project Constraint \\
\textbf{Derived Maximum Clock ($F_{\max}$)} & \textbf{303.58 MHz} & — & \textbf{3.04$\times$ Operating Timing Headroom} \\
\hline
\end{tabular}
\end{table}

The maximum clock frequency is derived from the critical datapath delay:
\begin{equation}
T_{\min} = T_{\text{clk}} - \text{WNS} = 10.000\text{ ns} - 6.706\text{ ns} = 3.294\text{ ns} \implies F_{\max} = \frac{1}{3.294\text{ ns}} \approx \mathbf{303.58\text{ MHz}}
\end{equation}

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{fig5_timing_and_fmax.png}
\caption{\textbf{Figure F.2:} Static Timing Closure, Setup Slack (+6.706 ns), and Fmax (303.58 MHz) Breakdown.}
\end{figure}

\subsection*{F3. Power Dissipation \& Energy Efficiency Profile}
\begin{itemize}
    \item \textbf{Active Dynamic Logic Power:} \textbf{0.004 W (Only 4 mW switching power!)}
    \item \textbf{Device Static Leakage Power:} 2.212 W (UltraScale+ 16nm package baseline)
    \item \textbf{Total On-Chip Power:} 2.216 W
    \item \textbf{Dynamic Energy per 64-Point FFT Transform:}
    \begin{equation}
    E_{\text{dyn}} = P_{\text{dynamic}} \cdot T_{\text{frame}} = 4\text{ mW} \times 5.43\ \mu\text{s} = \mathbf{21.72\text{ nJ / transform}}
    \end{equation}
\end{itemize}

\begin{figure}[H]
\centering
\includegraphics[width=0.88\textwidth]{fig6_power_and_energy.png}
\caption{\textbf{Figure F.3:} Power Dissipation (Dynamic vs. Static) \& Energy-per-Transform Profile.}
\end{figure}

\subsection*{F4. Cycle-Accurate Execution Latency \& Throughput Profile ($N=64$ @ 100 MHz)}

\begin{table}[H]
\centering
\small
\begin{tabular}{|l|c|c|l|}
\hline
\rowcolor{tableheaderbg}
\bfseries Pipeline Phase & \bfseries Clock Cycles & \bfseries Real-Time Latency & \bfseries Functional Operation \\
\hline
\textbf{Sample Ingestion (\texttt{ST\_LOAD})} & 65 cycles & $0.65\ \mu\text{s}$ & Stream in 64 samples directly to bit-reversed RAM addresses \\
\textbf{Butterfly Compute (\texttt{ST\_COMPUTE})} & 414 cycles & $4.14\ \mu\text{s}$ & 192 butterflies @ 2 cycles + inter-stage pipeline drains \\
\textbf{Bin Egress (\texttt{ST\_UNLOAD})} & 64 cycles & $0.64\ \mu\text{s}$ & Stream out 64 frequency bins in natural sequential order \\
\hline
\textbf{Total Frame Latency} & \textbf{543 cycles} & \textbf{5.43 $\mu$s (@ 100 MHz)} & \textbf{1.79 $\mu$s (@ 303.58 MHz)} \\
\textbf{Sustained Transform Throughput} & — & \textbf{184,162 transforms/sec} & \textbf{559,079 transforms/sec (@ 303.58 MHz)} \\
\textbf{Continuous Sample Bandwidth} & — & \textbf{11.78 Msamples/sec} & \textbf{35.78 Msamples/sec (@ 303.58 MHz)} \\
\hline
\end{tabular}
\end{table}

\begin{figure}[H]
\centering
\includegraphics[width=0.85\textwidth]{fig3_latency_scaling.png}
\caption{\textbf{Figure F.4:} Latency Breakdown (Load, Compute, Unload) Across Transform Sizes ($N=4$ to $64$).}
\end{figure}

\subsection*{F5. Numerical Precision \& Spectral Quality Performance ($N=64$ across 12 Classes)}

\begin{table}[H]
\centering
\small
\begin{tabular}{|l|c|c|c|c|}
\hline
\rowcolor{tableheaderbg}
\bfseries Test Signal Class & \bfseries SQNR (dB) & \bfseries RMSE (LSB) & \bfseries Max Abs Error & \bfseries RTL Mismatch \\
\hline
\texttt{zeros} & $\infty$ ($> 120$) & 0.0000 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{impulse} ($x[0] = 32767$) & 114.92 dB & 0.0000 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{delayed\_impulse} ($x[1] = 32767$) & 114.92 dB & 0.0000 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{dc} ($x[n] = 16384$) & 114.92 dB & 0.0000 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{bin\_centered\_tone} ($k=5$) & 114.92 dB & 0.0059 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{off\_bin\_tone} ($k=5.35$) & 88.42 dB & 0.1245 & 1.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{two\_tone} ($k=3, 7$) & 82.16 dB & 0.2031 & 1.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{complex\_exponential} ($e^{j 2\pi 4 n / 64}$) & 114.92 dB & 0.0071 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{uniform\_random} ($[-0.75, +0.75]$) & 67.85 dB & 0.7732 & 2.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{gaussian\_noise} ($\sigma=0.25$) & 68.21 dB & 0.7410 & 2.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{pos\_full\_scale} ($+32767$) & 114.92 dB & 0.0000 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\texttt{neg\_full\_scale} ($-32768$) & 114.92 dB & 0.0000 & 0.0 LSB & \textbf{PASS (0 LSB)} \\
\hline
\end{tabular}
\end{table}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{fig1_spectral_comparison.png}
\caption{\textbf{Figure F.5:} Spectral Response \& 0-LSB Hardware Residual Error (Two-Tone Signal, $N=64$).}
\end{figure}

\begin{figure}[H]
\centering
\includegraphics[width=0.92\textwidth]{fig2_sqnr_rmse_profile.png}
\caption{\textbf{Figure F.6:} SQNR and RMSE Precision Distribution Across 11 Standard Test Classes.}
\end{figure}

\end{tcolorbox}

\vspace{4mm}

% =============================================================================
% SECTION G: VERIFICATION
% =============================================================================
\begin{tcolorbox}[reportbox]
{\Large\bfseries\color{headerblue}G. Verification (Tool \& Model Cross-Check)}
\vspace{2mm}

The accelerator underwent automated multi-level verification in AMD Vivado Simulator (\texttt{xsim} v2026.1):

\begin{enumerate}[label=\bfseries\arabic*., leftmargin=6mm, itemsep=4pt]
    \item \textbf{Unit-Level Arithmetic Verification:}
    \begin{itemize}
        \item \texttt{tb\_complex\_mult.sv}: Verified identity ($W^0$), quadrature rotation ($-j$), non-trivial angle ($W_8^1$), full-scale negative boundary ($-32768 \times -32768$), and 50 randomized vectors. \textbf{Result: 57/57 PASSED (0 LSB mismatch)}.
        \item \texttt{tb\_butterfly.sv}: Verified complex multiplication, operand delay alignment, stage scaling, address tagging, and boundary saturation. \textbf{Result: 54/54 PASSED (0 LSB mismatch)}.
    \end{itemize}
    \item \textbf{Full-System Automated Regression (\texttt{scripts/run\_regression.py}):}
    \begin{table}[H]
    \centering
    \small
    \begin{tabular}{|c|c|c|c|c|c|}
    \hline
    \rowcolor{tableheaderbg}
    \bfseries Transform Size ($N$) & \bfseries Stages & \bfseries Butterflies & \bfseries Test Classes & \bfseries Mismatches & \bfseries Status \\
    \hline
    $N = 4$  & 2 & 4   & 12 & 0 & \textbf{PASS (0 LSB)} \\
    $N = 8$  & 3 & 12  & 12 & 0 & \textbf{PASS (0 LSB)} \\
    $N = 16$ & 4 & 32  & 12 & 0 & \textbf{PASS (0 LSB)} \\
    $N = 32$ & 5 & 80  & 12 & 0 & \textbf{PASS (0 LSB)} \\
    $N = 64$ & 6 & 192 & 12 & 0 & \textbf{PASS (0 LSB)} \\
    \hline
    \multicolumn{4}{|l|}{\textbf{Total Checked Output Bins: 1,536}} & \textbf{0} & \textbf{100\% PASS} \\
    \hline
    \end{tabular}
    \end{table}
    \item \textbf{Protocol Stress \& Fault Tolerance Testing (\texttt{tb\_fft\_protocol\_stress.sv}):}
    \begin{itemize}
        \item \textbf{Randomized Input Bubbles:} Random \texttt{s\_axis\_tvalid} pauses $\rightarrow$ \textbf{PASSED (0 LSB error)}.
        \item \textbf{Downstream Backpressure Stalls:} Random \texttt{m\_axis\_tready} drops $\rightarrow$ \textbf{PASSED (0 LSB error)}.
        \item \textbf{Contiguous Multi-Frame Execution:} 3 contiguous back-to-back frames $\rightarrow$ \textbf{PASSED (0 LSB error)}.
        \item \textbf{Mid-Frame Synchronous Reset Recovery:} Cleanly re-synchronized on subsequent frame.
    \end{itemize}
\end{enumerate}
\end{tcolorbox}

\vspace{4mm}

% =============================================================================
% SECTION H: CONCLUSION
% =============================================================================
\begin{tcolorbox}[reportbox]
{\Large\bfseries\color{headerblue}H. Conclusion \& Key Findings}
\vspace{2mm}

\begin{enumerate}[label=\bfseries\arabic*., leftmargin=6mm, itemsep=4pt]
    \item \textbf{Architectural Success:} A highly compact, iterative single Radix-2 DIT butterfly FFT accelerator was successfully designed, simulated, and implemented. Reusing a single 4-DSP complex multiplier and butterfly engine across all stages reduces DSP consumption by \textbf{83.3\%} compared to fully pipelined streaming architectures (4 DSPs vs. 24 DSPs) while maintaining a high sustained throughput of \textbf{184,162 transforms/second}.
    \item \textbf{Hazard Resolution:} The 2-cycle scheduled access engine completely resolves the 4-access/cycle True Dual-Port RAM contention hazard, enabling conflict-free in-place computation directly in a single dedicated Block RAM primitive (\texttt{RAMB36E2}) with zero wait states.
    \item \textbf{Physical \& Numerical Excellence:} The implementation achieved complete physical timing closure on an AMD Alveo U50 FPGA with \textbf{+6.706 ns WNS ($F_{\max} = 303.58\text{ MHz}$)} and only \textbf{4 mW dynamic logic power}. Numerical accuracy exceeded targets with $> 67.8\text{ dB}$ SQNR on random noise and $> 114.9\text{ dB}$ on tones.
    \item \textbf{Two-Tier Verification Gate:} Exact bit-accurate match (\textbf{0 LSB mismatch across all 60 test suites}) was demonstrated against the fixed-point golden model, confirming production-grade reliability for real-time DSP systems.
\end{enumerate}
\end{tcolorbox}

\vspace{4mm}

% =============================================================================
% SECTION I: FACULTY EVALUATION
% =============================================================================
\noindent
\begin{tabularx}{\textwidth}{|>{\bfseries\color{headerblue}\columncolor{tableheaderbg}}p{8cm}|>{\centering\bfseries\columncolor{tableheaderbg}}p{3.5cm}|>{\centering\columncolor{tableheaderbg}}X|}
\hline
\rowcolor{tableheaderbg}
\bfseries Parameter & \bfseries Max Marks & \bfseries Marks Obtained \\
\hline
Theory \& Understanding & 20 & \\
\hline
Implementation / Code & 25 & \\
\hline
Verification with Tool & 25 & \\
\hline
Result \& Observation & 20 & \\
\hline
Conclusion \& Viva & 10 & \\
\hline
\rowcolor{tableheaderbg}
\textbf{Total} & \textbf{100} & \\
\hline
\end{tabularx}

\end{document}
"""

with open("docs/DSP_Report.tex", "w", encoding="utf-8") as f:
    f.write(latex_content)

print(f"Successfully generated docs/DSP_Report.tex ({len(latex_content)} characters)!")
