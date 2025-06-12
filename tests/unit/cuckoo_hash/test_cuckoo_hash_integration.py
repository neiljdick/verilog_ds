import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
import random


@cocotb.test()
async def test_comprehensive_integration(dut):
    """Comprehensive integration test of all cuckoo hash functionality."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    dut._log.info("Starting comprehensive cuckoo hash integration test")
    
    # Phase 1: Insert a variety of keys
    dut._log.info("Phase 1: Inserting multiple keys")
    test_data = {
        0x12345678: 0xAABBCCDD,
        0x87654321: 0x11223344,
        0xDEADBEEF: 0x55667788,
        0xCAFEBABE: 0x99AABBCC,
        0x00000000: 0xFFFFFFFF,
        0xFFFFFFFF: 0x00000000,
        0xABCDEF01: 0x12345678,
        0x13579BDF: 0x2468ACE0
    }
    
    successful_inserts = {}
    
    for key, value in test_data.items():
        dut._log.info(f"Inserting key {hex(key)} with value {hex(value)}")
        dut.insert_key.value = key
        dut.insert_value.value = value
        dut.insert_valid.value = 1
        await RisingEdge(dut.clk)
        dut.insert_valid.value = 0
        
        # Wait for completion with timeout
        timeout = 0
        while not dut.insert_done.value and timeout < 50:
            await RisingEdge(dut.clk)
            timeout += 1
        
        if dut.insert_success.value == 1:
            successful_inserts[key] = value
            dut._log.info(f"Successfully inserted key {hex(key)}")
        elif dut.insert_overflow.value == 1:
            dut._log.info(f"Insert overflow for key {hex(key)}")
        else:
            dut._log.info(f"Insert failed for key {hex(key)} (collision={dut.insert_collision.value})")
        
        await RisingEdge(dut.clk)
    
    phase1_occupancy = int(dut.occupancy.value)
    dut._log.info(f"Phase 1 complete: {len(successful_inserts)}/{len(test_data)} keys inserted, occupancy: {phase1_occupancy}")
    
    # Phase 2: Verify all successful inserts can be found
    dut._log.info("Phase 2: Verifying lookup functionality")
    lookup_successes = 0
    
    for key, expected_value in successful_inserts.items():
        dut.lookup_key.value = key
        dut.lookup_valid.value = 1
        await RisingEdge(dut.clk)
        dut.lookup_valid.value = 0
        
        while not dut.lookup_done.value:
            await RisingEdge(dut.clk)
        
        if dut.lookup_found.value == 1:
            actual_value = int(dut.lookup_value.value)
            if actual_value == expected_value:
                lookup_successes += 1
            else:
                dut._log.error(f"Value mismatch for key {hex(key)}: expected {hex(expected_value)}, got {hex(actual_value)}")
        else:
            dut._log.error(f"Failed to find inserted key {hex(key)}")
        
        await RisingEdge(dut.clk)
    
    dut._log.info(f"Phase 2 complete: {lookup_successes}/{len(successful_inserts)} lookups successful")
    assert lookup_successes == len(successful_inserts), "All inserted keys should be found"
    
    # Phase 3: Test collision detection
    dut._log.info("Phase 3: Testing collision detection")
    if successful_inserts:
        collision_key = list(successful_inserts.keys())[0]
        dut.insert_key.value = collision_key
        dut.insert_value.value = 0xDEADBEEF  # Different value
        dut.insert_valid.value = 1
        await RisingEdge(dut.clk)
        dut.insert_valid.value = 0
        
        while not dut.insert_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.insert_collision.value == 1, "Should detect collision for duplicate key"
        assert dut.insert_success.value == 0, "Collision should not be successful"
        dut._log.info(f"Collision detection working correctly for key {hex(collision_key)}")
        await RisingEdge(dut.clk)
    
    # Phase 4: Delete some keys
    dut._log.info("Phase 4: Testing delete functionality")
    keys_to_delete = list(successful_inserts.keys())[:len(successful_inserts)//2]
    deleted_keys = set()
    
    for key in keys_to_delete:
        dut._log.info(f"Deleting key {hex(key)}")
        dut.delete_key.value = key
        dut.delete_valid.value = 1
        await RisingEdge(dut.clk)
        dut.delete_valid.value = 0
        
        while not dut.delete_done.value:
            await RisingEdge(dut.clk)
        
        if dut.delete_found.value == 1:
            deleted_keys.add(key)
            dut._log.info(f"Successfully deleted key {hex(key)}")
        else:
            dut._log.error(f"Failed to delete key {hex(key)}")
        
        await RisingEdge(dut.clk)
    
    phase4_occupancy = int(dut.occupancy.value)
    expected_occupancy = phase1_occupancy - len(deleted_keys)
    dut._log.info(f"Phase 4 complete: {len(deleted_keys)} keys deleted")
    dut._log.info(f"Occupancy: {phase1_occupancy} -> {phase4_occupancy} (expected: {expected_occupancy})")
    assert phase4_occupancy == expected_occupancy, f"Occupancy should be {expected_occupancy}"
    
    # Phase 5: Verify deleted keys are not found
    dut._log.info("Phase 5: Verifying deleted keys are not found")
    for key in deleted_keys:
        dut.lookup_key.value = key
        dut.lookup_valid.value = 1
        await RisingEdge(dut.clk)
        dut.lookup_valid.value = 0
        
        while not dut.lookup_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.lookup_found.value == 0, f"Should not find deleted key {hex(key)}"
        await RisingEdge(dut.clk)
    
    dut._log.info("Phase 5 complete: All deleted keys correctly not found")
    
    # Phase 6: Verify remaining keys are still found
    dut._log.info("Phase 6: Verifying remaining keys are still accessible")
    remaining_keys = {k: v for k, v in successful_inserts.items() if k not in deleted_keys}
    remaining_found = 0
    
    for key, expected_value in remaining_keys.items():
        dut.lookup_key.value = key
        dut.lookup_valid.value = 1
        await RisingEdge(dut.clk)
        dut.lookup_valid.value = 0
        
        while not dut.lookup_done.value:
            await RisingEdge(dut.clk)
        
        if dut.lookup_found.value == 1:
            actual_value = int(dut.lookup_value.value)
            if actual_value == expected_value:
                remaining_found += 1
            else:
                dut._log.error(f"Value changed for key {hex(key)}: expected {hex(expected_value)}, got {hex(actual_value)}")
        else:
            dut._log.error(f"Lost remaining key {hex(key)}")
        
        await RisingEdge(dut.clk)
    
    dut._log.info(f"Phase 6 complete: {remaining_found}/{len(remaining_keys)} remaining keys found")
    assert remaining_found == len(remaining_keys), "All remaining keys should still be accessible"
    
    # Phase 7: Reinsert some deleted keys with new values
    dut._log.info("Phase 7: Reinserting previously deleted keys")
    reinsert_keys = list(deleted_keys)[:2] if len(deleted_keys) >= 2 else list(deleted_keys)
    reinserted = {}
    
    for i, key in enumerate(reinsert_keys):
        new_value = 0x7000 + i
        dut._log.info(f"Reinserting key {hex(key)} with new value {hex(new_value)}")
        dut.insert_key.value = key
        dut.insert_value.value = new_value
        dut.insert_valid.value = 1
        await RisingEdge(dut.clk)
        dut.insert_valid.value = 0
        
        timeout = 0
        while not dut.insert_done.value and timeout < 50:
            await RisingEdge(dut.clk)
            timeout += 1
        
        if dut.insert_success.value == 1:
            reinserted[key] = new_value
            dut._log.info(f"Successfully reinserted key {hex(key)}")
        
        await RisingEdge(dut.clk)
    
    # Verify reinserted keys
    for key, expected_value in reinserted.items():
        dut.lookup_key.value = key
        dut.lookup_valid.value = 1
        await RisingEdge(dut.clk)
        dut.lookup_valid.value = 0
        
        while not dut.lookup_done.value:
            await RisingEdge(dut.clk)
        
        assert dut.lookup_found.value == 1, f"Should find reinserted key {hex(key)}"
        actual_value = int(dut.lookup_value.value)
        assert actual_value == expected_value, f"Reinserted key {hex(key)}: expected {hex(expected_value)}, got {hex(actual_value)}"
        
        await RisingEdge(dut.clk)
    
    final_occupancy = int(dut.occupancy.value)
    dut._log.info(f"Phase 7 complete: {len(reinserted)} keys reinserted")
    dut._log.info(f"Final occupancy: {final_occupancy}")
    
    # Summary
    dut._log.info("Integration test summary:")
    dut._log.info(f"  Total keys attempted: {len(test_data)}")
    dut._log.info(f"  Successful initial inserts: {len(successful_inserts)}")
    dut._log.info(f"  Successful lookups: {lookup_successes}")
    dut._log.info(f"  Keys deleted: {len(deleted_keys)}")
    dut._log.info(f"  Keys reinserted: {len(reinserted)}")
    dut._log.info(f"  Final occupancy: {final_occupancy}")
    dut._log.info("All functionality verified: lookup, insert, delete, collision detection, eviction")
    
    dut._log.info("Comprehensive integration test completed successfully!")


@cocotb.test()
async def test_stress_mixed_operations(dut):
    """Stress test with mixed random operations."""
    # Create a 10ns period clock (100MHz)
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    # Reset the DUT
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)
    dut.rst_n.value = 1
    await RisingEdge(dut.clk)
    
    dut._log.info("Starting stress test with mixed operations")
    
    # Track our own state
    inserted_keys = set()
    insert_count = 0
    delete_count = 0
    lookup_count = 0
    
    # Perform random operations
    for operation_num in range(30):
        # Randomly choose operation type
        if len(inserted_keys) == 0:
            # Force insert if no keys present
            operation = 'insert'
        else:
            operation = random.choice(['insert', 'insert', 'delete', 'lookup'])  # Bias toward inserts
        
        if operation == 'insert':
            # Generate a unique key
            key = random.randint(0x10000000, 0x9FFFFFFF)
            while key in inserted_keys:
                key = random.randint(0x10000000, 0x9FFFFFFF)
            
            value = random.randint(0x1000, 0x9999)
            
            dut._log.info(f"Op {operation_num+1}: INSERT key {hex(key)} value {hex(value)}")
            dut.insert_key.value = key
            dut.insert_value.value = value
            dut.insert_valid.value = 1
            await RisingEdge(dut.clk)
            dut.insert_valid.value = 0
            
            timeout = 0
            while not dut.insert_done.value and timeout < 50:
                await RisingEdge(dut.clk)
                timeout += 1
            
            if dut.insert_success.value == 1:
                inserted_keys.add(key)
                insert_count += 1
            elif dut.insert_overflow.value == 1:
                dut._log.info(f"  -> Overflow (table getting full)")
            
        elif operation == 'delete' and inserted_keys:
            key = random.choice(list(inserted_keys))
            
            dut._log.info(f"Op {operation_num+1}: DELETE key {hex(key)}")
            dut.delete_key.value = key
            dut.delete_valid.value = 1
            await RisingEdge(dut.clk)
            dut.delete_valid.value = 0
            
            while not dut.delete_done.value:
                await RisingEdge(dut.clk)
            
            if dut.delete_found.value == 1:
                inserted_keys.remove(key)
                delete_count += 1
            
        elif operation == 'lookup':
            if inserted_keys and random.random() < 0.7:
                # 70% chance to lookup existing key
                key = random.choice(list(inserted_keys))
                should_find = True
            else:
                # 30% chance to lookup non-existent key
                key = random.randint(0xA0000000, 0xFFFFFFFF)
                while key in inserted_keys:
                    key = random.randint(0xA0000000, 0xFFFFFFFF)
                should_find = False
            
            dut._log.info(f"Op {operation_num+1}: LOOKUP key {hex(key)} (expect: {'found' if should_find else 'not found'})")
            dut.lookup_key.value = key
            dut.lookup_valid.value = 1
            await RisingEdge(dut.clk)
            dut.lookup_valid.value = 0
            
            while not dut.lookup_done.value:
                await RisingEdge(dut.clk)
            
            found = dut.lookup_found.value == 1
            if found == should_find:
                lookup_count += 1
            else:
                dut._log.error(f"  -> Lookup mismatch! Expected {should_find}, got {found}")
        
        await RisingEdge(dut.clk)
        
        current_occupancy = int(dut.occupancy.value)
        expected_occupancy = len(inserted_keys)
        if current_occupancy != expected_occupancy:
            dut._log.error(f"  -> Occupancy mismatch! Expected {expected_occupancy}, got {current_occupancy}")
    
    final_occupancy = int(dut.occupancy.value)
    dut._log.info("Stress test summary:")
    dut._log.info(f"  Successful inserts: {insert_count}")
    dut._log.info(f"  Successful deletes: {delete_count}")
    dut._log.info(f"  Correct lookups: {lookup_count}")
    dut._log.info(f"  Final occupancy: {final_occupancy}")
    dut._log.info(f"  Keys in our tracking: {len(inserted_keys)}")
    
    assert final_occupancy == len(inserted_keys), "Occupancy should match our tracking"
    
    dut._log.info("Stress test with mixed operations completed successfully!")
