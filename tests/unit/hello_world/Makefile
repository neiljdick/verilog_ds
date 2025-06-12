# Makefile for hello_world cocotb tests with Verilator

# Simulator
SIM ?= verilator

# Project directories
RTL_DIR = ../../../rtl
TEST_DIR = .

# Python test module
MODULE = test_hello_world

# Top level module
TOPLEVEL = hello_world

# SystemVerilog source files
VERILOG_SOURCES = $(RTL_DIR)/hello_world.sv

# Verilator specific flags
EXTRA_ARGS += --trace --trace-structs
EXTRA_ARGS += -Wall -Wno-fatal
EXTRA_ARGS += --timescale 1ns/1ps
EXTRA_ARGS += --assert

# Include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

# Additional targets
.PHONY: waves lint-sv

waves:
	@echo "Opening waveform viewer..."
	@if command -v gtkwave >/dev/null 2>&1; then \
		gtkwave dump.vcd; \
	else \
		echo "gtkwave not found. Install with 'apt install gtkwave'"; \
	fi

lint-sv:
	@echo "Linting SystemVerilog sources..."
	@verilator --lint-only -Wall --timescale 1ns/1ps --assert $(VERILOG_SOURCES)
	@echo "SystemVerilog linting complete!"
