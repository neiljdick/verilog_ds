# Top-level Makefile for SystemVerilog Data Structures project

.PHONY: help setup test test-unit test-integration clean waves lint format

help:
	@echo "SystemVerilog Data Structures Test Environment"
	@echo ""
	@echo "Available targets:"
	@echo "  setup          - Set up Python virtual environment"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests"
	@echo "  test-integration - Run integration tests"
	@echo "  waves          - Open waveform viewer (gtkwave)"
	@echo "  clean          - Clean build artifacts"
	@echo "  lint           - Run Python linting"
	@echo "  format         - Format Python code"
	@echo "  help           - Show this help message"

setup:
	@echo "Setting up Python virtual environment..."
	@if [ ! -d "venv" ]; then \
		python3 -m venv venv; \
	fi
	@echo "Installing dependencies..."
	@. venv/bin/activate && pip install -r requirements.txt
	@echo "Setup complete! Activate with: source venv/bin/activate"

test: test-unit

test-unit:
	@echo "Running unit tests..."
	@. venv/bin/activate && $(MAKE) -C tests/unit

test-integration:
	@echo "Running integration tests..."
	@. venv/bin/activate && $(MAKE) -C tests/integration

waves:
	@$(MAKE) -C tests/unit waves

lint:
	@echo "Running Python linting..."
	@. venv/bin/activate && flake8 tests/ --max-line-length=88

format:
	@echo "Formatting Python code..."
	@. venv/bin/activate && black tests/

clean:
	@echo "Cleaning build artifacts..."
	@$(MAKE) -C tests/unit clean
	@$(MAKE) -C tests/integration clean
	@rm -rf venv
	@find . -name "__pycache__" -type d -exec rm -rf {} +
	@find . -name "*.pyc" -delete
