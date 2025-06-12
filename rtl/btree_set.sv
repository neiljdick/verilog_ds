// A 'set' implemented by a simple binary search tree backed by a contiguous
// block ram. Supports insert and search operations.
// Uses implicit binary heap indexing: left = 2*i+1, right = 2*i+2

module btree_set #(
    parameter DATA_WIDTH = 32,
    parameter DEPTH = 64,
    parameter ADDR_WIDTH = $clog2(DEPTH)
)(
    input logic clk,
    input logic rst_n,
    // data to be operated on
    input logic [DATA_WIDTH-1:0] data,
    // begin the set insertion
    input logic insert,
    // begin a search operation
    input logic search,
    // goes high the same clock as search done, high if set contains this
    // value
    output logic found,
    // goes high the same clock as insert_done, high if set already
    // contains
    output logic insert_collision,
    // goes high when the insertion is done
    output logic insert_done,
    // goes high when the search is done
    output logic search_done
);

    // Memory to store the binary tree nodes
    // Each node contains: [valid][data]
    // Invalid nodes are marked with valid=0
    typedef struct packed {
        logic valid;
        logic [DATA_WIDTH-1:0] data;
    } node_t;
    
    node_t ram [DEPTH-1:0];
    
    // State machine enumerations
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        TRAVERSE = 2'b01,
        COMPLETE = 2'b10
    } insert_state_t;
    
    typedef enum logic [1:0] {
        SEARCH_IDLE = 2'b00,
        SEARCH_TRAVERSE = 2'b01,
        SEARCH_COMPLETE = 2'b10
    } search_state_t;
    
    // State registers
    insert_state_t insert_state, insert_state_next;
    search_state_t search_state, search_state_next;
    
    // Internal registers
    logic [ADDR_WIDTH-1:0] current_addr, current_addr_next;
    logic [ADDR_WIDTH-1:0] search_addr, search_addr_next;
    logic [DATA_WIDTH-1:0] target_data, target_data_next;
    logic [DATA_WIDTH-1:0] search_data, search_data_next;
    
    // Operation tracking
    logic insert_found_collision, insert_found_collision_next;
    logic search_found_match, search_found_match_next;
    logic write_enable;
    
    // Memory read data
    node_t current_node, search_node;
    assign current_node = ram[current_addr];
    assign search_node = ram[search_addr];
    
    // Helper functions for tree navigation
    function automatic logic [ADDR_WIDTH-1:0] left_child(logic [ADDR_WIDTH-1:0] addr);
        return (2 * addr + 1);
    endfunction
    
    function automatic logic [ADDR_WIDTH-1:0] right_child(logic [ADDR_WIDTH-1:0] addr);
        return (2 * addr + 2);
    endfunction
    
    function automatic logic addr_valid(logic [ADDR_WIDTH-1:0] addr);
        /* verilator lint_off WIDTHEXPAND */
        return (addr < DEPTH);
        /* verilator lint_on WIDTHEXPAND */
    endfunction
    
    // State machine sequential logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            insert_state <= IDLE;
            search_state <= SEARCH_IDLE;
            current_addr <= 0;
            search_addr <= 0;
            target_data <= 0;
            search_data <= 0;
            search_found_match <= 1'b0;
            insert_found_collision <= 1'b0;
            
            // Initialize memory - all nodes invalid
            for (int i = 0; i < DEPTH; i++) begin
                ram[i].valid <= 1'b0;
                ram[i].data <= '0;
            end
        end else begin
            insert_state <= insert_state_next;
            search_state <= search_state_next;
            current_addr <= current_addr_next;
            search_addr <= search_addr_next;
            target_data <= target_data_next;
            search_data <= search_data_next;
            search_found_match <= search_found_match_next;
            insert_found_collision <= insert_found_collision_next;
            
            // Handle memory writes during insert
            if (write_enable) begin
                ram[current_addr].valid <= 1'b1;
                ram[current_addr].data <= target_data;
            end
        end
    end
    
    // Insert state machine combinatorial logic
    always_comb begin
        insert_state_next = insert_state;
        current_addr_next = current_addr;
        target_data_next = target_data;
        insert_found_collision_next = insert_found_collision; // Keep current value by default
        write_enable = 1'b0;
        
        case (insert_state)
            IDLE: begin
                if (insert) begin
                    insert_state_next = TRAVERSE;
                    current_addr_next = 0; // Start at root
                    target_data_next = data;
                    insert_found_collision_next = 1'b0; // Clear collision flag at start
                end
            end
            
            TRAVERSE: begin
                if (!current_node.valid) begin
                    // Found empty spot - insert here
                    write_enable = 1'b1;
                    insert_state_next = COMPLETE;
                    // insert_found_collision_next remains 0
                end else if (current_node.data == target_data) begin
                    // Found collision
                    insert_found_collision_next = 1'b1;
                    insert_state_next = COMPLETE;
                end else if (target_data < current_node.data) begin
                    // Go left
                    if (addr_valid(left_child(current_addr))) begin
                        current_addr_next = left_child(current_addr);
                    end else begin
                        // Tree capacity exceeded - can't go left
                        insert_state_next = COMPLETE;
                    end
                end else begin
                    // Go right
                    if (addr_valid(right_child(current_addr))) begin
                        current_addr_next = right_child(current_addr);
                    end else begin
                        // Tree capacity exceeded - can't go right
                        insert_state_next = COMPLETE;
                    end
                end
            end
            
            COMPLETE: begin
                insert_state_next = IDLE;
                // Keep insert_found_collision value during COMPLETE state
            end
            
            default: begin
                insert_state_next = IDLE;
                insert_found_collision_next = 1'b0;
            end
        endcase
    end
    
    // Search state machine combinatorial logic
    always_comb begin
        search_state_next = search_state;
        search_addr_next = search_addr;
        search_data_next = search_data;
        search_found_match_next = search_found_match; // Keep current value by default
        
        case (search_state)
            SEARCH_IDLE: begin
                if (search) begin
                    search_state_next = SEARCH_TRAVERSE;
                    search_addr_next = 0; // Start at root
                    search_data_next = data;
                    search_found_match_next = 1'b0; // Clear found flag at start of new search
                end
            end
            
            SEARCH_TRAVERSE: begin
                if (!search_node.valid) begin
                    // Reached invalid node - not found
                    search_state_next = SEARCH_COMPLETE;
                    // search_found_match_next remains 0
                end else if (search_node.data == search_data) begin
                    // Found match
                    search_found_match_next = 1'b1;
                    search_state_next = SEARCH_COMPLETE;
                end else if (search_data < search_node.data) begin
                    // Go left
                    if (addr_valid(left_child(search_addr))) begin
                        search_addr_next = left_child(search_addr);
                    end else begin
                        // Can't go left - not found
                        search_state_next = SEARCH_COMPLETE;
                        // search_found_match_next remains 0
                    end
                end else begin
                    // Go right
                    if (addr_valid(right_child(search_addr))) begin
                        search_addr_next = right_child(search_addr);
                    end else begin
                        // Can't go right - not found
                        search_state_next = SEARCH_COMPLETE;
                        // search_found_match_next remains 0
                    end
                end
            end
            
            SEARCH_COMPLETE: begin
                search_state_next = SEARCH_IDLE;
                // Keep search_found_match value during COMPLETE state
            end
            
            default: begin
                search_state_next = SEARCH_IDLE;
                search_found_match_next = 1'b0;
            end
        endcase
    end
    
    // Output assignments
    assign insert_done = (insert_state == COMPLETE);
    assign insert_collision = insert_done && insert_found_collision;
    assign search_done = (search_state == SEARCH_COMPLETE);
    assign found = search_done && search_found_match;
    
    // Assertions for verification
    /* verilator lint_off SYNCASYNCNET */
    /* verilator lint_off WIDTHEXPAND */
    assert property (@(posedge clk) disable iff (!rst_n)
        !(insert && search))
    else $error("Simultaneous insert and search operations not supported");
    
    assert property (@(posedge clk) disable iff (!rst_n)
        current_addr < DEPTH)
    else $error("Insert address out of bounds");
    
    assert property (@(posedge clk) disable iff (!rst_n)
        search_addr < DEPTH)
    else $error("Search address out of bounds");
    /* verilator lint_on WIDTHEXPAND */
    /* verilator lint_on SYNCASYNCNET */

endmodule
