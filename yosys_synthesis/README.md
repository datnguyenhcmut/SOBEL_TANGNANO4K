# Yosys Synthesis & Diagram Generation Guide

## 📋 Overview
This folder contains a Yosys synthesis script to process Verilog designs and generate RTL/gate-level diagrams in PDF format.

## 🔧 Prerequisites

### Install Yosys on WSL Ubuntu:
```bash
sudo apt update
sudo apt install -y yosys graphviz xdot
```

## 🚀 Quick Start

### 1. Navigate to this folder in WSL
```bash
wsl
cd /mnt/d/tangnano4k/SOBEL_TANGNANO4K/yosys_synthesis
```

### 2. Run Yosys Synthesis
```bash
yosys synthesize.ys
```

### 3. View Output Files
After running, you'll find:
- `rtl_diagram.pdf` - Complete RTL schematic (all flip-flops, muxes, adders)
- `gate_diagram.pdf` - Gate-level netlist (after synthesis)
- `synthesized_netlist.v` - Synthesized Verilog netlist

## 📂 File Locations
All output files are generated in: `/mnt/d/tangnano4k/SOBEL_TANGNANO4K/yosys_synthesis`

Access from Windows: `d:\tangnano4k\SOBEL_TANGNANO4K\yosys_synthesis\`

## 📊 What the Script Does

### Synthesis Flow:
1. **Read Verilog** - Load all Sobel modules
2. **proc** - Convert always blocks to logic
3. **opt** - Optimize (remove unused logic)
4. **fsm** - Extract finite state machines
5. **memory** - Extract memory blocks
6. **flatten** - Expand all modules to show complete RTL
7. **show** (1st) - Generate RTL diagram
8. **wreduce** - Optimize bit widths
9. **techmap** - Map to generic gates
10. **abc** - Advanced logic synthesis
11. **show** (2nd) - Generate gate-level diagram

## 🎯 Expected Outputs

### RTL Diagram shows:
- All D flip-flops (registers)
- All multiplexers
- All adders/subtractors
- All comparators
- Complete datapath and control logic

### Gate-Level Diagram shows:
- AND, OR, XOR, NAND gates
- Optimized logic after synthesis
- Final netlist structure

## 💡 Tips

- **Large Design**: PDF may be very large. Use `xdot rtl_diagram.dot` to view interactively
- **Simplify**: Comment out `flatten;` to see hierarchical modules instead
- **Performance**: Synthesis may take a few minutes for complex designs

---

**Created**: 2025-11-20  
**Author**: GitHub Copilot  
**Compatible with**: WSL Ubuntu, Yosys 0.9+
