# LINE BUFFER OPTIMIZATION FOR TANG NANO 4K
## Target Device: GW1NSR-4C (4608 LUTs, 10 BSRAM)

### Current Status (from synthesis report):
- **Logic Usage**: 2173/4608 LUTs (48%)
- **BSRAM Usage**: 9/10 blocks (90%)
- **Registers**: 1422/3612 (40%)

### Identified Issues:

#### 1. **TIMING BUG - Window Alignment Error**
From golden test output:
```
[MISMATCH t=6260000] got=7bcf exp=3186 (idx=0)
  window=00_00_00_9b_00_6f_f3_4a_cb
```

**Problem**: Window has extra 00_00_00 prefix  3-pixel misalignment
**Root Cause**: Pipeline delays not properly synchronized between:
- BRAM 2-cycle read latency
- Shift register updates  
- Valid signal generation

#### 2. **Resource Waste - Redundant Registers**

**Current Implementation**:
```verilog
reg [9:0] write_addr, write_addr_d0, write_addr_d1;  // 30 FFs
reg pixel_valid_d0, pixel_valid_d1, pixel_valid_d2;  // 3 FFs
reg [9:0] col_addr_d0, col_addr_d1, col_addr_d2;     // 30 FFs
reg [7:0] line0_q_d, line1_q_d, line2_q_d;           // 24 FFs
```
**Total**: ~87 redundant flip-flops

**Issue**: 
- write_addr duplicates col_addr
- _d0 stage unnecessary (BRAM has internal address register)
- line*_q_d redundant (BRAM has oce output register)

### Optimization Strategy:

#### Phase 1: Remove Redundant Registers (-75 FFs)
```verilog
// BEFORE (87 FFs):
reg [9:0] write_addr, write_addr_d0, write_addr_d1;
reg pixel_valid_d0;
reg [9:0] col_addr_d0;
reg [7:0] line0_q_d, line1_q_d, line2_q_d;

// AFTER (12 FFs):  
// Use col_addr directly, remove _d0 stage, remove line*_q_d
```

**Savings**: ~15-20 LUTs (from mux + control logic)

#### Phase 2: Simplify Address Logic
```verilog
// BEFORE:
always @(posedge clk) begin
    if (pixel_valid) begin
        if (col_addr == IMG_WIDTH-1) begin
            col_addr <= 0;
            write_addr <= 0;
        end else begin
            col_addr <= col_addr + 1;
            write_addr <= write_addr + 1;  // DUPLICATE!
        end
        write_addr_d0 <= write_addr;
    end
    if (pixel_valid_d0) write_addr_d1 <= write_addr_d0;
end

// AFTER:
always @(posedge clk) begin
    if (pixel_valid) begin
        col_addr <= (col_addr == IMG_WIDTH-1) ? 0 : col_addr + 1;
    end
end
```

**Savings**: ~5 LUTs (from address incrementer + mux)

#### Phase 3: Fix Pipeline Alignment

**BRAM Timing Diagram**:
```
Cycle:     0      1      2      3      4
          
addr_in:   A0     A1     A2     A3     A4
BRAM:      [reg]  [mem]  [reg]  ...
data_out:  --     --     D0     D1     D2
          
Latency = 2 cycles (address register + output register)
```

**Corrected Pipeline**:
```verilog
// Stage 0: Input
pixel_in, col_addr, row_count

// Stage 1: BRAM address register
pixel_in_d1, col_addr_d1, row_count_d1

// Stage 2: BRAM output available
pixel_in_d2, col_addr_d2, row_count_d2
line0_q, line1_q, line2_q (valid here!)

// Stage 3: Window formation
top_row[2] = line2_q  (row n-2)
mid_row[2] = line1_q  (row n-1)  
bot_row[2] = pixel_in_d2 (row n)
```

**Fix**: Use _d2 signals for window formation, not _d1

### Expected Results:

**Resource Savings**:
- **FFs**: -75 (~5% of total)
- **LUTs**: -20 to -25 (~1% reduction)
- **BSRAM**: Unchanged (3 blocks required)

**Performance**:
- **Latency**: 2 cycles (unchanged, BRAM limitation)
- **Throughput**: 1 pixel/cycle (unchanged)
- **Fmax**: Potentially +5-10% (shorter comb paths)

### Implementation Steps:

1. **Backup original**: cp line_buffer.v line_buffer_backup.v

2. **Remove redundant registers**:
   - Delete write_addr, write_addr_d0, write_addr_d1
   - Delete pixel_valid_d0, col_addr_d0, ow_count_d0  
   - Delete line0_q_d, line1_q_d, line2_q_d

3. **Simplify address generation**:
   - Use col_addr directly for BRAM addressing
   - Chain delays: col_addr  col_addr_d1  col_addr_d2

4. **Fix window timing**:
   - Update shift registers on pixel_valid_d2 (not _d1)
   - Use BRAM outputs directly: line2_q, line1_q (not _q_d)
   - Align pixel_in_d2 with BRAM outputs

5. **Update valid generation**:
   ```verilog
   window_valid <= pixel_valid_d2 && 
                   (row_count_d2 >= 2) && 
                   (col_addr_d2 >= 1) &&
                   !prefill_active;
   ```

6. **Test**:
   ```bash
   cd sim
   make golden  # Should pass with 0 mismatches
   make random  # Verify on random data
   ```

### Verification Checklist:

- [ ] Golden test passes (0 mismatches)
- [ ] Random test passes (< 5 mismatches acceptable)
- [ ] Synthesis uses < 2100 LUTs
- [ ] BSRAM usage = 9 blocks
- [ ] Timing meets 74.25 MHz (video clock)

---
**Author**: GitHub Copilot  
**Date**: 2025-11-08  
**Device**: Tang Nano 4K (GW1NSR-LV4C)
