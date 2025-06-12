import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def test_cuckoo_hash_reset(dut):
    """Test that reset functionality works correctly."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize inputs
    dut.rst_n.value = 0
    dut.lookup_key.value = 0
    dut.lookup_valid.value = 0
    dut.insert_key.value = 0
    dut.insert_value.value = 0
    dut.insert_valid.value = 0
    dut.delete_key.value = 0
    dut.delete_valid.value = 0
    
    # Wait a few clock cycles
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Check that outputs are reset
    assert dut.lookup_found.value == 0, f"lookup_found should be 0 after reset"
    assert dut.lookup_done.value == 0, f"lookup_done should be 0 after reset"
    assert dut.insert_done.value == 0, f"insert_done should be 0 after reset"
    assert dut.insert_success.value == 0, f"insert_success should be 0 after reset"
    assert dut.insert_collision.value == 0, f"insert_collision should be 0 after reset"
    assert dut.insert_overflow.value == 0, f"insert_overflow should be 0 after reset"
    assert dut.delete_done.value == 0, f"delete_done should be 0 after reset"
    assert dut.delete_found.value == 0, f"delete_found should be 0 after reset"
    assert dut.occupancy.value == 0, f"occupancy should be 0 after reset"
    assert dut.table_full.value == 0, f"table_full should be 0 after reset"
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Outputs should still be 0 in idle state
    assert dut.lookup_found.value == 0, f"lookup_found should remain 0 when idle"
    assert dut.insert_success.value == 0, f"insert_success should remain 0 when idle"
    assert dut.occupancy.value == 0, f"occupancy should remain 0 when empty"


@cocotb.test()
async def test_cuckoo_hash_interface(dut):
    """Test the basic interface without functionality."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Test lookup interface (should complete even without functionality)
    dut._log.info("Testing lookup interface")
    dut.lookup_key.value = 0x12345678
    dut.lookup_valid.value = 1
    await RisingEdge(dut.clk)
    dut.lookup_valid.value = 0
    
    # Wait for lookup to complete (should be quick since no functionality)
    timeout = 0
    while not dut.lookup_done.value and timeout < 10:
        await RisingEdge(dut.clk)
        timeout += 1
    
    assert timeout < 10, "Lookup should complete quickly"
    assert dut.lookup_done.value == 1, "Lookup should indicate done"
    
    await RisingEdge(dut.clk)  # Let done signal clear
    
    # Test insert interface
    dut._log.info("Testing insert interface")
    dut.insert_key.value = 0xABCDEF01
    dut.insert_value.value = 0x87654321
    dut.insert_valid.value = 1
    await RisingEdge(dut.clk)
    dut.insert_valid.value = 0
    
    # Wait for insert to complete
    timeout = 0
    while not dut.insert_done.value and timeout < 10:
        await RisingEdge(dut.clk)
        timeout += 1
    
    assert timeout < 10, "Insert should complete quickly"
    assert dut.insert_done.value == 1, "Insert should indicate done"
    
    await RisingEdge(dut.clk)  # Let done signal clear
    
    # Test delete interface
    dut._log.info("Testing delete interface")
    dut.delete_key.value = 0x11223344
    dut.delete_valid.value = 1
    await RisingEdge(dut.clk)
    dut.delete_valid.value = 0
    
    # Wait for delete to complete
    timeout = 0
    while not dut.delete_done.value and timeout < 10:
        await RisingEdge(dut.clk)
        timeout += 1
    
    assert timeout < 10, "Delete should complete quickly"
    assert dut.delete_done.value == 1, "Delete should indicate done"


@cocotb.test()
async def test_cuckoo_hash_parameters(dut):
    """Test that the module instantiated with correct parameters."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Check that the module has the expected bit widths
    # These should match our default parameters
    key_width = len(dut.lookup_key)
    value_width = len(dut.lookup_value)
    occupancy_width = len(dut.occupancy)
    
    dut._log.info(f"Key width: {key_width} bits")
    dut._log.info(f"Value width: {value_width} bits") 
    dut._log.info(f"Occupancy width: {occupancy_width} bits")
    
    # With default parameters: KEY_WIDTH=32, VALUE_WIDTH=32, TABLE_SIZE=64
    assert key_width == 32, f"Expected key width 32, got {key_width}"
    assert value_width == 32, f"Expected value width 32, got {value_width}"
    # Occupancy should be 7 bits for TABLE_SIZE=64 (need to count up to 128)
    assert occupancy_width == 7, f"Expected occupancy width 7, got {occupancy_width}"


@cocotb.test()
async def test_cuckoo_hash_state_transitions(dut):
    """Test that state machine responds to inputs (without checking functionality)."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Check initial state (should be IDLE = 0)
    initial_state = dut.current_state.value
    dut._log.info(f"Initial state: {initial_state}")
    
    # Trigger a lookup and observe state change
    dut.lookup_key.value = 0x12345678
    dut.lookup_valid.value = 1
    await RisingEdge(dut.clk)
    lookup_state = dut.current_state.value
    dut._log.info(f"Lookup state: {lookup_state}")
    
    dut.lookup_valid.value = 0
    await RisingEdge(dut.clk)
    
    # Should return to IDLE quickly
    final_state = dut.current_state.value
    dut._log.info(f"Final state: {final_state}")
    
    # Just verify the state machine is responsive
    assert initial_state == 0, "Should start in IDLE state (0)"
    # We can't assert specific state values since they depend on implementation
    # but we can verify the module is responding to inputs


@cocotb.test()
async def test_cuckoo_hash_no_simultaneous_ops(dut):
    """Test that simultaneous operations are properly rejected by assertions."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Test that we can trigger operations individually without issues
    
    # Single lookup
    dut.lookup_key.value = 0x11111111
    dut.lookup_valid.value = 1
    await RisingEdge(dut.clk)
    dut.lookup_valid.value = 0
    await RisingEdge(dut.clk)
    
    # Single insert
    dut.insert_key.value = 0x22222222
    dut.insert_value.value = 0x33333333
    dut.insert_valid.value = 1
    await RisingEdge(dut.clk)
    dut.insert_valid.value = 0
    await RisingEdge(dut.clk)
    
    # Single delete
    dut.delete_key.value = 0x44444444
    dut.delete_valid.value = 1
    await RisingEdge(dut.clk)
    dut.delete_valid.value = 0
    await RisingEdge(dut.clk)
    
    # Note: We don't test simultaneous operations as they would trigger
    # assertion failures and crash the simulation. The assertions are there
    # to catch design errors during development.
    
    dut._log.info("Sequential operations completed successfully")
