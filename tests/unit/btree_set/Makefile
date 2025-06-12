# Makefile for btree_set cocotb tests with Verilator

# Simulator
SIM ?= verilator

# Project directories
RTL_DIR = ../../../rtl
TEST_DIR = .

# Python test module (default to comprehensive test suite)
MODULE ?= test_btree_set

# Top level module
TOPLEVEL = btree_set

# SystemVerilog source files
VERILOG_SOURCES = $(RTL_DIR)/btree_set.sv

# Verilator specific flags
EXTRA_ARGS += --trace --trace-structs
EXTRA_ARGS += -Wall -Wno-fatal
EXTRA_ARGS += --timescale 1ns/1ps
EXTRA_ARGS += --assert

# Include cocotb's make rules to take care of the simulator setup
include $(shell cocotb-config --makefiles)/Makefile.sim

# Additional targets
.PHONY: waves lint-sv test-simple test-debug

test-simple:
	@echo "Running simple btree_set tests..."
	@$(MAKE) MODULE=test_btree_simple

test-debug:
	@echo "Running debug btree_set tests..."
	@$(MAKE) MODULE=test_btree_debug_simple

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
