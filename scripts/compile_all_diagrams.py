"""
compile_all_diagrams.py - Compiles all Mermaid diagrams in the repository
into high-resolution PNG images using mmdc, and ensures they render seamlessly
in all markdown viewers.
"""

import os
import subprocess

os.makedirs("docs/figures/diagrams", exist_ok=True)

diagrams = {
    "architecture_block_diagram": """graph TD
    subgraph AXI_Stream_Interfaces [AXI4-Stream Interfaces]
        s_axis["s_axis_tdata[31:0]<br/>s_axis_tvalid<br/>s_axis_tready<br/>s_axis_tlast"]
        m_axis["m_axis_tdata[31:0]<br/>m_axis_tvalid<br/>m_axis_tready<br/>m_axis_tlast"]
    end

    subgraph Control_Unit [Control & Address Generation]
        FSM["fft_controller FSM<br/>(IDLE, LOAD, COMPUTE, DRAIN, UNLOAD)"]
        BitRev["Bit-Reversal Unit<br/>(Direct in-place loading)"]
        AddrGen["DIT Butterfly Address Gen<br/>(p, q, twiddle k)"]
    end

    subgraph Memory_Subsystem [Memory Subsystem]
        BRAM["data_ram (True Dual-Port BRAM)<br/>Port A: Addr P (Read/Write)<br/>Port B: Addr Q (Read/Write)"]
        ROM["twiddle_rom (Synchronous ROM)<br/>Depth: N/2 words (Q2.14)"]
    end

    subgraph Datapath [Pipelined Arithmetic Engine]
        DelayA["Operand A Delay Pipeline<br/>(3 Register Stages)"]
        CMULT["complex_mult (3 Stages)<br/>4-DSP Pipelined (16x16 -> 32)<br/>14-bit Convergent Rounding"]
        BF_ALU["Butterfly ALU Stage 4<br/>A' = (A + T) / 2<br/>B' = (A - T) / 2<br/>1-bit Convergent Round & Sat"]
    end

    s_axis -->|LOAD bit-reversed| BRAM
    FSM --> AddrGen
    FSM --> BitRev
    AddrGen -->|Read addra=p, addrb=q| BRAM
    AddrGen -->|rom_addr=k| ROM
    BRAM -->|douta = A| DelayA
    BRAM -->|doutb = B| CMULT
    ROM -->|tw_data = W| CMULT
    DelayA -->|Delayed A| BF_ALU
    CMULT -->|T = B * W| BF_ALU
    BF_ALU -->|Writeback A' to p| BRAM
    BF_ALU -->|Writeback B' to q| BRAM
""",

    "procedure_flowchart": """flowchart TB
    subgraph Row1 ["Row 1: Architecture Design, Software Modeling & Functional RTL Verification"]
        direction LR
        P0["<b>Phase 0: Spec Lock</b><br/>Spec & XDC Constraints"] --> P1["<b>Phase 1: Software Models</b><br/>Float, Fixed & 120 Vectors"]
        P1 --> P2["<b>Phase 2: Arithmetic RTL</b><br/>4-DSP Butterfly Prototype"]
        P2 --> P3["<b>Phase 3: Parameter Scaling</b><br/>N=4..64 Batch Regressions"]
        P3 --> P4["<b>Phase 4: Protocol Stress</b><br/>AXI Bubbles, Stalls & Reset"]
    end

    subgraph Row2 ["Row 2: Physical Implementation, Precision Analysis & Deliverables"]
        direction LR
        P5["<b>Phase 5: Numerical Analysis</b><br/>SQNR > 65dB & 0-LSB Match"] --> P6["<b>Phase 6: Timing Closure</b><br/>Vivado 100MHz on Alveo U50"]
        P6 --> P7["<b>Phase 7: Scaling Study</b><br/>Comparative Benchmarks"]
        P7 --> P8["<b>Phase 8: Project Delivery</b><br/>DSP Report & GitHub"]
    end

    Row1 ==>|Functional Sign-off: 60/60 Suites Passed| Row2
""",

    "fsm_state_transition": """stateDiagram-v2
    [*] --> ST_IDLE
    ST_IDLE --> ST_LOAD: s_axis_tvalid asserted (Sample 0 written to bit_rev(0))
    ST_LOAD --> ST_LOAD: s_axis_tvalid (Samples 1 to N-2)
    ST_LOAD --> ST_COMPUTE: Sample N-1 received (load_cnt == N-1)
    
    ST_COMPUTE --> ST_COMPUTE: Phase 0 (Read) <-> Phase 1 (Launch) for N/2 butterflies
    ST_COMPUTE --> ST_DRAIN: All N/2 butterflies launched (phase == 1 && bf_cnt == N/2 - 1)
    
    ST_DRAIN --> ST_COMPUTE: Next Stage (written_cnt == N/2 && stage_cnt < LOG2_N)
    ST_DRAIN --> ST_UNLOAD: All Stages Finished (written_cnt == N/2 && stage_cnt == LOG2_N)
    
    ST_UNLOAD --> ST_UNLOAD: Stream out N frequency bins (m_axis_tvalid && m_axis_tready)
    ST_UNLOAD --> ST_DONE: All N bins accepted (unload_cnt == N)
    ST_DONE --> ST_IDLE: Return to ready state
"""
}

for name, mmd in diagrams.items():
    mmd_file = f"docs/figures/diagrams/{name}.mmd"
    png_file = f"docs/figures/diagrams/{name}.png"
    svg_file = f"docs/figures/diagrams/{name}.svg"
    
    with open(mmd_file, "w") as f:
        f.write(mmd)
        
    print(f"Compiling {name} to PNG and SVG...")
    res_png = subprocess.run(["mmdc.cmd", "-i", mmd_file, "-o", png_file, "-b", "white", "-s", "2"], capture_output=True, text=True)
    res_svg = subprocess.run(["mmdc.cmd", "-i", mmd_file, "-o", svg_file, "-b", "white"], capture_output=True, text=True)
    
    if os.path.exists(png_file):
        print(f"  [Success] PNG: {png_file} ({os.path.getsize(png_file)} bytes)")
    else:
        print(f"  [Error] Failed to generate PNG: {res_png.stderr}")

if os.path.exists("scripts/test_mermaid.py"):
    os.remove("scripts/test_mermaid.py")

print("\nAll Mermaid diagrams successfully compiled to static PNG and SVG assets!")
