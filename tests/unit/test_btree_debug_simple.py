import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def test_debug_states(dut):
    """Debug test to trace state machine behavior."""
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
    
    dut._log.info(f"After reset: insert_state={dut.insert_state.value}")
    
    # Try a simple insert
    dut.data.value = 42
    dut.insert.value = 1
    dut._log.info(f"Starting insert: data=42, insert=1")
    await RisingEdge(dut.clk)
    dut.insert.value = 0
    
    # Monitor insert state machine
    for cycle in range(10):
        state = dut.insert_state.value
        addr = dut.current_addr.value
        done = dut.insert_done.value
        collision = dut.insert_collision.value
        write_en = dut.write_enable.value
        
        dut._log.info(f"Cycle {cycle}: state={state}, addr={addr}, done={done}, collision={collision}, write_en={write_en}")
        
        if done:
            dut._log.info(f"Insert completed with collision={collision}")
            break
            
        await RisingEdge(dut.clk)
    
    await RisingEdge(dut.clk)  # Let done signal clear
    
    # Now try search
    dut.data.value = 42
    dut.search.value = 1
    dut._log.info(f"Starting search: data=42, search=1")
    await RisingEdge(dut.clk)
    dut.search.value = 0
    
    # Monitor search state machine  
    for cycle in range(10):
        state = dut.search_state.value
        addr = dut.search_addr.value
        done = dut.search_done.value
        found = dut.found.value
        
        dut._log.info(f"Search cycle {cycle}: state={state}, addr={addr}, done={done}, found={found}")
        
        if done:
            dut._log.info(f"Search completed with found={found}")
            break
            
        await RisingEdge(dut.clk)
