import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge


@cocotb.test()
async def test_basic_delete(dut):
    """Test basic delete functionality."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    test_key = 0x12345678
    test_value = 0xABCDEF01
    
    # First insert a key
    dut._log.info(f"Inserting key {hex(test_key)} with value {hex(test_value)}")
    dut.insert_key.value = test_key
    dut.insert_value.value = test_value
    dut.insert_valid.value = 1
    await RisingEdge(dut.clk)
    dut.insert_valid.value = 0
    
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.insert_success.value == 1, "Insert should succeed"
    assert int(dut.occupancy.value) == 1, "Occupancy should be 1 after insert"
    
    await RisingEdge(dut.clk)
    
    # Verify key can be found
    dut.lookup_key.value = test_key
    dut.lookup_valid.value = 1
    await RisingEdge(dut.clk)
    dut.lookup_valid.value = 0
    
    while not dut.lookup_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.lookup_found.value == 1, "Should find key before deletion"
    await RisingEdge(dut.clk)
    
    # Now delete the key
    dut._log.info(f"Deleting key {hex(test_key)}")
    dut.delete_key.value = test_key
    dut.delete_valid.value = 1
    await RisingEdge(dut.clk)
    dut.delete_valid.value = 0
    
    while not dut.delete_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.delete_done.value == 1, "Delete should be done"
    assert dut.delete_found.value == 1, "Should find and delete the key"
    assert int(dut.occupancy.value) == 0, "Occupancy should be 0 after delete"
    
    await RisingEdge(dut.clk)
    
    # Verify key can no longer be found
    dut.lookup_key.value = test_key
    dut.lookup_valid.value = 1
    await RisingEdge(dut.clk)
    dut.lookup_valid.value = 0
    
    while not dut.lookup_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.lookup_found.value == 0, "Should not find key after deletion"
    
    dut._log.info("Basic delete test completed successfully")


@cocotb.test()
async def test_delete_nonexistent_key(dut):
    """Test deleting a key that doesn't exist."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Try to delete a key from empty table
    test_key = 0x87654321
    
    dut._log.info(f"Attempting to delete nonexistent key {hex(test_key)}")
    dut.delete_key.value = test_key
    dut.delete_valid.value = 1
    await RisingEdge(dut.clk)
    dut.delete_valid.value = 0
    
    while not dut.delete_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.delete_done.value == 1, "Delete should complete"
    assert dut.delete_found.value == 0, "Should not find nonexistent key"
    assert int(dut.occupancy.value) == 0, "Occupancy should remain 0"
    
    dut._log.info("Delete nonexistent key test completed successfully")


