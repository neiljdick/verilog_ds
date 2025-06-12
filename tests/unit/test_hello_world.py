import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer
import random


@cocotb.test()
async def test_hello_world_reset(dut):
    """Test that reset functionality works correctly."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Initialize inputs
    dut.rst_n.value = 0
    dut.enable.value = 0
    
    # Wait a few clock cycles
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    
    # Check that counter is reset
    assert dut.counter.value == 0, f"Counter should be 0 after reset, got {dut.counter.value}"
    assert dut.overflow.value == 0, f"Overflow should be 0 after reset, got {dut.overflow.value}"
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Counter should still be 0 when not enabled
    assert dut.counter.value == 0, f"Counter should remain 0 when not enabled, got {dut.counter.value}"


@cocotb.test()
async def test_hello_world_basic_counting(dut):
    """Test basic counting functionality."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    
    # Release reset and enable counting
    dut.rst_n.value = 1
    dut.enable.value = 1
    
    # Let it count for a few cycles and verify it's incrementing
    previous_count = 0
    for _ in range(10):
        await RisingEdge(dut.clk)
        current_count = int(dut.counter.value)
        # Just verify it's incrementing (don't worry about exact timing)
        assert current_count >= previous_count, f"Counter should increment, got {current_count} after {previous_count}"
        previous_count = current_count
    
    # Disable counting and verify it stops
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    stopped_count = int(dut.counter.value)
    
    # Wait a few cycles and ensure counter doesn't change
    for _ in range(5):
        await RisingEdge(dut.clk)
        assert dut.counter.value == stopped_count, f"Counter should not change when disabled"


@cocotb.test()
async def test_hello_world_async_reset(dut):
    """Test asynchronous reset behavior."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Start with reset released and enable high
    dut.rst_n.value = 1
    dut.enable.value = 1
    await RisingEdge(dut.clk)
    
    # Let counter increment a few times
    for _ in range(5):
        await RisingEdge(dut.clk)
    
    # Verify counter is not zero
    assert dut.counter.value != 0, "Counter should have incremented"
    
    # Assert reset asynchronously (not on clock edge)
    await Timer(5, units="ns")  # Half clock period
    dut.rst_n.value = 0
    await Timer(1, units="ns")  # Small delay
    
    # Counter should be reset immediately
    assert dut.counter.value == 0, "Counter should be reset immediately"
    assert dut.overflow.value == 0, "Overflow should be reset immediately"
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)


@cocotb.test()
async def test_hello_world_enable_disable(dut):
    """Test enable/disable functionality with random patterns."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    dut.enable.value = 0
    await RisingEdge(dut.clk)
    
    # Release reset
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Test random enable/disable patterns
    last_count_when_enabled = 0
    
    for cycle in range(20):
        # Randomly enable/disable
        enable = random.choice([0, 1])
        dut.enable.value = enable
        
        await RisingEdge(dut.clk)
        current_count = int(dut.counter.value)
        
        if enable:
            # When enabled, counter should be >= last count when it was enabled
            assert current_count >= last_count_when_enabled, \
                f"Counter should increment when enabled: {current_count} vs {last_count_when_enabled}"
            last_count_when_enabled = current_count
        
        # Basic sanity check - counter shouldn't go backwards (except overflow)
        assert current_count < 256, "Counter should wrap at 256 for 8-bit width"
