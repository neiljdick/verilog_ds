#!/bin/bash
# SystemVerilog linting script using Verilator

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running SystemVerilog linting with Verilator...${NC}"

# Find all SystemVerilog and Verilog files
SV_FILES=$(find rtl -name "*.sv" -o -name "*.v" 2>/dev/null || true)

if [ -z "$SV_FILES" ]; then
    echo -e "${YELLOW}No SystemVerilog files found in rtl/ directory${NC}"
    exit 0
fi

# Lint each file
ERROR_COUNT=0
for file in $SV_FILES; do
    echo -e "Linting: ${file}"
    if ! verilator --lint-only -Wall --timescale 1ns/1ps --assert "$file" 2>&1; then
        ERROR_COUNT=$((ERROR_COUNT + 1))
        echo -e "${RED}✗ Linting failed for $file${NC}"
    else
        echo -e "${GREEN}✓ $file passed linting${NC}"
    fi
done

if [ $ERROR_COUNT -eq 0 ]; then
    echo -e "${GREEN}All SystemVerilog files passed linting!${NC}"
    exit 0
else
    echo -e "${RED}$ERROR_COUNT file(s) failed linting${NC}"
    exit 1
fi
