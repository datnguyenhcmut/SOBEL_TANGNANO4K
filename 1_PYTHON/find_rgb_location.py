from generate_golden_rtl_aware_v2 import generate_vectors_rtl_optimized, pack_edge_to_rgb565

frame, exp = generate_vectors_rtl_optimized(64, 48, 123)

# Find output[2180]
target_rgb = 0x632c
for i, rgb in enumerate(exp):
    if rgb == target_rgb:
        print(f"Python output[{i}] = 0x{rgb:04x}")
        
        # Calculate which (row, col) this corresponds to
        # Valid outputs start at row=3, col=2 (after window_valid)
        # Each row has (IMG_WIDTH - 2) = 62 valid columns (col 2 to 63)
        row = 3 + i // 62
        col = 2 + i % 62
        print(f"  Corresponds to: row={row}, col={col}")
        print()
