import re

# Read original file
with open('verilog/sobel/line_buffer.v', 'r', encoding='utf-8') as f:
    content = f.read()

print("Starting optimization...")

# 1. Remove redundant register declarations
content = re.sub(r'\s*// Registered BRAM outputs.*\n.*\n.*\n.*\n', '', content)

# 2. Simplify declarations
content = content.replace(
    """    // Address tracking for BRAM access
    reg [ADDR_WIDTH-1:0] write_addr;
    reg [ADDR_WIDTH-1:0] write_addr_d0;
    reg [ADDR_WIDTH-1:0] write_addr_d1;""",
    "    // Address tracking - simplified"
)

content = content.replace(
    """    // Pipeline control (extended to match BRAM 2-cycle read latency)
    reg pixel_valid_d0, pixel_valid_d1, pixel_valid_d2;
    reg [ADDR_WIDTH-1:0] col_addr_d0, col_addr_d1, col_addr_d2;
    reg [ADDR_WIDTH-1:0] row_count_d0, row_count_d1, row_count_d2;

    // Current row pixel pipeline (align with BRAM outputs)
    reg [PIXEL_WIDTH-1:0] pixel_in_d0;
    reg [PIXEL_WIDTH-1:0] pixel_in_d1;
    reg [PIXEL_WIDTH-1:0] pixel_in_d2;""",
    """    // Pipeline for BRAM 2-cycle read latency  
    reg pixel_valid_d1, pixel_valid_d2;
    reg [ADDR_WIDTH-1:0] col_addr_d1, col_addr_d2;
    reg [ADDR_WIDTH-1:0] row_count_d1, row_count_d2;

    // Current row pixel pipeline
    reg [PIXEL_WIDTH-1:0] pixel_in_d1;
    reg [PIXEL_WIDTH-1:0] pixel_in_d2;"""
)

print("Step 1: Declarations optimized")

# Save for checking
with open('verilog/sobel/line_buffer.v', 'w', encoding='utf-8') as f:
    f.write(content)
    
print("Optimization complete! File saved.")
