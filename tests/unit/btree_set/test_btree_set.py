import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random


@cocotb.test()
async def test_btree_set_reset(dut):
    """Test that reset functionality works correctly."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize inputs
    dut.rst_n.value = 0
    dut.data.value = 0
    dut.insert.value = 0
    dut.search.value = 0
    
    # Wait a few clock cycles
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Check that outputs are reset
    assert dut.found.value == 0, f"found should be 0 after reset"
    assert dut.insert_collision.value == 0, f"insert_collision should be 0 after reset"
    assert dut.insert_done.value == 0, f"insert_done should be 0 after reset"
    assert dut.search_done.value == 0, f"search_done should be 0 after reset"
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Outputs should still be 0 in idle state
    assert dut.found.value == 0, f"found should remain 0 when idle"
    assert dut.insert_collision.value == 0, f"insert_collision should remain 0 when idle"
    assert dut.insert_done.value == 0, f"insert_done should remain 0 when idle"
    assert dut.search_done.value == 0, f"search_done should remain 0 when idle"


@cocotb.test()
async def test_btree_set_single_insert_and_search(dut):
    """Test inserting a single element and searching for it."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.data.value = 0
    dut.insert.value = 0
    dut.search.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Insert value 42
    dut.data.value = 42
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    # Wait for insert to complete
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    # Check insert completed successfully without collision
    assert dut.insert_done.value == 1, "Insert should be done"
    assert dut.insert_collision.value == 0, "First insert should not have collision"
    
    await RisingEdge(dut.clk)  # insert_done goes low after one cycle
    
    # Search for the inserted value
    dut.data.value = 42
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    # Wait for search to complete
    while not dut.search_done.value:
        await RisingEdge(dut.clk)
    
    # Check search found the value
    assert dut.search_done.value == 1, "Search should be done"
    assert dut.found.value == 1, "Should find the inserted value"
    
    await RisingEdge(dut.clk)  # search_done goes low after one cycle
    
    # Search for a value that wasn't inserted
    dut.data.value = 99
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    # Wait for search to complete
    while not dut.search_done.value:
        await RisingEdge(dut.clk)
    
    # Check search didn't find the value
    assert dut.search_done.value == 1, "Search should be done"
    assert dut.found.value == 0, "Should not find non-inserted value"


@cocotb.test()
async def test_btree_set_insert_collision(dut):
    """Test inserting the same value twice causes collision."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.data.value = 0
    dut.insert.value = 0
    dut.search.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Insert value 123
    dut.data.value = 123
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    # Wait for insert to complete
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    # Check first insert succeeded
    assert dut.insert_collision.value == 0, "First insert should not have collision"
    
    await RisingEdge(dut.clk)
    
    # Try to insert the same value again
    dut.data.value = 123
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    # Wait for insert to complete
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    # Check second insert caused collision
    assert dut.insert_done.value == 1, "Insert should be done"
    assert dut.insert_collision.value == 1, "Second insert should have collision"


@cocotb.test()
async def test_btree_set_multiple_inserts(dut):
    """Test inserting multiple values and searching for them."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.data.value = 0
    dut.insert.value = 0
    dut.search.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Values to insert (will create a balanced-ish tree)
    values_to_insert = [50, 25, 75, 10, 30, 60, 80]
    
    # Insert all values
    for value in values_to_insert:
        dut._log.info(f"Inserting value: {value}")
        dut.data.value = value
        dut.insert.value = 1
        await RisingEdge(dut.clk)
        dut.insert.value = 0
        
        # Wait for insert to complete
        while not dut.insert_done.value:
            await RisingEdge(dut.clk)
        
        # Check insert succeeded without collision
        assert dut.insert_collision.value == 0, f"Insert of {value} should not have collision"
        await RisingEdge(dut.clk)
    
    # Search for all inserted values
    for value in values_to_insert:
        dut._log.info(f"Searching for value: {value}")
        dut.data.value = value
        dut.search.value = 1
        await RisingEdge(dut.clk)
        dut.search.value = 0
        
        # Wait for search to complete
        while not dut.search_done.value:
            await RisingEdge(dut.clk)
        
        # Check search found the value
        assert dut.found.value == 1, f"Should find inserted value {value}"
        await RisingEdge(dut.clk)
    
    # Search for values not in the set
    missing_values = [5, 15, 35, 55, 70, 85, 100]
    for value in missing_values:
        dut._log.info(f"Searching for missing value: {value}")
        dut.data.value = value
        dut.search.value = 1
        await RisingEdge(dut.clk)
        dut.search.value = 0
        
        # Wait for search to complete
        while not dut.search_done.value:
            await RisingEdge(dut.clk)
        
        # Check search didn't find the value
        assert dut.found.value == 0, f"Should not find missing value {value}"
        await RisingEdge(dut.clk)


@cocotb.test()
async def test_btree_set_edge_cases(dut):
    """Test edge cases like inserting zero and maximum values."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.data.value = 0
    dut.insert.value = 0
    dut.search.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Test with zero value
    dut.data.value = 0
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.insert_collision.value == 0, "Insert of 0 should succeed"
    await RisingEdge(dut.clk)
    
    # Search for zero
    dut.data.value = 0
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    while not dut.search_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.found.value == 1, "Should find inserted zero value"
    await RisingEdge(dut.clk)
    
    # Test with maximum 32-bit value
    max_val = (2**32) - 1
    dut.data.value = max_val
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.insert_collision.value == 0, "Insert of max value should succeed"
    await RisingEdge(dut.clk)
    
    # Search for max value
    dut.data.value = max_val
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    while not dut.search_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.found.value == 1, "Should find inserted max value"


@cocotb.test()
async def test_btree_set_random_operations(dut):
    """Test with random insert and search operations."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.data.value = 0
    dut.insert.value = 0
    dut.search.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Keep track of inserted values
    inserted_values = set()
    
    # Perform random operations
    for _ in range(20):
        value = random.randint(1, 100)
        
        # Insert the value
        dut._log.info(f"Inserting random value: {value}")
        dut.data.value = value
        dut.insert.value = 1
        await RisingEdge(dut.clk)
        dut.insert.value = 0
        
        while not dut.insert_done.value:
            await RisingEdge(dut.clk)
        
        # Check if collision matches our expectation
        expected_collision = value in inserted_values
        actual_collision = bool(dut.insert_collision.value)
        assert actual_collision == expected_collision, f"Collision mismatch for {value}: expected {expected_collision}, got {actual_collision}"
        
        inserted_values.add(value)
        await RisingEdge(dut.clk)
        
        # Search for a random value
        search_value = random.randint(1, 100)
        dut._log.info(f"Searching for value: {search_value}")
        dut.data.value = search_value
        dut.search.value = 1
        await RisingEdge(dut.clk)
        dut.search.value = 0
        
        while not dut.search_done.value:
            await RisingEdge(dut.clk)
        
        # Check if found matches our expectation
        expected_found = search_value in inserted_values
        actual_found = bool(dut.found.value)
        assert actual_found == expected_found, f"Search mismatch for {search_value}: expected {expected_found}, got {actual_found}"
        
        await RisingEdge(dut.clk)
