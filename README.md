# SystemVerilog Data Structures with cocotb

A test environment for implementing and testing SystemVerilog data structures using Verilator and cocotb.

## Project Structure

```
├── rtl/                    # SystemVerilog source files
│   ├── hello_world.sv      # Example counter module with enable/overflow
│   ├── btree_set.sv        # Binary tree set with implicit heap indexing
│   └── cuckoo_hash.sv      # Complete cuckoo hash table implementation
├── tests/
│   ├── unit/              # Unit tests (organized by module)
│   │   ├── Makefile       # Top-level unit test orchestrator
│   │   ├── hello_world/   # Hello world module tests (4 tests)
│   │   │   ├── Makefile   # Module-specific Makefile
│   │   │   └── test_hello_world.py  # cocotb test file
│   │   ├── btree_set/     # Binary tree set tests (6 tests)
│   │   │   ├── Makefile   # Module-specific Makefile
│   │   │   └── test_btree_set.py    # cocotb test file
│   │   └── cuckoo_hash/   # Cuckoo hash table tests (25 tests)
│   │       ├── Makefile   # Module-specific Makefile
│   │       └── test_cuckoo_hash.py  # Consolidated test file
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

# Run specific module tests
cd tests/unit && make hello_world
cd tests/unit && make btree_set
cd tests/unit && make cuckoo_hash

# Run all unit tests from tests/unit
cd tests/unit && make all

# Module-specific test variants
cd tests/unit/btree_set && make test-simple
cd tests/unit/btree_set && make test-debug

# Lint SystemVerilog code
make lint-sv
cd tests/unit && make lint-sv  # Lint all modules

# Open waveform viewer (requires gtkwave)
make waves
cd tests/unit && make waves    # From any recent test
```

### Available Make Targets

- `make help` - Show available targets
- `make setup` - Set up Python virtual environment
- `make test` - Run all tests
- `make test-unit` - Run unit tests only
- `make lint-sv` - Lint SystemVerilog code with Verilator
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

## Implemented Data Structures

The repository includes three complete SystemVerilog modules with comprehensive test coverage:

### 1. Hello World Counter (`rtl/hello_world.sv`)

- **Features**: Parameterized counter with enable, reset, and overflow detection
- **Tests**: 4 comprehensive tests covering basic functionality and edge cases  
- **Demonstrates**: Clock generation, reset testing, sequential logic verification

### 2. Binary Tree Set (`rtl/btree_set.sv`)

- **Features**: Set data structure with insert and search operations
- **Implementation**: Uses implicit heap indexing (`left = 2*i+1, right = 2*i+2`)
- **Tests**: 6 tests covering insert/search, collision detection, multiple values, and random operations
- **State Machines**: Uses SystemVerilog enumerations for insert and search states

### 3. Cuckoo Hash Table (`rtl/cuckoo_hash.sv`)

- **Features**: Complete hash table with O(1) worst-case lookup, insert, and delete
- **Implementation**: Dual hash tables with eviction chain handling
- **Parameters**: Configurable KEY_WIDTH=32, VALUE_WIDTH=32, TABLE_SIZE=64
- **Tests**: 25 comprehensive tests organized in categories:
  - **Skeleton Tests (5)**: Interface validation and basic functionality
  - **Lookup Tests (6)**: Hash functions, empty table, state machine timing
  - **Insert Tests (7)**: Basic insert, collision detection, eviction logic
  - **Delete Tests (5)**: Key removal, occupancy management, cross-table deletion
  - **Integration Tests (2)**: End-to-end validation and stress testing

### Running Examples

```bash
# Test individual modules
cd tests/unit && source ../../venv/bin/activate
make hello_world    # 4/4 tests pass
make btree_set      # 6/6 tests pass  
make cuckoo_hash    # 25/25 tests pass

# Test all modules
make all           # 35/35 total tests pass
```

### Key Features Demonstrated

- **SystemVerilog Best Practices**: Parameterized modules, enumerated types, proper reset handling
- **State Machine Design**: Complex multi-state operations with proper timing
- **Memory Management**: Dual hash tables, occupancy tracking, eviction algorithms
- **Comprehensive Testing**: Unit tests, integration tests, stress testing with random operations
- **Hardware Verification**: Clock-accurate timing, assertion-based testing, waveform generation

## Project Status

✅ **Complete**: Full SystemVerilog data structures test environment with three working implementations

### Implemented & Tested:
- ✅ Hello World Counter (4 tests passing)
- ✅ Binary Tree Set with heap indexing (6 tests passing)  
- ✅ Cuckoo Hash Table with full CRUD operations (25 tests passing)
- ✅ Comprehensive test framework with cocotb + Verilator
- ✅ Automated build system with modular Makefiles
- ✅ SystemVerilog linting and code quality checks

### Ready for Extension:
This environment is ready for implementing additional SystemVerilog data structures:

- Queues and FIFOs
- Stacks  
- Linked lists
- Advanced tree structures (AVL, Red-Black)
- Bloom filters
- Custom memory architectures

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
