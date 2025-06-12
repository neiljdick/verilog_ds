import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def test_btree_reset(dut):
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
    
    # Root node validity is internal - we'll test behavior instead


@cocotb.test()
async def test_btree_single_insert(dut):
    """Test inserting a single element."""
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
    dut._log.info("Inserting value 42")
    dut.data.value = 42
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    # Wait for insert to complete
    while not dut.insert_done.value:
        dut._log.info(f"Insert state: {dut.insert_state.value}, addr: {dut.current_addr.value}")
        await RisingEdge(dut.clk)
    
    # Check insert completed successfully without collision
    assert dut.insert_done.value == 1, "Insert should be done"
    assert dut.insert_collision.value == 0, "First insert should not have collision"
    
    await RisingEdge(dut.clk)  # insert_done goes low after one cycle
    
    # We can't directly check memory, but we can verify behavior through search


@cocotb.test()
async def test_btree_insert_and_search(dut):
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
    
    assert dut.insert_collision.value == 0, "First insert should not have collision"
    await RisingEdge(dut.clk)
    
    # Search for the inserted value
    dut._log.info("Searching for value 42")
    dut.data.value = 42
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    # Wait for search to complete
    while not dut.search_done.value:
        dut._log.info(f"Search state: {dut.search_state.value}, addr: {dut.search_addr.value}")
        await RisingEdge(dut.clk)
    
    # Check search found the value
    assert dut.search_done.value == 1, "Search should be done"
    assert dut.found.value == 1, "Should find the inserted value"
    
    await RisingEdge(dut.clk)
    
    # Search for a value that wasn't inserted
    dut._log.info("Searching for value 99")
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
async def test_btree_collision(dut):
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
    
    assert dut.insert_collision.value == 0, "First insert should not have collision"
    await RisingEdge(dut.clk)
    
    # Try to insert the same value again
    dut._log.info("Inserting duplicate value 123")
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
async def test_btree_multiple_values(dut):
    """Test inserting multiple values to build a tree."""
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
    
    # Insert values in order: 50, 25, 75
    # This should create: 50 at root, 25 at left child, 75 at right child
    values = [50, 25, 75]
    
    for value in values:
        dut._log.info(f"Inserting value: {value}")
        dut.data.value = value
        dut.insert.value = 1
        await RisingEdge(dut.clk)
        dut.insert.value = 0
        
        # Wait for insert to complete
        while not dut.insert_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.insert_collision.value == 0, f"Insert of {value} should not have collision"
        await RisingEdge(dut.clk)
    
    # Tree structure is internal - we'll verify through search behavior
    
    # Search for all inserted values
    for value in values:
        dut._log.info(f"Searching for value: {value}")
        dut.data.value = value
        dut.search.value = 1
        await RisingEdge(dut.clk)
        dut.search.value = 0
        
        while not dut.search_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.found.value == 1, f"Should find inserted value {value}"
        await RisingEdge(dut.clk)
    
    # Search for value not in tree
    dut.data.value = 100
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    while not dut.search_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.found.value == 0, "Should not find value 100"
