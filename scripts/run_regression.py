"""
run_regression.py - Automated SystemVerilog regression runner via Vivado Simulator.
Compiles and simulates N in {4, 8, 16, 32, 64} across all 12 test classes.
Enforces 0-LSB exact match gate.
"""

import os
import subprocess
import sys
import time

VIVADO_BIN = r"C:\AMDDesignTools\2026.1\Vivado\bin"

RTL_SOURCES = [
    "rtl/fixed_point_pkg.sv",
    "rtl/complex_mult.sv",
    "rtl/butterfly.sv",
    "rtl/twiddle_rom.sv",
    "rtl/data_ram.sv",
    "rtl/fft_controller.sv",
    "rtl/fft_top.sv",
    "tb/tb_fft_top.sv",
]

SIZES = [4, 8, 16, 32, 64]


def run_cmd(cmd, env=None):
    if env is None:
        env = os.environ.copy()
        env["PATH"] = VIVADO_BIN + os.pathsep + env.get("PATH", "")
    p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    return p.returncode, p.stdout


def main():
    print("======================================================================")
    print("  Starting Automated FFT System Regression (Vivado Simulator)")
    print("======================================================================")
    
    # 1. Compile base RTL and TB sources
    print("--> Step 1: Compiling SystemVerilog Sources via xvlog...")
    src_cmd = f"xvlog -sv " + " ".join(RTL_SOURCES)
    code, out = run_cmd(src_cmd)
    if code != 0:
        print(f"ERROR: xvlog compilation failed:\n{out}")
        sys.exit(1)
    print("   Compilation successful.")
    
    # 2. Iterate through each size
    regression_results = []
    
    for n in SIZES:
        tb_wrapper = f"tb/tb_fft_top_n{n}.sv"
        snapshot = f"tb_fft_top_n{n}_snapshot"
        print(f"\n--> Step 2: Testing N={n} (Wrapper: {tb_wrapper})...")
        
        # Compile wrapper
        code, out = run_cmd(f"xvlog -sv {tb_wrapper}")
        if code != 0:
            print(f"ERROR compiling {tb_wrapper}:\n{out}")
            sys.exit(1)
            
        # Elaborate snapshot
        elab_cmd = f"xelab -debug typical -top work.tb_fft_top_n{n} -snapshot {snapshot}"
        code, out = run_cmd(elab_cmd)
        if code != 0:
            print(f"ERROR elaborating snapshot {snapshot}:\n{out}")
            sys.exit(1)
            
        # Run xsim
        sim_cmd = f"xsim {snapshot} -R"
        t0 = time.time()
        code, sim_out = run_cmd(sim_cmd)
        elapsed = time.time() - t0
        
        # Parse simulation output
        passed = "ALL tb_fft_top TESTS PASSED (0 LSB MISMATCH)" in sim_out
        mismatches = 0
        total_tests = 0
        for line in sim_out.splitlines():
            if "Total Tests:" in line:
                # e.g. Total Tests: 12 | Mismatches: 0
                parts = line.split("|")
                try:
                    total_tests = int(parts[0].split(":")[1].strip())
                    mismatches = int(parts[1].split(":")[1].strip())
                except Exception:
                    pass
                    
        status_str = "PASS (0 LSB Diff)" if (passed and mismatches == 0) else f"FAIL ({mismatches} mismatches)"
        print(f"   N={n:2d} Result: {status_str} | Tests Run: {total_tests} | Sim Time: {elapsed:.2f}s")
        
        regression_results.append({
            "N": n,
            "Status": "PASS" if passed else "FAIL",
            "Tests_Run": total_tests,
            "Mismatches": mismatches,
            "Elapsed_Sec": f"{elapsed:.2f}"
        })
        
        if not passed:
            print(f"Log excerpt for N={n}:\n{sim_out[-2000:]}")
            
    print("\n======================================================================")
    print("  Regression Summary Table")
    print("======================================================================")
    print(f"{'N':>4} | {'Status':>6} | {'Tests Run':>10} | {'Mismatches':>10} | {'Runtime (s)':>12}")
    print("-" * 55)
    all_passed = True
    for r in regression_results:
        print(f"{r['N']:4d} | {r['Status']:>6} | {r['Tests_Run']:10d} | {r['Mismatches']:10d} | {r['Elapsed_Sec']:>12}")
        if r['Status'] != "PASS":
            all_passed = False
            
    # Save markdown summary
    os.makedirs("docs", exist_ok=True)
    with open("docs/regression_summary.md", "w") as f:
        f.write("# Automated FFT Simulation Regression Summary\n\n")
        f.write("| N | Status | Tests Run | Mismatches | Vivado Runtime (s) |\n")
        f.write("| :---: | :---: | :---: | :---: | :---: |\n")
        for r in regression_results:
            f.write(f"| **{r['N']}** | {r['Status']} | {r['Tests_Run']} | {r['Mismatches']} | {r['Elapsed_Sec']} s |\n")
        f.write(f"\n**All-Pass Gate (0 LSB):** {'PASSED' if all_passed else 'FAILED'}\n")
        
    if all_passed:
        print("\n>>> ALL REGRESSION SUITES PASSED WITH 0 LSB MISMATCH! <<<")
        sys.exit(0)
    else:
        print("\n>>> REGRESSION FAILED! <<<")
        sys.exit(1)


if __name__ == "__main__":
    main()
