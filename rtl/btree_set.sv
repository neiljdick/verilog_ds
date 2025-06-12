// A 'set' implemented by a simple binary search tree backed by a contiguous
// block ram. Supports insert and search operations.

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
    // Each node contains: [valid][data][left_ptr][right_ptr]
    typedef struct packed {
        logic valid;
        logic [DATA_WIDTH-1:0] data;
        logic [ADDR_WIDTH-1:0] left_ptr;
        logic [ADDR_WIDTH-1:0] right_ptr;
    } node_t;
    
    node_t ram [DEPTH-1:0];
    
    // State machine enumerations
    typedef enum logic [2:0] {
        IDLE = 3'b000,
        INSERT_TRAVERSE = 3'b001,
        INSERT_WRITE = 3'b010,
        INSERT_COMPLETE = 3'b011
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
    logic [ADDR_WIDTH-1:0] free_addr, free_addr_next;
    logic [DATA_WIDTH-1:0] target_data, target_data_next;
    logic [DATA_WIDTH-1:0] search_data, search_data_next;
    logic [ADDR_WIDTH-1:0] root_addr;
    
    // Operation tracking
    logic insert_found_collision;
    logic search_found_match;
    
    // Memory read data
    node_t current_node, search_node;
    assign current_node = ram[current_addr];
    assign search_node = ram[search_addr];
    
    // Free address tracking (simple linear allocation)
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            free_addr <= 1; // Reserve address 0 for special cases
        end else begin
            free_addr <= free_addr_next;
        end
    end
    
    // Root address is always 0 when tree is not empty
    assign root_addr = 0;
    
    // State machine sequential logic
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            insert_state <= IDLE;
            search_state <= SEARCH_IDLE;
            current_addr <= 0;
            search_addr <= 0;
            target_data <= 0;
            search_data <= 0;
            
            // Initialize memory
            for (int i = 0; i < DEPTH; i++) begin
                ram[i] <= '0;
            end
        end else begin
            insert_state <= insert_state_next;
            search_state <= search_state_next;
            current_addr <= current_addr_next;
            search_addr <= search_addr_next;
            target_data <= target_data_next;
            search_data <= search_data_next;
            
            // Handle memory writes during insert
            if (insert_state == INSERT_WRITE) begin
                if (!ram[root_addr].valid) begin
                    // First node in tree
                    ram[root_addr].valid <= 1'b1;
                    ram[root_addr].data <= target_data;
                    ram[root_addr].left_ptr <= '0;
                    ram[root_addr].right_ptr <= '0;
                end else begin
                    // Add new node
                    ram[free_addr].valid <= 1'b1;
                    ram[free_addr].data <= target_data;
                    ram[free_addr].left_ptr <= '0;
                    ram[free_addr].right_ptr <= '0;
                    
                    // Update parent's pointer
                    if (target_data < current_node.data) begin
                        ram[current_addr].left_ptr <= free_addr;
                    end else begin
                        ram[current_addr].right_ptr <= free_addr;
                    end
                end
            end
        end
    end
    
    // Insert state machine combinatorial logic
    always_comb begin
        insert_state_next = insert_state;
        current_addr_next = current_addr;
        target_data_next = target_data;
        free_addr_next = free_addr;
        insert_found_collision = 1'b0;
        
        case (insert_state)
            IDLE: begin
                if (insert) begin
                    insert_state_next = INSERT_TRAVERSE;
                    current_addr_next = root_addr;
                    target_data_next = data;
                end
            end
            
            INSERT_TRAVERSE: begin
                if (!current_node.valid) begin
                    // Empty tree or reached empty spot
                    insert_state_next = INSERT_WRITE;
                end else if (current_node.data == target_data) begin
                    // Found collision
                    insert_found_collision = 1'b1;
                    insert_state_next = INSERT_COMPLETE;
                end else if (target_data < current_node.data) begin
                    // Go left
                    if (current_node.left_ptr == 0) begin
                        // Need to create new left child
                        insert_state_next = INSERT_WRITE;
                    end else begin
                        current_addr_next = current_node.left_ptr;
                    end
                end else begin
                    // Go right
                    if (current_node.right_ptr == 0) begin
                        // Need to create new right child
                        insert_state_next = INSERT_WRITE;
                    end else begin
                        current_addr_next = current_node.right_ptr;
                    end
                end
            end
            
            INSERT_WRITE: begin
                insert_state_next = INSERT_COMPLETE;
                if (ram[root_addr].valid) begin
                    free_addr_next = free_addr + 1;
                end
            end
            
            INSERT_COMPLETE: begin
                insert_state_next = IDLE;
            end
            
            default: begin
                insert_state_next = IDLE;
            end
        endcase
    end
    
    // Search state machine combinatorial logic
    always_comb begin
        search_state_next = search_state;
        search_addr_next = search_addr;
        search_data_next = search_data;
        search_found_match = 1'b0;
        
        case (search_state)
            SEARCH_IDLE: begin
                if (search) begin
                    search_state_next = SEARCH_TRAVERSE;
                    search_addr_next = root_addr;
                    search_data_next = data;
                end
            end
            
            SEARCH_TRAVERSE: begin
                if (!search_node.valid) begin
                    // Empty tree or reached empty spot - not found
                    search_state_next = SEARCH_COMPLETE;
                end else if (search_node.data == search_data) begin
                    // Found match
                    search_found_match = 1'b1;
                    search_state_next = SEARCH_COMPLETE;
                end else if (search_data < search_node.data && search_node.left_ptr != 0) begin
                    // Go left
                    search_addr_next = search_node.left_ptr;
                end else if (search_data > search_node.data && search_node.right_ptr != 0) begin
                    // Go right
                    search_addr_next = search_node.right_ptr;
                end else begin
                    // No more children and no match - not found
                    search_state_next = SEARCH_COMPLETE;
                end
            end
            
            SEARCH_COMPLETE: begin
                search_state_next = SEARCH_IDLE;
            end
            
            default: begin
                search_state_next = SEARCH_IDLE;
            end
        endcase
    end
    
    // Output assignments
    assign insert_done = (insert_state == INSERT_COMPLETE);
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
        free_addr < DEPTH)
    else $error("Tree capacity exceeded");
    /* verilator lint_on WIDTHEXPAND */
    /* verilator lint_on SYNCASYNCNET */

endmodule
