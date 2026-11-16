# ==============================================================================
# run_sim.tcl: Headless Vivado xsim batch simulation runner
# Usage:
#   vivado -mode batch -source scripts/run_sim.tcl -tclargs [TB_NAME]
# Default TB_NAME: tb_complex_mult
# ==============================================================================

set DEFAULT_TB "tb_complex_mult"
if { $argc > 0 } {
    set TB_NAME [lindex $argv 0]
} else {
    set TB_NAME $DEFAULT_TB
}

puts "======================================================================"
puts "  Running Simulation for Testbench: $TB_NAME"
puts "======================================================================"

set BUILD_DIR "build/sim_$TB_NAME"
file mkdir $BUILD_DIR
cd $BUILD_DIR

# Define source file lists based on testbench
set SV_FILES [list]
lappend SV_FILES "../../rtl/fixed_point_pkg.sv"

if { $TB_NAME == "tb_complex_mult" } {
    lappend SV_FILES "../../rtl/complex_mult.sv"
    lappend SV_FILES "../../tb/tb_complex_mult.sv"
} elseif { $TB_NAME == "tb_butterfly" } {
    lappend SV_FILES "../../rtl/complex_mult.sv"
    lappend SV_FILES "../../rtl/butterfly.sv"
    lappend SV_FILES "../../tb/tb_butterfly.sv"
} elseif { $TB_NAME == "tb_fft_top" } {
    lappend SV_FILES "../../rtl/complex_mult.sv"
    lappend SV_FILES "../../rtl/butterfly.sv"
    lappend SV_FILES "../../rtl/twiddle_rom.sv"
    lappend SV_FILES "../../rtl/data_ram_banked.sv"
    lappend SV_FILES "../../rtl/fft_controller.sv"
    lappend SV_FILES "../../rtl/fft_top.sv"
    lappend SV_FILES "../../tb/tb_fft_top.sv"
} else {
    # Generic attempt: load all RTL and tb
    foreach f [glob -nocomplain ../../rtl/*.sv] {
        if {[lsearch -exact $SV_FILES $f] < 0} {
            lappend SV_FILES $f
        }
    }
    lappend SV_FILES "../../tb/$TB_NAME.sv"
}

# Compile SystemVerilog files
puts "--> Compiling SystemVerilog files..."
foreach f $SV_FILES {
    if {[file exists $f]} {
        puts "   xvlog -sv $f"
        if {[catch {exec xvlog -sv $f} err]} {
            puts "ERROR during xvlog compilation of $f:\n$err"
            exit 1
        }
    } else {
        puts "WARNING: File not found: $f"
    }
}

# Elaborate snapshot
puts "--> Elaborating snapshot: work.${TB_NAME}_snapshot..."
if {[catch {exec xelab -debug typical -top "work.$TB_NAME" -snapshot "${TB_NAME}_snapshot"} err]} {
    puts "ERROR during xelab elaboration:\n$err"
    exit 2
}

# Run simulation
puts "--> Running xsim..."
if {[catch {exec xsim "${TB_NAME}_snapshot" -R} sim_output]} {
    puts "Simulation execution completed with output/error:\n$sim_output"
} else {
    puts "$sim_output"
}

puts "======================================================================"
puts "  Simulation for $TB_NAME finished."
puts "======================================================================"
exit 0
