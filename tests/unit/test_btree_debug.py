import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def test_btree_debug_simple(dut):
    """Debug test to understand what's happening with insert/search."""
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
    
    dut._log.info(f"After reset: insert_state={dut.insert_state.value}, search_state={dut.search_state.value}")
    
    # Insert value 42
    dut._log.info("Starting insert of 42")
    dut.data.value = 42
    dut.insert.value = 1
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    # Monitor states during insert
    cycle = 0
    while not dut.insert_done.value and cycle < 10:
        dut._log.info(f"Insert cycle {cycle}: state={dut.insert_state.value}, addr={dut.current_addr.value}, done={dut.insert_done.value}")
        await RisingEdge(dut.clk)
        cycle += 1
    
    if dut.insert_done.value:
        dut._log.info(f"Insert completed: collision={dut.insert_collision.value}")
    else:
        dut._log.error("Insert did not complete in 10 cycles")
    
    await RisingEdge(dut.clk)  # Let insert_done go low
    
    # Check memory state
    dut._log.info(f"Root node valid: {dut.ram[0].valid.value}, data: {dut.ram[0].data.value}")
    
    # Now search for 42
    dut._log.info("Starting search for 42")
    dut.data.value = 42
    dut.search.value = 1
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    # Monitor states during search
    cycle = 0
    while not dut.search_done.value and cycle < 10:
        dut._log.info(f"Search cycle {cycle}: state={dut.search_state.value}, addr={dut.search_addr.value}, done={dut.search_done.value}")
        await RisingEdge(dut.clk)
        cycle += 1
    
    if dut.search_done.value:
        dut._log.info(f"Search completed: found={dut.found.value}")
    else:
        dut._log.error("Search did not complete in 10 cycles")
