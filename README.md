# SystemVerilog Data Structures with cocotb

A test environment for implementing and testing SystemVerilog data structures using Verilator and cocotb.

## Project Structure

```
├── rtl/                    # SystemVerilog source files
│   └── hello_world.sv      # Example counter module
├── tests/
│   ├── unit/              # Unit tests
│   │   ├── Makefile       # Test-specific Makefile
│   │   └── test_*.py      # cocotb test files
│   └── integration/       # Integration tests
├── scripts/               # Utility scripts
├── docs/                  # Documentation
├── Makefile              # Top-level Makefile
├── requirements.txt      # Python dependencies
└── pyproject.toml        # Python project configuration
```

## Setup

### Prerequisites

- Ubuntu/Debian system
- Python 3.8+
- Verilator (automatically installed)

### Quick Start

1. **Set up the environment:**
   ```bash
   make setup
   ```

2. **Activate the virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Run tests:**
   ```bash
   make test
   ```

### Manual Setup

If you prefer manual setup:

```bash
# Install Verilator
sudo apt update && sudo apt install -y verilator

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

## Usage

### Running Tests

```bash
# Run all tests
make test

# Run only unit tests
make test-unit

# Run integration tests
make test-integration

# Open waveform viewer (requires gtkwave)
make waves
```

### Available Make Targets

- `make help` - Show available targets
- `make setup` - Set up Python virtual environment
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make waves` - Open waveform viewer
- `make clean` - Clean build artifacts
- `make lint` - Run Python linting
- `make format` - Format Python code

## Writing Tests

### SystemVerilog Modules

Place your SystemVerilog modules in the `rtl/` directory:

```systemverilog
module my_module #(
    parameter WIDTH = 8
) (
    input  logic clk,
    input  logic rst_n,
    // ... other ports
);
    // Module implementation
endmodule
```

### cocotb Tests

Create test files in `tests/unit/` with the naming pattern `test_*.py`:

```python
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge

@cocotb.test()
async def test_my_module(dut):
    """Test my module functionality."""
    # Create clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Test logic here
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Assertions
    assert dut.output.value == expected_value
```

### Test Configuration

Update the `Makefile` in `tests/unit/` for your module:

```makefile
# Test module name
MODULE = test_my_module

# Top level SystemVerilog module
TOPLEVEL = my_module

# SystemVerilog source files
VERILOG_SOURCES = $(RTL_DIR)/my_module.sv
```

## Tools and Dependencies

### Core Tools

- **Verilator**: High-performance SystemVerilog simulator
- **cocotb**: Python-based verification framework
- **pytest**: Python testing framework

### Python Dependencies

- `cocotb>=1.8.0` - Main testing framework
- `cocotb-test>=0.2.4` - Test utilities
- `pytest>=7.0.0` - Testing framework
- `pytest-xdist>=2.5.0` - Parallel test execution
- `pytest-cov>=4.0.0` - Coverage reporting

### Optional Tools

- `gtkwave` - Waveform viewer (install with `sudo apt install gtkwave`)
- `black` - Python code formatter
- `flake8` - Python linter

## Example: Hello World Counter

The repository includes a working example with:

- **`rtl/hello_world.sv`**: A simple parameterized counter with enable and overflow
- **`tests/unit/test_*.py`**: Various test approaches for the counter
- **Makefile configuration**: Ready-to-use build setup

### Running the Example

```bash
cd tests/unit
source ../../venv/bin/activate
make  # This will run the hello_world tests
```

This demonstrates:
- Clock generation
- Reset testing
- Sequential logic verification
- Parameterized testing
- Waveform generation

## Next Steps

This environment is ready for implementing SystemVerilog data structures such as:

- Queues and FIFOs
- Stacks
- Linked lists
- Hash tables
- Trees and heaps
- Custom memory structures

## Troubleshooting

### Common Issues

1. **Verilator not found**: Install with `sudo apt install verilator`
2. **Python venv issues**: Install with `sudo apt install python3.12-venv`
3. **Permission errors**: Ensure you're in the project directory
4. **Test failures**: Check timing in your tests - SystemVerilog is cycle-accurate

### Getting Help

- Check the cocotb documentation: https://docs.cocotb.org/
- Verilator manual: https://verilator.org/guide/latest/
- SystemVerilog reference: IEEE 1800-2017 standard
