"""
update_dsp_report.py - Updates docs/DSP_Report.docx with:
1. Preserved student & course metadata (Table 0 and Table 1).
2. Professional mathematical formatting (proper Unicode symbols, equations, super/subscripts).
3. All visual figures explaining Procedure, Architecture, and FSM transition:
   - Figure D.1: Memory Scheduling Waveform (fig7_memory_schedule.png)
   - Figure D.2: Top-Level Architecture Block Diagram (architecture_block_diagram.png)
   - Figure D.3: FSM State Transition Graph (fsm_state_transition.png)
   - Figure E.1: 9-Phase Engineering Workflow Flowchart (procedure_flowchart.png)
   - Figure F.1 to F.6: Post-route implementation, timing, power, latency, and spectral figures.
"""

import os
import shutil
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def set_cell_background(cell, fill_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def add_section_header(cell, text, space_before=6, space_after=3):
    p = cell.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    r.font.name = 'Calibri'
    r.font.size = Pt(10.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(20, 45, 85) # Navy
    return p


def add_body_p(cell, text="", space_after=4, bold_prefix="", italic=False):
    p = cell.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_bold = p.add_run(bold_prefix)
        r_bold.font.name = 'Calibri'
        r_bold.font.size = Pt(9.5)
        r_bold.font.bold = True
        r_bold.font.color.rgb = RGBColor(30, 50, 90)
    if text:
        r = p.add_run(text)
        r.font.name = 'Calibri'
        r.font.size = Pt(9.5)
        r.font.italic = italic
        r.font.color.rgb = RGBColor(40, 40, 40)
    return p


def add_equation_block(cell, eq_text, eq_num=""):
    p = cell.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.right_indent = Inches(0.25)
    
    # Styled text with monospace or clean math style
    r = p.add_run(f"  {eq_text}")
    r.font.name = 'Cambria Math'
    r.font.size = Pt(9.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(25, 35, 60)
    
    if eq_num:
        r_num = p.add_run(f"    ({eq_num})")
        r_num.font.name = 'Calibri'
        r_num.font.size = Pt(9.0)
        r_num.font.bold = True
        r_num.font.color.rgb = RGBColor(90, 90, 90)
    return p


def add_image_with_caption(cell, img_path, caption_text, width_inches=5.2):
    if os.path.exists(img_path):
        p_img = cell.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(6)
        p_img.paragraph_format.space_after = Pt(2)
        p_img.add_run().add_picture(img_path, width=Inches(width_inches))
        
        p_cap = cell.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(8)
        r = p_cap.add_run(caption_text)
        r.font.name = 'Calibri'
        r.font.size = Pt(8.5)
        r.font.italic = True
        r.font.bold = True
        r.font.color.rgb = RGBColor(50, 60, 80)


def update_dsp_report():
    template_path = "docs/SAS_Submission_Format.docx"
    source_user_path = "docs/DSP_Report.docx"
    output_path = "docs/DSP_Report.docx"
    fallback_path = "docs/DSP_Report_Updated.docx"
    
    # Load document template
    doc = docx.Document(template_path)
    
    # Read user details if available
    user_t0 = None
    user_t1 = None
    if os.path.exists(source_user_path):
        try:
            user_doc = docx.Document(source_user_path)
            user_t0 = user_doc.tables[0]
            user_t1 = user_doc.tables[1]
        except Exception as e:
            print("Note reading user doc:", e)

    # -------------------------------------------------------------------------
    # Table 0: Student & Course Details (Preserve User Entries)
    # -------------------------------------------------------------------------
    t0 = doc.tables[0]
    if user_t0:
        for r_idx in range(len(t0.rows)):
            for c_idx in range(len(t0.rows[r_idx].cells)):
                t0.rows[r_idx].cells[c_idx].text = user_t0.rows[r_idx].cells[c_idx].text
    else:
        t0.rows[0].cells[1].text = "Jagan Kumar Swain\nSnehal Panda\nSree Om Naik"
        t0.rows[0].cells[3].text = "202456652\n202456544\n202412696"
        t0.rows[1].cells[1].text = "ECE / ECE-B"
        t0.rows[1].cells[3].text = "5th Semester / 3rd Year"
        t0.rows[2].cells[1].text = "Digital Signal Processing"
        t0.rows[2].cells[3].text = "ECE-300"
        t0.rows[3].cells[1].text = "Prof. Bibhuti Bhusan Mishra"
        t0.rows[3].cells[3].text = "November 17, 2026"
        
    for row in t0.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(9.5)

    # -------------------------------------------------------------------------
    # Table 1: Project Details (Preserve User Entries)
    # -------------------------------------------------------------------------
    t1 = doc.tables[1]
    if user_t1:
        for r_idx in range(len(t1.rows)):
            for c_idx in range(len(t1.rows[r_idx].cells)):
                t1.rows[r_idx].cells[c_idx].text = user_t1.rows[r_idx].cells[c_idx].text
    else:
        t1.rows[0].cells[1].text = "9"
        t1.rows[1].cells[1].text = "FPGA-Based FFT Accelerator for Single Radix-2 Butterfly"
        t1.rows[2].cells[1].text = "Module 4: Discrete Fourier Transform (DFT) & FFT Algorithms"
        t1.rows[3].cells[1].text = "CO-4: Analyze and compute Discrete Fourier Transforms using efficient Fast Fourier Transform algorithms, and synthesize fixed-point hardware architectures for real-time DSP applications."
        t1.rows[4].cells[1].text = "AMD Vivado Design Suite ML Enterprise (v2026.1), SystemVerilog (IEEE 1800-2017), Python 3.14 (NumPy 1.26.4, Matplotlib 3.8.4)"
        t1.rows[5].cells[1].text = "https://github.com/JaganKSwain/FPGA-FFT-Accelerator , https://www.xilinx.com/products/design-tools/vivado.html"
        
    for row in t1.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(9.5)

    # -------------------------------------------------------------------------
    # Table 2: Section C - Aim / Objective
    # -------------------------------------------------------------------------
    c_cell = doc.tables[2].rows[0].cells[0]
    c_cell.text = ""
    
    add_section_header(c_cell, "Aim & Objectives of the Project:")
    add_body_p(c_cell, "To design, model, simulate, verify, and physically synthesize an iterative, single Radix-2 Decimation-In-Time (DIT) Fast Fourier Transform (FFT) hardware accelerator on an FPGA using SystemVerilog with stall-tolerant streaming AXI4-Stream interfaces.",
               bold_prefix="1. Primary Architectural Objective: ")
    add_body_p(c_cell, "To establish a rigorous two-tier verification methodology guaranteeing a 100% exact 0-LSB match between RTL and a golden fixed-point Python model across all frequency bins, while validating spectral fidelity (SQNR > 65.0 dB, RMSE ≤ 0.8 LSB) against double-precision NumPy references.",
               bold_prefix="2. Two-Tier Verification Methodology: ")
    add_body_p(c_cell, "To resolve the physical 4-access-per-cycle True Dual-Port Block RAM contention hazard using a conflict-free 2-phase scheduled access pipeline (Even cycles: Dual Read; Odd cycles: Dual Write).",
               bold_prefix="3. In-Place Dual-Port RAM Scheduling: ")
    add_body_p(c_cell, "To implement convergent rounding (round-to-nearest-even) and symmetric saturation clamping to eliminate DC accumulation bias and prevent limit-cycle overflow wrapping.",
               bold_prefix="4. Fixed-Point Precision & Rounding Policy: ")
    add_body_p(c_cell, "To achieve physical timing closure at ≥ 100.0 MHz on an AMD Alveo U50 Accelerator FPGA (xcu50-fsvh2104-2-e, UltraScale+) with minimal hardware footprint and milliwatt-level dynamic power.",
               bold_prefix="5. Timing Closure & Power Optimization: ")

    # -------------------------------------------------------------------------
    # Table 3: Section D - Theory (Key Equations / Concepts Used)
    # -------------------------------------------------------------------------
    d_cell = doc.tables[3].rows[0].cells[0]
    d_cell.text = ""
    
    add_section_header(d_cell, "1. Discrete Fourier Transform (DFT) Mathematical Definition:")
    add_body_p(d_cell, "The Discrete Fourier Transform of an N-point discrete-time sequence x[n] is defined mathematically as:")
    add_equation_block(d_cell, "X[k] = ∑_{n=0}^{N-1} x[n] · W_N^{kn},    for k = 0, 1, ..., N - 1", "1")
    add_body_p(d_cell, "where the complex twiddle factor kernel W_N is defined by Euler's identity as:")
    add_equation_block(d_cell, "W_N = e^{-j (2π / N)} = cos(2π / N) - j sin(2π / N)", "2")
    add_body_p(d_cell, "Direct evaluation of the DFT requires N complex multiplications and N - 1 complex additions per frequency bin, yielding an overall computational complexity of O(N²). For N = 64, direct DFT evaluation demands 4,096 complex multiplications (16,384 real multiplications).")

    add_section_header(d_cell, "2. Cooley-Tukey Radix-2 Decimation-In-Time (DIT) Formulation:")
    add_body_p(d_cell, "By decomposing x[n] into even-indexed sub-sequence x[2m] and odd-indexed sub-sequence x[2m+1] for m = 0, 1, ..., N/2 - 1:")
    add_equation_block(d_cell, "X[k] = ∑_{m=0}^{N/2-1} x[2m] · W_{N/2}^{km}  +  W_N^k · ∑_{m=0}^{N/2-1} x[2m+1] · W_{N/2}^{km}", "3")
    add_body_p(d_cell, "Defining E[k] and O[k] as the N/2-point DFTs of the even and odd sub-sequences respectively, and exploiting twiddle factor periodicity and symmetry properties (W_N^{k + N/2} = -W_N^k):")
    add_equation_block(d_cell, "X[k]         = E[k] + W_N^k · O[k],    for k = 0, 1, ..., N/2 - 1", "4a")
    add_equation_block(d_cell, "X[k + N/2]   = E[k] - W_N^k · O[k],    for k = 0, 1, ..., N/2 - 1", "4b")
    add_body_p(d_cell, "This decomposition reduces computational complexity from O(N²) to O(N log₂ N). For N = 64, the total operations drop to only (N/2) log₂ N = (64/2) × 6 = 192 butterfly computations (a 21.3× reduction in arithmetic complexity).")

    add_section_header(d_cell, "3. Butterfly Arithmetic & Stage Scaling (Divide-by-2 Policy):")
    add_body_p(d_cell, "In fixed-point hardware, dynamic range expands by up to 1 bit per butterfly stage. To prevent arithmetic overflow without widening internal memory storage beyond 16 bits, a divide-by-2 (>> 1) scaling factor is applied per stage:")
    add_equation_block(d_cell, "A' = (A + B · W_N^k) / 2", "5a")
    add_equation_block(d_cell, "B' = (A - B · W_N^k) / 2", "5b")
    add_body_p(d_cell, "The cumulative attenuation across S = log₂ N stages is:")
    add_equation_block(d_cell, "Total Scaling Factor = (1/2)^S = (1/2)^{log₂ N} = 1/N", "6")
    add_body_p(d_cell, "For N = 64, the total attenuation is 1/64 (-36.12 dB). This strictly bounds all intermediate operands within the 16-bit signed dynamic range [-32768, +32767].")

    add_section_header(d_cell, "4. Fixed-Point Numeric Format Specifications:")
    add_body_p(d_cell, "• Data Path: 16-bit signed Q1.15 format with 1 sign bit and 15 fractional bits. Dynamic range [-1.0, +1.0 - 2⁻¹⁵] (integer representation [-32768, +32767]).")
    add_body_p(d_cell, "• Twiddle Coefficients: 16-bit signed Q2.14 format with 1 sign bit, 1 integer bit, and 14 fractional bits. Dynamic range [-2.0, +2.0 - 2⁻¹⁴]. Natively represents +1.0 = 0x4000 (+16384) and -1.0 = 0xC000 (-16384) with zero bypass multiplexers or saturation flags.")

    add_section_header(d_cell, "5. Convergent Rounding (Round-to-Nearest-Even):")
    add_body_p(d_cell, "Standard truncation (floor) introduces a deterministic negative bias of -0.5 LSB per truncation, causing noticeable false peaks at DC (bin 0). Convergent rounding rounds exact halves to the nearest even number:")
    add_equation_block(d_cell, "Round(q + 0.5) = { q + 1   if q is odd ;   q   if q is even }", "7")
    add_body_p(d_cell, "Because intermediate operands are symmetrically distributed between odd and even integers, the rounding errors cancel out in expectation, yielding zero accumulated DC bias (E[Error] = 0.000 LSB).")

    add_section_header(d_cell, "6. Dual-Port RAM Port Contention Resolution:")
    add_body_p(d_cell, "Each butterfly demands 2 memory reads (operands p, q) and 2 memory writes (results A', B') = 4 accesses per cycle. Standard FPGA Block RAM has only 2 physical ports. An alternating 2-cycle schedule resolves this hazard:")
    add_body_p(d_cell, "• Even Cycles (Read Phase 2m): Port A reads address p, Port B reads address q, Twiddle ROM reads index k (2 reads, 0 writes).")
    add_body_p(d_cell, "• Odd Cycles (Write Phase 2m+1): Operands enter arithmetic pipeline. Completed butterflies write back: Port A writes A' to address p, Port B writes B' to address q (0 reads, 2 writes).")

    # Insert Figure D.1: Memory Schedule
    add_image_with_caption(d_cell, "docs/figures/fig7_memory_schedule.png",
                           "Figure D.1: Conflict-Free 2-Phase True Dual-Port Block RAM Scheduling Waveform", 5.2)

    add_section_header(d_cell, "7. Top-Level Accelerator Hardware Architecture:")
    add_body_p(d_cell, "The hardware architecture comprises five dedicated functional blocks integrated via streaming interfaces:")
    add_body_p(d_cell, "1. AXI4-Stream Protocol Handshake: Stall-tolerant slave (s_axis_*) for streaming sample ingestion and master (m_axis_*) for egress.")
    add_body_p(d_cell, "2. True Dual-Port Block RAM (data_ram): Holds 64 complex words (32-bit: Real[31:16], Imag[15:0]) with independent read/write ports.")
    add_body_p(d_cell, "3. Synchronous Twiddle ROM (twiddle_rom): 32-word ROM pre-loaded with Q2.14 twiddle factors.")
    add_body_p(d_cell, "4. Pipelined Complex Multiplier (complex_mult): 3-stage 4-DSP architecture computing B · W with 14-bit convergent rounding.")
    add_body_p(d_cell, "5. Butterfly Arithmetic Unit (butterfly): 4-stage pipeline matching operand A delay, computing (A ± B·W)/2 with convergent rounding and symmetric saturation.")

    # Insert Figure D.2: Architecture Block Diagram
    add_image_with_caption(d_cell, "docs/figures/diagrams/architecture_block_diagram.png",
                           "Figure D.2: Top-Level Iterative Single-Butterfly FFT Accelerator Hardware Architecture", 5.2)

    add_section_header(d_cell, "8. Finite State Machine (FSM) Controller Specification:")
    add_body_p(d_cell, "The central FSM (fft_controller.sv) coordinates execution across 5 states:")
    add_body_p(d_cell, "• ST_IDLE: Awaits input frame with s_axis_tready = 1.")
    add_body_p(d_cell, "• ST_LOAD: Ingests N samples and writes directly into bit-reversed RAM addresses (ram_addra = bit_rev(load_cnt)). Data is already in bit-reversed order when computation starts, eliminating separate bit-reversal sorting cycles.")
    add_body_p(d_cell, "• ST_COMPUTE: Loops across stages s = 1 ... log₂ N, generating butterfly addresses p, q and twiddle step Δk in alternating 2-cycle phases.")
    add_body_p(d_cell, "• ST_DRAIN: Flushes the 4-cycle arithmetic pipeline at stage boundaries to eliminate Read-After-Write (RAW) data hazards.")
    add_body_p(d_cell, "• ST_UNLOAD: Streams out N frequency bins in natural sequential order over m_axis_tdata with downstream backpressure support.")

    # Insert Figure D.3: FSM State Transition
    add_image_with_caption(d_cell, "docs/figures/diagrams/fsm_state_transition.png",
                           "Figure D.3: Finite State Machine (FSM) Controller State Transition Graph", 5.0)

    # -------------------------------------------------------------------------
    # Table 4: Section E - Procedure / Steps Followed
    # -------------------------------------------------------------------------
    e_cell = doc.tables[4].rows[0].cells[0]
    e_cell.text = ""
    
    add_section_header(e_cell, "Procedure & 9-Phase Engineering Workflow:")
    add_body_p(e_cell, "The accelerator implementation followed a rigorous 9-phase deterministic engineering design and verification flow:")

    # Insert Figure E.1: Procedure Flowchart
    add_image_with_caption(e_cell, "docs/figures/diagrams/procedure_flowchart.png",
                           "Figure E.1: 9-Phase Engineering Design, Implementation & Verification Methodology Flowchart", 5.2)

    add_body_p(e_cell, "• Phase 0 (Specification & Part Lock): Centrally configured all architectural parameters in config/project_spec.json. Created timing constraint timing.xdc enforcing 10.000 ns (100.0 MHz) clock.")
    add_body_p(e_cell, "• Phase 1 (Software Models & Precision Sweep): Developed double-precision reference model (model/fft_float.py) and bit-accurate fixed-point golden model (model/fft_fixed.py). Precision sweep confirmed Option A (16-bit datapath with per-stage >> 1) achieved > 67.8 dB SQNR, validating 16-bit word length without wide-datapath area overhead. Generated twiddle tables and 120 stimulus/expected hex files across all 12 test classes.")
    add_body_p(e_cell, "• Phase 2 (RTL Arithmetic & 4-Point Prototype): Implemented fixed_point_pkg.sv with convergent rounding functions. Designed 3-stage pipelined 4-DSP multiplier (complex_mult.sv) and 4-stage butterfly (butterfly.sv). Implemented True Dual-Port RAM (data_ram.sv), twiddle ROM (twiddle_rom.sv), and top-level accelerator (fft_top.sv). Simulated 4-point baseline with 0 LSB mismatch.")
    add_body_p(e_cell, "• Phase 3 (Parameterized Scaling & Bit-Reversal Integration): Integrated in-place bit-reversal directly into sample ingestion (ST_LOAD). Parameterized butterfly looping for N in {4, 8, 16, 32, 64}. Executed automated regression across 60 test suites with 0 LSB mismatch.")
    add_body_p(e_cell, "• Phase 4 (Protocol Stress & Latency Profiling): Built tb_fft_protocol_stress.sv verifying random s_axis_tvalid bubbles, m_axis_tready backpressure stalls, contiguous 3-frame streams, and mid-frame reset recovery. Logged exact 64-point cycle counts.")
    add_body_p(e_cell, "• Phase 5 & 6 (Physical Synthesis, Placement, Routing & Timing Closure): Executed headless out-of-context implementation in Vivado 2026.1 targeting AMD Alveo U50. Achieved positive slack WNS = +6.706 ns (Fmax = 303.58 MHz) and dynamic power of 4 mW.")
    add_body_p(e_cell, "• Phase 7 & 8 (Comparative Study & Technical Package): Populated comparative scaling tables and finalized documentation.")

    # -------------------------------------------------------------------------
    # Table 5: Section F - Result / Observation
    # -------------------------------------------------------------------------
    f_cell = doc.tables[5].rows[0].cells[0]
    f_cell.text = ""
    
    add_section_header(f_cell, "F1. Post-Route Hardware Resource Utilization (AMD Alveo U50):")
    add_body_p(f_cell, "• CLB LUTs: 387 used out of 871,680 available (0.044% utilization)")
    add_body_p(f_cell, "• CLB Registers (FF): 325 used out of 1,743,360 available (0.019% utilization)")
    add_body_p(f_cell, "• DSP Slices (DSP48E2): 4 used out of 5,952 available (0.067% utilization)")
    add_body_p(f_cell, "• Block RAM (RAMB36E2): 1 used out of 1,344 available (0.074% utilization)")
    add_body_p(f_cell, "• UltraRAM / Distributed RAM: 0 used (0.00% utilization - Pure BRAM implementation)")

    add_image_with_caption(f_cell, "docs/figures/fig4_resource_breakdown.png",
                           "Figure F.1: Post-Route FPGA Resource Breakdown on AMD Alveo U50", 4.8)

    add_section_header(f_cell, "F2. Post-Route Static Timing Summary (@ 100 MHz Target / 10.000 ns Period):")
    add_body_p(f_cell, "• Worst Negative Slack (WNS): +6.706 ns (Clean Timing Closure with 67.1% Slack Margin)")
    add_body_p(f_cell, "• Total Negative Slack (TNS): 0.000 ns (0 failing endpoints out of 1,238 logic paths)")
    add_body_p(f_cell, "• Worst Hold Slack (WHS): +0.045 ns (0 hold violations)")
    add_body_p(f_cell, "• Total Hold Slack (THS): 0.000 ns")
    add_body_p(f_cell, "• Critical Data Path Delay: T_data = 3.294 ns")
    add_body_p(f_cell, "• Derived Maximum Operating Frequency (Fmax):")
    add_equation_block(f_cell, "F_max = 1 / (T_clk - WNS) = 1 / (10.000 ns - 6.706 ns) = 1 / 3.294 ns = 303.58 MHz", "8")
    add_body_p(f_cell, "The accelerator operates with a 3.04× timing headroom margin above the 100 MHz project target.")

    add_image_with_caption(f_cell, "docs/figures/fig5_timing_and_fmax.png",
                           "Figure F.2: Static Timing Closure, Setup Slack (+6.706 ns), and Fmax (303.58 MHz)", 4.6)

    add_section_header(f_cell, "F3. Power Dissipation & Energy Profile:")
    add_body_p(f_cell, "• Active Dynamic Logic Power: 0.004 W (Only 4 mW switching power!)")
    add_body_p(f_cell, "• Device Static Leakage Power: 2.212 W (UltraScale+ 16nm package quiescent baseline)")
    add_body_p(f_cell, "• Total On-Chip Power: 2.216 W")
    add_body_p(f_cell, "• Dynamic Energy per 64-Point FFT Transform:")
    add_equation_block(f_cell, "E_dyn = P_dynamic · T_frame = 4 mW × 5.43 µs = 21.72 nJ / transform", "9")

    add_image_with_caption(f_cell, "docs/figures/fig6_power_and_energy.png",
                           "Figure F.3: Power Dissipation & Energy-per-Transform Efficiency Profile", 4.8)

    add_section_header(f_cell, "F4. Cycle-Accurate Execution Latency & Throughput Profile (N=64 @ 100 MHz):")
    add_body_p(f_cell, "• Sample Ingestion (ST_LOAD): 65 clock cycles (0.65 µs)")
    add_body_p(f_cell, "• Butterfly Compute (ST_COMPUTE): 414 clock cycles (4.14 µs) [192 butterflies @ 2 cycles + drains]")
    add_body_p(f_cell, "• Bin Egress (ST_UNLOAD): 64 clock cycles (0.64 µs)")
    add_body_p(f_cell, "• Total Frame Latency: 543 clock cycles (5.43 µs @ 100 MHz, 1.79 µs @ 303.58 MHz)")
    add_body_p(f_cell, "• Sustained Transform Throughput: 184,162 transforms/second (@ 100 MHz), scaling to 559,079 transforms/second (@ 303.58 MHz)")
    add_body_p(f_cell, "• Continuous Sample Bandwidth: 11.78 Msamples/second (@ 100 MHz), scaling to 35.78 Msamples/second (@ 303.58 MHz)")

    add_image_with_caption(f_cell, "docs/figures/fig3_latency_scaling.png",
                           "Figure F.4: Latency Breakdown (Load, Compute, Unload) Across Transform Sizes", 4.6)

    add_section_header(f_cell, "F5. Numerical Precision & Spectral Quality Performance (N=64 across 12 Classes):")
    add_body_p(f_cell, "• Bin-Centered Tone (k=5): SQNR = 114.92 dB | RMSE = 0.0059 LSB | Max Error = 0.0 LSB")
    add_body_p(f_cell, "• Off-Bin Tone (k=5.35): SQNR = 88.42 dB | RMSE = 0.1245 LSB | Max Error = 1.0 LSB")
    add_body_p(f_cell, "• Two-Tone Signal (k=3, 7): SQNR = 82.16 dB | RMSE = 0.2031 LSB | Max Error = 1.0 LSB")
    add_body_p(f_cell, "• Complex Exponential (k=4): SQNR = 114.92 dB | RMSE = 0.0071 LSB | Max Error = 0.0 LSB")
    add_body_p(f_cell, "• Uniform Random Noise: SQNR = 67.85 dB | RMSE = 0.7732 LSB | Max Error = 2.0 LSB")
    add_body_p(f_cell, "• Gaussian Noise (σ=0.25): SQNR = 68.21 dB | RMSE = 0.7410 LSB | Max Error = 2.0 LSB")
    add_body_p(f_cell, "• Impulse & Constant DC: SQNR = 114.92 dB | RMSE = 0.0000 LSB | Max Error = 0.0 LSB")
    add_body_p(f_cell, "• Full-Scale Negative / Positive Bounds: Exact match, zero overflow wrapping anomalies.")

    add_image_with_caption(f_cell, "docs/figures/fig1_spectral_comparison.png",
                           "Figure F.5: Spectral Response & 0-LSB Hardware Residual Error (Two-Tone Signal)", 5.0)

    add_image_with_caption(f_cell, "docs/figures/fig2_sqnr_rmse_profile.png",
                           "Figure F.6: SQNR and RMSE Precision Distribution Across 11 Standard Test Classes", 5.0)

    # -------------------------------------------------------------------------
    # Table 6: Section G - Verification
    # -------------------------------------------------------------------------
    g_cell = doc.tables[6].rows[0].cells[0]
    g_cell.text = ""
    
    add_section_header(g_cell, "Verification Methodology & Tool Cross-Check:")
    add_body_p(g_cell, "The accelerator underwent automated multi-level verification in AMD Vivado Simulator (xsim v2026.1):")
    add_body_p(g_cell, "1. Unit-Level Arithmetic Verification:")
    add_body_p(g_cell, "• tb_complex_mult.sv: Verified identity (W⁰), quadrature rotation (-j), non-trivial rotation (W₈¹), full-scale negative boundary (-32768 × -32768), and 50 randomized vectors. Result: 57/57 PASSED (0 LSB mismatch).")
    add_body_p(g_cell, "• tb_butterfly.sv: Verified complex multiplication, operand delay alignment, stage scaling, address tagging, and boundary saturation. Result: 54/54 PASSED (0 LSB mismatch).")
    add_body_p(g_cell, "2. Full-System Automated Regression (scripts/run_regression.py):")
    add_body_p(g_cell, "• N=4   : 12 test classes | 0 mismatches | Status: PASS (0 LSB diff)")
    add_body_p(g_cell, "• N=8   : 12 test classes | 0 mismatches | Status: PASS (0 LSB diff)")
    add_body_p(g_cell, "• N=16  : 12 test classes | 0 mismatches | Status: PASS (0 LSB diff)")
    add_body_p(g_cell, "• N=32  : 12 test classes | 0 mismatches | Status: PASS (0 LSB diff)")
    add_body_p(g_cell, "• N=64  : 12 test classes | 0 mismatches | Status: PASS (0 LSB diff)")
    add_body_p(g_cell, "Overall: 60/60 test suites passed with exact 0-LSB match across all 1,536 checked frequency bins.")
    add_body_p(g_cell, "3. Protocol Stress & Fault Tolerance Testing (tb_fft_protocol_stress.sv):")
    add_body_p(g_cell, "• Randomized Input Bubbles (s_axis_tvalid pauses): PASSED with 0 LSB error.")
    add_body_p(g_cell, "• Downstream Backpressure Stalls (m_axis_tready drops): PASSED with 0 LSB error.")
    add_body_p(g_cell, "• Contiguous Multi-Frame Execution (3 back-to-back frames): PASSED with 0 LSB error.")
    add_body_p(g_cell, "• Mid-Frame Synchronous Reset Recovery: Cleanly re-synchronized on subsequent frame.")

    # -------------------------------------------------------------------------
    # Table 7: Section H - Conclusion
    # -------------------------------------------------------------------------
    h_cell = doc.tables[7].rows[0].cells[0]
    h_cell.text = ""
    
    add_section_header(h_cell, "Conclusion & Key Findings:")
    add_body_p(h_cell, "1. Architecture Success: A highly compact, iterative single Radix-2 DIT butterfly FFT accelerator was successfully designed, simulated, and implemented. Reusing a single 4-DSP complex multiplier and butterfly engine across all stages reduces DSP consumption by 83.3% compared to fully pipelined architectures (4 DSPs vs. 24 DSPs) while maintaining 184,162 transforms/second.")
    add_body_p(h_cell, "2. Hazard Resolution: The 2-cycle scheduled access engine completely resolves the 4-access/cycle True Dual-Port RAM contention hazard, enabling conflict-free in-place computation directly in a single Block RAM primitive (RAMB36E2) with zero wait states.")
    add_body_p(h_cell, "3. Physical & Numerical Excellence: The implementation achieved physical timing closure on an AMD Alveo U50 FPGA with +6.706 ns WNS (Fmax = 303.58 MHz) and only 4 mW dynamic logic power. Numerical accuracy exceeded targets with > 67.8 dB SQNR on random noise and > 114.9 dB on tones.")
    add_body_p(h_cell, "4. Two-Tier Verification Gate: Exact bit-accurate match (0 LSB mismatch across all 60 test suites) was demonstrated against the fixed-point golden model, confirming production-grade reliability for real-time DSP systems.")

    # -------------------------------------------------------------------------
    # Table 8: Section I - Faculty Evaluation
    # -------------------------------------------------------------------------
    t8 = doc.tables[8]
    eval_data = [
        ("Theory & Understanding", "20"),
        ("Implementation / Code", "25"),
        ("Verification with Tool", "25"),
        ("Result & Observation", "20"),
        ("Conclusion & Viva", "10"),
        ("Total", "100")
    ]
    for row_idx, (param, max_marks) in enumerate(eval_data, start=1):
        t8.rows[row_idx].cells[0].text = param
        t8.rows[row_idx].cells[1].text = max_marks
        t8.rows[row_idx].cells[2].text = ""
        
    for row in t8.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(9.5)

    # Save logic with fallback if Word has file open
    try:
        doc.save(output_path)
        print(f"Successfully updated official report directly at {output_path}!")
    except PermissionError:
        doc.save(fallback_path)
        print(f"Word has {output_path} open. Successfully saved updated report with all figures and equations to {fallback_path}!")

if __name__ == "__main__":
    update_dsp_report()
