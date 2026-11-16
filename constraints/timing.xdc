# Timing constraints for 64-point Radix-2 FFT Accelerator
# Target FPGA: AMD Alveo U50 Accelerator (xcu50-fsvh2104-2-e, UltraScale+)
# Target Clock: 100 MHz (Period: 10.000 ns, 50% duty cycle)

create_clock -period 10.000 -name sys_clk -waveform {0.000 5.000} [get_ports clk]

# Input delays relative to sys_clk (2.0 ns max setup, 0.5 ns min hold margin)
set_input_delay -clock sys_clk -max 2.000 [get_ports {rst_n s_axis_tvalid s_axis_tdata* s_axis_tlast m_axis_tready}]
set_input_delay -clock sys_clk -min 0.500 [get_ports {rst_n s_axis_tvalid s_axis_tdata* s_axis_tlast m_axis_tready}]

# Output delays relative to sys_clk
set_output_delay -clock sys_clk -max 2.000 [get_ports {s_axis_tready m_axis_tvalid m_axis_tdata* m_axis_tlast}]
set_output_delay -clock sys_clk -min 0.500 [get_ports {s_axis_tready m_axis_tvalid m_axis_tdata* m_axis_tlast}]
