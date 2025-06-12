// Cuckoo hash table implementation
// Uses two hash tables with different hash functions for O(1) worst-case lookup
// Each key can be stored in one of two possible locations

module cuckoo_hash #(
    parameter KEY_WIDTH = 32,
    parameter VALUE_WIDTH = 32,
    parameter TABLE_SIZE = 64,       // Size of each hash table (power of 2)
    parameter ADDR_WIDTH = $clog2(TABLE_SIZE),
    parameter MAX_EVICTIONS = 8      // Maximum eviction chain length
)(
    input logic clk,
    input logic rst_n,
    
    // Lookup interface
    input logic [KEY_WIDTH-1:0] lookup_key,
    input logic lookup_valid,
    output logic lookup_found,
    output logic [VALUE_WIDTH-1:0] lookup_value,
    output logic lookup_done,
    
    // Insert interface
    input logic [KEY_WIDTH-1:0] insert_key,
    input logic [VALUE_WIDTH-1:0] insert_value,
    input logic insert_valid,
    output logic insert_done,
    output logic insert_success,
    output logic insert_collision,   // Key already exists
    output logic insert_overflow,    // Table is full/max evictions exceeded
    
    // Delete interface
    input logic [KEY_WIDTH-1:0] delete_key,
    input logic delete_valid,
    output logic delete_done,
    output logic delete_found,
    
    // Status interface
    output logic [ADDR_WIDTH:0] occupancy,  // Number of occupied slots
    output logic table_full
);

    // Hash table entries
    typedef struct packed {
        logic valid;
        logic [KEY_WIDTH-1:0] key;
        logic [VALUE_WIDTH-1:0] value;
    } hash_entry_t;
    
    // Two hash tables for cuckoo hashing
    hash_entry_t table0 [TABLE_SIZE-1:0];
    hash_entry_t table1 [TABLE_SIZE-1:0];
    
    // State machine enumerations
    typedef enum logic [2:0] {
        IDLE = 3'b000,
        LOOKUP = 3'b001,
        INSERT = 3'b010,
        EVICT = 3'b011,
        DELETE = 3'b100
    } state_t;
    
    typedef enum logic [1:0] {
        EVICT_IDLE = 2'b00,
        EVICT_FIND = 2'b01,
        EVICT_MOVE = 2'b10,
        EVICT_DONE = 2'b11
    } evict_state_t;
    
    // State registers
    state_t current_state, next_state;
    evict_state_t evict_state, evict_state_next;
    
    // Internal registers
    logic [KEY_WIDTH-1:0] current_key, current_key_next;
    logic [VALUE_WIDTH-1:0] current_value, current_value_next;
    logic [ADDR_WIDTH-1:0] hash0_addr, hash0_addr_next;
    logic [ADDR_WIDTH-1:0] hash1_addr, hash1_addr_next;
    logic [$clog2(MAX_EVICTIONS+1)-1:0] evict_count, evict_count_next;
    logic [ADDR_WIDTH:0] slot_count, slot_count_next;
    
    // Memory write control
    logic write_table0, write_table0_next;
    logic write_table1, write_table1_next;
    logic [ADDR_WIDTH-1:0] write_addr, write_addr_next;
    logic [KEY_WIDTH-1:0] write_key, write_key_next;
    logic [VALUE_WIDTH-1:0] write_value, write_value_next;
    logic write_valid, write_valid_next;
    logic write_delete, write_delete_next;  // Flag to indicate this is a delete operation
    
    // Eviction tracking
    logic [KEY_WIDTH-1:0] evict_key, evict_key_next;
    logic [VALUE_WIDTH-1:0] evict_value, evict_value_next;
    logic [ADDR_WIDTH-1:0] evict_hash0, evict_hash0_next;
    logic [ADDR_WIDTH-1:0] evict_hash1, evict_hash1_next;
    logic evict_try_table1, evict_try_table1_next;  // Which table to try for evicted item
    
    // Operation tracking
    logic lookup_result, lookup_result_next;
    logic [VALUE_WIDTH-1:0] lookup_data, lookup_data_next;
    logic lookup_done_flag, lookup_done_flag_next;
    logic insert_result, insert_result_next;
    logic insert_collision_flag, insert_collision_flag_next;
    logic insert_overflow_flag, insert_overflow_flag_next;
    logic insert_done_flag, insert_done_flag_next;
    logic delete_result, delete_result_next;
    logic delete_done_flag, delete_done_flag_next;
    
    // Memory read data
    /* verilator lint_off UNUSEDSIGNAL */
    hash_entry_t table0_data, table1_data;
    assign table0_data = table0[hash0_addr];
    assign table1_data = table1[hash1_addr];
    /* verilator lint_on UNUSEDSIGNAL */
    
    // Temporary variables for eviction logic
    logic [KEY_WIDTH-1:0] next_evict_key;
    logic [VALUE_WIDTH-1:0] next_evict_value;
    
    // Hash function implementations
    function automatic logic [ADDR_WIDTH-1:0] hash_func0(logic [KEY_WIDTH-1:0] key);
        // Simple hash function 0 - XOR folding
        logic [ADDR_WIDTH-1:0] result;
        /* verilator lint_off WIDTHEXPAND */
        /* verilator lint_off WIDTHTRUNC */
        result = key[ADDR_WIDTH-1:0];
        if (KEY_WIDTH > ADDR_WIDTH) begin
            result = result ^ key[2*ADDR_WIDTH-1:ADDR_WIDTH];
        end
        if (KEY_WIDTH > 2*ADDR_WIDTH) begin
            result = result ^ key[3*ADDR_WIDTH-1:2*ADDR_WIDTH];
        end
        if (KEY_WIDTH > 3*ADDR_WIDTH) begin
            result = result ^ key[KEY_WIDTH-1:3*ADDR_WIDTH];
        end
        /* verilator lint_on WIDTHTRUNC */
        /* verilator lint_on WIDTHEXPAND */
        return result;
    endfunction
    
    function automatic logic [ADDR_WIDTH-1:0] hash_func1(logic [KEY_WIDTH-1:0] key);
        // Simple hash function 1 - Different XOR pattern with shift
        logic [ADDR_WIDTH-1:0] result;
        logic [KEY_WIDTH-1:0] shifted_key;
        /* verilator lint_off WIDTHEXPAND */
        /* verilator lint_off WIDTHTRUNC */
        
        // Rotate key by ADDR_WIDTH/2 positions
        shifted_key = {key[KEY_WIDTH-ADDR_WIDTH/2-1:0], key[KEY_WIDTH-1:KEY_WIDTH-ADDR_WIDTH/2]};
        
        result = shifted_key[ADDR_WIDTH-1:0];
        if (KEY_WIDTH > ADDR_WIDTH) begin
            result = result ^ shifted_key[2*ADDR_WIDTH-1:ADDR_WIDTH];
        end
        if (KEY_WIDTH > 2*ADDR_WIDTH) begin
            result = result ^ shifted_key[3*ADDR_WIDTH-1:2*ADDR_WIDTH];
        end
        if (KEY_WIDTH > 3*ADDR_WIDTH) begin
            result = result ^ shifted_key[KEY_WIDTH-1:3*ADDR_WIDTH];
        end
        
        /* verilator lint_on WIDTHTRUNC */
        /* verilator lint_on WIDTHEXPAND */
        return result;
    endfunction
    
    // State machine sequential logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            current_state <= IDLE;
            evict_state <= EVICT_IDLE;
            current_key <= '0;
            current_value <= '0;
            hash0_addr <= '0;
            hash1_addr <= '0;
            evict_count <= '0;
            slot_count <= '0;
            lookup_result <= 1'b0;
            lookup_data <= '0;
            lookup_done_flag <= 1'b0;
            insert_result <= 1'b0;
            insert_collision_flag <= 1'b0;
            insert_overflow_flag <= 1'b0;
            insert_done_flag <= 1'b0;
            delete_result <= 1'b0;
            delete_done_flag <= 1'b0;
            write_table0 <= 1'b0;
            write_table1 <= 1'b0;
            write_addr <= '0;
            write_key <= '0;
            write_value <= '0;
            write_valid <= 1'b0;
            write_delete <= 1'b0;
            evict_key <= '0;
            evict_value <= '0;
            evict_hash0 <= '0;
            evict_hash1 <= '0;
            evict_try_table1 <= 1'b0;
            
            // Initialize hash tables
            for (int i = 0; i < TABLE_SIZE; i++) begin
                table0[i].valid <= 1'b0;
                table0[i].key <= '0;
                table0[i].value <= '0;
                table1[i].valid <= 1'b0;
                table1[i].key <= '0;
                table1[i].value <= '0;
            end
        end else begin
            current_state <= next_state;
            evict_state <= evict_state_next;
            current_key <= current_key_next;
            current_value <= current_value_next;
            hash0_addr <= hash0_addr_next;
            hash1_addr <= hash1_addr_next;
            evict_count <= evict_count_next;
            slot_count <= slot_count_next;
            lookup_result <= lookup_result_next;
            lookup_data <= lookup_data_next;
            lookup_done_flag <= lookup_done_flag_next;
            insert_result <= insert_result_next;
            insert_collision_flag <= insert_collision_flag_next;
            insert_overflow_flag <= insert_overflow_flag_next;
            insert_done_flag <= insert_done_flag_next;
            delete_result <= delete_result_next;
            delete_done_flag <= delete_done_flag_next;
            write_table0 <= write_table0_next;
            write_table1 <= write_table1_next;
            write_addr <= write_addr_next;
            write_key <= write_key_next;
            write_value <= write_value_next;
            write_valid <= write_valid_next;
            write_delete <= write_delete_next;
            evict_key <= evict_key_next;
            evict_value <= evict_value_next;
            evict_hash0 <= evict_hash0_next;
            evict_hash1 <= evict_hash1_next;
            evict_try_table1 <= evict_try_table1_next;
            
            // Memory write operations
            if (write_valid) begin
                if (write_table0) begin
                    if (write_delete) begin
                        // Delete operation - clear valid bit
                        table0[write_addr].valid <= 1'b0;
                        table0[write_addr].key <= '0;
                        table0[write_addr].value <= '0;
                    end else begin
                        // Insert operation - set valid bit and data
                        table0[write_addr].valid <= 1'b1;
                        table0[write_addr].key <= write_key;
                        table0[write_addr].value <= write_value;
                    end
                end else if (write_table1) begin
                    if (write_delete) begin
                        // Delete operation - clear valid bit
                        table1[write_addr].valid <= 1'b0;
                        table1[write_addr].key <= '0;
                        table1[write_addr].value <= '0;
                    end else begin
                        // Insert operation - set valid bit and data
                        table1[write_addr].valid <= 1'b1;
                        table1[write_addr].key <= write_key;
                        table1[write_addr].value <= write_value;
                    end
                end
            end
        end
    end
    
    // Main state machine combinatorial logic
    always_comb begin
        // Default assignments
        next_state = current_state;
        current_key_next = current_key;
        current_value_next = current_value;
        hash0_addr_next = hash0_addr;
        hash1_addr_next = hash1_addr;
        evict_count_next = evict_count;
        slot_count_next = slot_count;
        lookup_result_next = lookup_result;
        lookup_data_next = lookup_data;
        lookup_done_flag_next = 1'b0;  // Default: clear done flag
        insert_result_next = insert_result;
        insert_collision_flag_next = insert_collision_flag;
        insert_overflow_flag_next = insert_overflow_flag;
        insert_done_flag_next = 1'b0;  // Default: clear done flag
        delete_result_next = delete_result;
        delete_done_flag_next = 1'b0;  // Default: clear done flag
        write_table0_next = 1'b0;
        write_table1_next = 1'b0;
        write_addr_next = write_addr;
        write_key_next = write_key;
        write_value_next = write_value;
        write_valid_next = 1'b0;
        write_delete_next = 1'b0;
        evict_key_next = evict_key;
        evict_value_next = evict_value;
        evict_hash0_next = evict_hash0;
        evict_hash1_next = evict_hash1;
        evict_try_table1_next = evict_try_table1;
        next_evict_key = '0;
        next_evict_value = '0;
        
        case (current_state)
            IDLE: begin
                // Clear previous operation results
                lookup_result_next = 1'b0;
                insert_result_next = 1'b0;
                insert_collision_flag_next = 1'b0;
                insert_overflow_flag_next = 1'b0;
                delete_result_next = 1'b0;
                
                // Handle new operations
                if (lookup_valid) begin
                    next_state = LOOKUP;
                    current_key_next = lookup_key;
                    hash0_addr_next = hash_func0(lookup_key);
                    hash1_addr_next = hash_func1(lookup_key);
                end else if (insert_valid) begin
                    next_state = INSERT;
                    current_key_next = insert_key;
                    current_value_next = insert_value;
                    hash0_addr_next = hash_func0(insert_key);
                    hash1_addr_next = hash_func1(insert_key);
                    evict_count_next = '0;
                end else if (delete_valid) begin
                    next_state = DELETE;
                    current_key_next = delete_key;
                    hash0_addr_next = hash_func0(delete_key);
                    hash1_addr_next = hash_func1(delete_key);
                end
            end
            
            LOOKUP: begin
                // Check both hash tables for the key
                // Check table0 first
                if (table0_data.valid && table0_data.key == current_key) begin
                    // Found in table0
                    lookup_result_next = 1'b1;
                    lookup_data_next = table0_data.value;
                end else if (table1_data.valid && table1_data.key == current_key) begin
                    // Found in table1
                    lookup_result_next = 1'b1;
                    lookup_data_next = table1_data.value;
                end else begin
                    // Not found in either table
                    lookup_result_next = 1'b0;
                    lookup_data_next = '0;
                end
                
                next_state = IDLE;
                lookup_done_flag_next = 1'b1;  // Signal completion
            end
            
            INSERT: begin
                // Check if key already exists (collision detection)
                if ((table0_data.valid && table0_data.key == current_key) ||
                    (table1_data.valid && table1_data.key == current_key)) begin
                    // Key already exists - collision
                    insert_result_next = 1'b0;
                    insert_collision_flag_next = 1'b1;
                    insert_done_flag_next = 1'b1;
                    next_state = IDLE;
                end else if (!table0_data.valid) begin
                    // Slot in table0 is empty - insert here
                    insert_result_next = 1'b1;
                    insert_done_flag_next = 1'b1;
                    slot_count_next = slot_count + 1;
                    next_state = IDLE;
                    // Set up memory write
                    write_table0_next = 1'b1;
                    write_addr_next = hash0_addr;
                    write_key_next = current_key;
                    write_value_next = current_value;
                    write_valid_next = 1'b1;
                end else if (!table1_data.valid) begin
                    // Slot in table1 is empty - insert here
                    insert_result_next = 1'b1;
                    insert_done_flag_next = 1'b1;
                    slot_count_next = slot_count + 1;
                    next_state = IDLE;
                    // Set up memory write
                    write_table1_next = 1'b1;
                    write_addr_next = hash1_addr;
                    write_key_next = current_key;
                    write_value_next = current_value;
                    write_valid_next = 1'b1;
                end else begin
                    // Both slots occupied - need eviction
                    if (evict_count >= MAX_EVICTIONS) begin
                        // Max evictions exceeded - overflow
                        insert_result_next = 1'b0;
                        insert_overflow_flag_next = 1'b1;
                        insert_done_flag_next = 1'b1;
                        next_state = IDLE;
                    end else begin
                        // Start eviction process - evict from table0 first
                        evict_key_next = table0_data.key;
                        evict_value_next = table0_data.value;
                        evict_hash0_next = hash_func0(table0_data.key);
                        evict_hash1_next = hash_func1(table0_data.key);
                        evict_try_table1_next = 1'b1;  // Try placing evicted item in table1
                        
                        // Place new item in table0
                        write_table0_next = 1'b1;
                        write_addr_next = hash0_addr;
                        write_key_next = current_key;
                        write_value_next = current_value;
                        write_valid_next = 1'b1;
                        
                        next_state = EVICT;
                        evict_count_next = evict_count + 1;
                    end
                end
            end
            
            EVICT: begin
                // Try to place the evicted item in its alternate location
                if (evict_try_table1) begin
                    // Check if table1 slot is available for evicted item
                    if (!table1[evict_hash1].valid) begin
                        // Success - place evicted item in table1
                        write_table1_next = 1'b1;
                        write_addr_next = evict_hash1;
                        write_key_next = evict_key;
                        write_value_next = evict_value;
                        write_valid_next = 1'b1;
                        
                        insert_result_next = 1'b1;
                        insert_done_flag_next = 1'b1;
                        slot_count_next = slot_count + 1;
                        next_state = IDLE;
                    end else begin
                        // Table1 slot occupied - need to evict again
                        if (evict_count >= MAX_EVICTIONS) begin
                            // Max evictions reached - overflow
                            insert_result_next = 1'b0;
                            insert_overflow_flag_next = 1'b1;
                            insert_done_flag_next = 1'b1;
                            next_state = IDLE;
                        end else begin
                            // Continue eviction chain
                            next_evict_key = table1[evict_hash1].key;
                            next_evict_value = table1[evict_hash1].value;
                            
                            // Place current evicted item in table1
                            write_table1_next = 1'b1;
                            write_addr_next = evict_hash1;
                            write_key_next = evict_key;
                            write_value_next = evict_value;
                            write_valid_next = 1'b1;
                            
                            // Set up next eviction (newly evicted item tries table0)
                            evict_key_next = next_evict_key;
                            evict_value_next = next_evict_value;
                            evict_hash0_next = hash_func0(next_evict_key);
                            evict_hash1_next = hash_func1(next_evict_key);
                            evict_try_table1_next = 1'b0;  // Try table0 next
                            
                            evict_count_next = evict_count + 1;
                            // Stay in EVICT state
                        end
                    end
                end else begin
                    // Try to place evicted item in table0
                    if (!table0[evict_hash0].valid) begin
                        // Success - place evicted item in table0
                        write_table0_next = 1'b1;
                        write_addr_next = evict_hash0;
                        write_key_next = evict_key;
                        write_value_next = evict_value;
                        write_valid_next = 1'b1;
                        
                        insert_result_next = 1'b1;
                        insert_done_flag_next = 1'b1;
                        slot_count_next = slot_count + 1;
                        next_state = IDLE;
                    end else begin
                        // Table0 slot occupied - need to evict again
                        if (evict_count >= MAX_EVICTIONS) begin
                            // Max evictions reached - overflow
                            insert_result_next = 1'b0;
                            insert_overflow_flag_next = 1'b1;
                            insert_done_flag_next = 1'b1;
                            next_state = IDLE;
                        end else begin
                            // Continue eviction chain
                            next_evict_key = table0[evict_hash0].key;
                            next_evict_value = table0[evict_hash0].value;
                            
                            // Place current evicted item in table0
                            write_table0_next = 1'b1;
                            write_addr_next = evict_hash0;
                            write_key_next = evict_key;
                            write_value_next = evict_value;
                            write_valid_next = 1'b1;
                            
                            // Set up next eviction (newly evicted item tries table1)
                            evict_key_next = next_evict_key;
                            evict_value_next = next_evict_value;
                            evict_hash0_next = hash_func0(next_evict_key);
                            evict_hash1_next = hash_func1(next_evict_key);
                            evict_try_table1_next = 1'b1;  // Try table1 next
                            
                            evict_count_next = evict_count + 1;
                            // Stay in EVICT state
                        end
                    end
                end
            end
            
            DELETE: begin
                // Check both hash tables for the key to delete
                if (table0_data.valid && table0_data.key == current_key) begin
                    // Found in table0 - mark as invalid
                    write_table0_next = 1'b1;
                    write_addr_next = hash0_addr;
                    write_key_next = '0;  // Clear key (optional)
                    write_value_next = '0;  // Clear value (optional)
                    write_valid_next = 1'b1;
                    write_delete_next = 1'b1;  // Indicate this is a delete operation
                    
                    delete_result_next = 1'b1;
                    delete_done_flag_next = 1'b1;
                    slot_count_next = slot_count - 1;
                    next_state = IDLE;
                end else if (table1_data.valid && table1_data.key == current_key) begin
                    // Found in table1 - mark as invalid
                    write_table1_next = 1'b1;
                    write_addr_next = hash1_addr;
                    write_key_next = '0;  // Clear key (optional)
                    write_value_next = '0;  // Clear value (optional)
                    write_valid_next = 1'b1;
                    write_delete_next = 1'b1;  // Indicate this is a delete operation
                    
                    delete_result_next = 1'b1;
                    delete_done_flag_next = 1'b1;
                    slot_count_next = slot_count - 1;
                    next_state = IDLE;
                end else begin
                    // Key not found in either table
                    delete_result_next = 1'b0;
                    delete_done_flag_next = 1'b1;
                    next_state = IDLE;
                end
            end
            
            default: begin
                next_state = IDLE;
            end
        endcase
    end
    
    // Eviction state machine combinatorial logic
    always_comb begin
        evict_state_next = evict_state;
        
        case (evict_state)
            EVICT_IDLE: begin
                // Wait for eviction to be triggered
            end
            
            EVICT_FIND: begin
                // TODO: Find which item to evict and where to place it
                evict_state_next = EVICT_MOVE;
            end
            
            EVICT_MOVE: begin
                // TODO: Perform the eviction and move
                evict_state_next = EVICT_DONE;
            end
            
            EVICT_DONE: begin
                evict_state_next = EVICT_IDLE;
            end
            
            default: begin
                evict_state_next = EVICT_IDLE;
            end
        endcase
    end
    
    // Output assignments
    assign lookup_found = lookup_done && lookup_result;
    assign lookup_value = lookup_data;
    assign lookup_done = lookup_done_flag;
    
    assign insert_done = insert_done_flag;
    assign insert_success = insert_done && insert_result;
    assign insert_collision = insert_done && insert_collision_flag;
    assign insert_overflow = insert_done && insert_overflow_flag;
    
    assign delete_done = delete_done_flag;
    assign delete_found = delete_done && delete_result;
    
    assign occupancy = slot_count;
    assign table_full = (slot_count >= (2 * TABLE_SIZE));
    
    // Assertions for verification
    /* verilator lint_off SYNCASYNCNET */
    /* verilator lint_off WIDTHEXPAND */
    assert property (@(posedge clk) disable iff (!rst_n)
        !(lookup_valid && insert_valid))
    else $error("Simultaneous lookup and insert operations not supported");
    
    assert property (@(posedge clk) disable iff (!rst_n)
        !(lookup_valid && delete_valid))
    else $error("Simultaneous lookup and delete operations not supported");
    
    assert property (@(posedge clk) disable iff (!rst_n)
        !(insert_valid && delete_valid))
    else $error("Simultaneous insert and delete operations not supported");
    
    assert property (@(posedge clk) disable iff (!rst_n)
        slot_count <= (2 * TABLE_SIZE))
    else $error("Occupancy counter exceeded table capacity");
    /* verilator lint_on WIDTHEXPAND */
    /* verilator lint_on SYNCASYNCNET */

endmodule