@cocotb.test()
async def test_insert_delete_insert_sequence(dut):
    """Test inserting, deleting, then inserting again."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    test_key = 0xDEADBEEF
    test_value1 = 0x11111111
    test_value2 = 0x22222222
    
    # Insert first value
    dut._log.info(f"First insert: key {hex(test_key)} with value {hex(test_value1)}")
    dut.insert_key.value = test_key
    dut.insert_value.value = test_value1
    dut.insert_valid.value = 1
    await RisingEdge(dut.clk)
    dut.insert_valid.value = 0
    
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.insert_success.value == 1, "First insert should succeed"
    assert int(dut.occupancy.value) == 1, "Occupancy should be 1"
    await RisingEdge(dut.clk)
    
    # Delete the key
    dut._log.info(f"Deleting key {hex(test_key)}")
    dut.delete_key.value = test_key
    dut.delete_valid.value = 1
    await RisingEdge(dut.clk)
    dut.delete_valid.value = 0
    
    while not dut.delete_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.delete_found.value == 1, "Should find and delete the key"
    assert int(dut.occupancy.value) == 0, "Occupancy should be 0 after delete"
    await RisingEdge(dut.clk)
    
    # Insert same key with different value
    dut._log.info(f"Second insert: key {hex(test_key)} with value {hex(test_value2)}")
    dut.insert_key.value = test_key
    dut.insert_value.value = test_value2
    dut.insert_valid.value = 1
    await RisingEdge(dut.clk)
    dut.insert_valid.value = 0
    
    while not dut.insert_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.insert_success.value == 1, "Second insert should succeed"
    assert int(dut.occupancy.value) == 1, "Occupancy should be 1 again"
    await RisingEdge(dut.clk)
    
    # Verify lookup returns new value
    dut.lookup_key.value = test_key
    dut.lookup_valid.value = 1
    await RisingEdge(dut.clk)
    dut.lookup_valid.value = 0
    
    while not dut.lookup_done.value:
        await RisingEdge(dut.clk)
    
    assert dut.lookup_found.value == 1, "Should find the re-inserted key"
    assert int(dut.lookup_value.value) == test_value2, f"Should return new value {hex(test_value2)}"
    
    dut._log.info("Insert-delete-insert sequence test completed successfully")


@cocotb.test()
async def test_delete_multiple_keys(dut):
    """Test deleting multiple keys."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Insert multiple keys
    test_pairs = [
        (0x12345678, 0x1000),
        (0x87654321, 0x2000),
        (0xDEADBEEF, 0x3000),
        (0xCAFEBABE, 0x4000)
    ]
    
    inserted_keys = []
    
    # Insert all keys
    for key, value in test_pairs:
        dut._log.info(f"Inserting key {hex(key)} with value {hex(value)}")
        dut.insert_key.value = key
        dut.insert_value.value = value
        dut.insert_valid.value = 1
        await RisingEdge(dut.clk)
        dut.insert_valid.value = 0
        
        while not dut.insert_done.value:
            await RisingEdge(dut.clk)
        
        if dut.insert_success.value == 1:
            inserted_keys.append(key)
        
        await RisingEdge(dut.clk)
    
    initial_occupancy = int(dut.occupancy.value)
    dut._log.info(f"Successfully inserted {len(inserted_keys)} keys, occupancy: {initial_occupancy}")
    
    # Delete half of the keys
    keys_to_delete = inserted_keys[:len(inserted_keys)//2]
    successful_deletes = 0
    
    for key in keys_to_delete:
        dut._log.info(f"Deleting key {hex(key)}")
        dut.delete_key.value = key
        dut.delete_valid.value = 1
        await RisingEdge(dut.clk)
        dut.delete_valid.value = 0
        
        while not dut.delete_done.value:
            await RisingEdge(dut.clk)
        
        if dut.delete_found.value == 1:
            successful_deletes += 1
        
        await RisingEdge(dut.clk)
    
    final_occupancy = int(dut.occupancy.value)
    expected_occupancy = initial_occupancy - successful_deletes
    
    dut._log.info(f"Deleted {successful_deletes} keys")
    dut._log.info(f"Occupancy: {initial_occupancy} -> {final_occupancy} (expected: {expected_occupancy})")
    
    assert final_occupancy == expected_occupancy, f"Occupancy should be {expected_occupancy}, got {final_occupancy}"
    
    # Verify deleted keys can't be found
    for key in keys_to_delete[:successful_deletes]:
        dut.lookup_key.value = key
        dut.lookup_valid.value = 1
        await RisingEdge(dut.clk)
        dut.lookup_valid.value = 0
        
        while not dut.lookup_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.lookup_found.value == 0, f"Should not find deleted key {hex(key)}"
        await RisingEdge(dut.clk)
    
    dut._log.info("Multiple delete test completed successfully")


@cocotb.test()
async def test_delete_from_different_tables(dut):
    """Test deleting keys from both hash tables."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    # Insert keys that will likely be distributed across both tables
    test_keys = [
        0x00000000,  # Hash to (0, 0)
        0xABCDEF01,  # Hash to (41, 12) from earlier tests
        0xFFFFFFFF   # Hash to (16, 1) from earlier tests
    ]
    
    inserted_keys = []
    
    # Insert keys
    for i, key in enumerate(test_keys):
        value = 0x5000 + i
        dut._log.info(f"Inserting key {hex(key)} with value {hex(value)}")
        dut.insert_key.value = key
        dut.insert_value.value = value
        dut.insert_valid.value = 1
        await RisingEdge(dut.clk)
        dut.insert_valid.value = 0
        
        while not dut.insert_done.value:
            await RisingEdge(dut.clk)
        
        if dut.insert_success.value == 1:
            inserted_keys.append(key)
            dut._log.info(f"Successfully inserted key {hex(key)}")
        else:
            dut._log.info(f"Failed to insert key {hex(key)}")
        
        await RisingEdge(dut.clk)
    
    initial_occupancy = int(dut.occupancy.value)
    dut._log.info(f"Initial occupancy: {initial_occupancy}")
    
    # Delete all inserted keys
    for key in inserted_keys:
        dut._log.info(f"Deleting key {hex(key)}")
        dut.delete_key.value = key
        dut.delete_valid.value = 1
        await RisingEdge(dut.clk)
        dut.delete_valid.value = 0
        
        while not dut.delete_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.delete_found.value == 1, f"Should find and delete key {hex(key)}"
        await RisingEdge(dut.clk)
    
    final_occupancy = int(dut.occupancy.value)
    assert final_occupancy == 0, f"Final occupancy should be 0, got {final_occupancy}"
    
    dut._log.info("Delete from different tables test completed successfully")
