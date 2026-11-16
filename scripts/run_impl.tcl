# ==============================================================================
# run_impl.tcl: Headless Vivado synthesis, implementation and report generation
# Usage:
#   vivado -mode batch -source scripts/run_impl.tcl
# ==============================================================================

set PART "xcu50-fsvh2104-2-e"
set TOP  "fft_top"

puts "======================================================================"
puts "  Starting Implementation for $TOP on Part: $PART"
puts "======================================================================"

set BUILD_DIR "build/impl"
file mkdir $BUILD_DIR
set REPORT_DIR "reports"
file mkdir $REPORT_DIR

# Read SystemVerilog files
read_verilog -sv rtl/fixed_point_pkg.sv
read_verilog -sv rtl/complex_mult.sv
read_verilog -sv rtl/butterfly.sv
read_verilog -sv rtl/twiddle_rom.sv
read_verilog -sv rtl/data_ram.sv
read_verilog -sv rtl/fft_controller.sv
read_verilog -sv rtl/fft_top.sv

# Read constraints
read_xdc constraints/timing.xdc

# Synthesis (Out of context for top-level IP evaluation)
puts "--> Running Synthesis..."
synth_design -top $TOP -part $PART -mode out_of_context

# Opt Design
puts "--> Running opt_design..."
opt_design

# Place Design
puts "--> Running place_design..."
place_design

# Route Design
puts "--> Running route_design..."
route_design

# Write Checkpoint
write_checkpoint -force "$BUILD_DIR/${TOP}_routed.dcp"

# Generate Reports
puts "--> Generating Reports..."
report_utilization -file "$REPORT_DIR/utilization_route.rpt" -pb "$REPORT_DIR/utilization_route.pb"
report_timing_summary -file "$REPORT_DIR/timing_summary_route.rpt"
report_power -file "$REPORT_DIR/power_route.rpt"

puts "======================================================================"
puts "  Implementation finished successfully. Reports saved in $REPORT_DIR/"
puts "======================================================================"
exit 0
