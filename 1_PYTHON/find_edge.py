from generate_golden_rtl_aware_v2 import generate_vectors_rtl_optimized

frame, exp = generate_vectors_rtl_optimized(64, 48, 123)
edges = []
for i, rgb565 in enumerate(exp):
    r = (rgb565 >> 11) * 8
    g = ((rgb565 >> 5) & 0x3f) * 4
    b = (rgb565 & 0x1f) * 8
    edge_approx = (r + g + b) // 3
    edges.append((i, edge_approx, rgb565))

# Find outputs with edge near 97
print("Python outputs with edge ~= 97:")
for i, e, rgb in edges:
    if 95 <= e <= 99:
        print(f"  [{i:3d}] edge~={e:3d} rgb=0x{rgb:04x}")
