# Top-level Makefile for unit tests
# Orchestrates testing across all unit test subdirectories

# Test subdirectories
TEST_DIRS = hello_world btree_set

# Default target runs all unit tests
.PHONY: all clean waves lint-sv $(TEST_DIRS)

all: $(TEST_DIRS)

# Run tests in each subdirectory
$(TEST_DIRS):
	@echo "\n=== Running tests for $@ ==="
	@$(MAKE) -C $@
	@echo "=== $@ tests completed ===\n"

# Clean all test subdirectories
clean:
	@echo "Cleaning all unit test directories..."
	@for dir in $(TEST_DIRS); do \
		echo "Cleaning $$dir..."; \
		$(MAKE) -C $$dir clean 2>/dev/null || true; \
	done
	@echo "Unit test cleanup complete"

# Run linting on all SystemVerilog sources
lint-sv:
	@echo "Running SystemVerilog linting for all modules..."
	@for dir in $(TEST_DIRS); do \
		echo "Linting $$dir..."; \
		$(MAKE) -C $$dir lint-sv; \
	done
	@echo "SystemVerilog linting complete for all modules"

# Open waveforms (from last run directory)
waves:
	@echo "Looking for waveform files..."
	@for dir in $(TEST_DIRS); do \
		if [ -f $$dir/dump.vcd ]; then \
			echo "Opening waveforms from $$dir"; \
			$(MAKE) -C $$dir waves; \
			break; \
		fi; \
	done

# Help target
help:
	@echo "Unit Test Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  all       - Run all unit tests (default)"
	@echo "  clean     - Clean all test directories"
	@echo "  lint-sv   - Run SystemVerilog linting on all modules"
	@echo "  waves     - Open waveform viewer"
	@echo "  help      - Show this help message"
	@echo ""
	@echo "Individual module targets:"
	@for dir in $(TEST_DIRS); do \
		echo "  $$dir      - Run tests for $$dir module"; \
	done
	@echo ""
	@echo "Module-specific targets (run in module directory):"
	@echo "  make -C btree_set test-simple  - Run simple btree tests"
	@echo "  make -C btree_set test-debug   - Run debug btree tests"
