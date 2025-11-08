#!/usr/bin/env python3
"""
Generate golden input/output vectors for the Sobel pipeline matching the RTL behavior.
- Input: random RGB565 frame (deterministic with seed)
- Output: two mem files in sim/golden/
    * input_rgb565.mem       (WIDTH*HEIGHT lines, 16-bit hex)
    * expected_output.mem    ((HEIGHT-2)*(WIDTH-1) lines, 16-bit hex)

The simulator mirrors the RTL pipeline stage-by-stage (rgb_to_gray -> line_buffer ->
sobel_kernel -> edge_mag), including the Gowin-style line buffer warm-up and pipeline
latencies, so the generated vectors should align exactly with `make golden`.
"""
import argparse
import os
import random
from collections import deque
from typing import Deque, List, Optional, Tuple


# -----------------------------------------------------------------------------
# RGB565 helpers
# -----------------------------------------------------------------------------


def expand5to8(v5: int) -> int:
    return ((v5 & 0x1F) << 3) | ((v5 & 0x1F) >> 2)


def expand6to8(v6: int) -> int:
    return ((v6 & 0x3F) << 2) | ((v6 & 0x3F) >> 4)


def rgb565_to_rgb8(rgb: int) -> Tuple[int, int, int]:
    r5 = (rgb >> 11) & 0x1F
    g6 = (rgb >> 5) & 0x3F
    b5 = rgb & 0x1F
    return expand5to8(r5), expand6to8(g6), expand5to8(b5)


def rgb565_to_gray8(rgb: int) -> int:
    r8, g8, b8 = rgb565_to_rgb8(rgb)
    weighted = (77 * r8) + (151 * g8) + (28 * b8)
    return (weighted >> 8) & 0xFF


def pack_edge_to_rgb565(edge8: int) -> int:
    r5 = (edge8 >> 3) & 0x1F
    g6 = (edge8 >> 2) & 0x3F
    b5 = (edge8 >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


# -----------------------------------------------------------------------------
# Sobel helpers
# -----------------------------------------------------------------------------


def sobel_gx_gy(win: List[List[int]]) -> Tuple[int, int]:
    p0, p1, p2 = win[0]
    p3, _, p5 = win[1]
    p6, p7, p8 = win[2]
    gx = -p0 + p2 - (p3 << 1) + (p5 << 1) - p6 + p8
    gy = -p0 - (p1 << 1) - p2 + p6 + (p7 << 1) + p8
    return gx, gy


def gradients_to_edge_mag(gx: int, gy: int) -> int:
    ax = abs(int(gx))
    ay = abs(int(gy))
    s = ax + ay
    s >>= 3  # match RTL right shift before saturation
    if s > 255:
        s = 255
    return s


# -----------------------------------------------------------------------------
# Cycle-accurate Sobel pipeline simulator
# -----------------------------------------------------------------------------


class SobelPipelineSimulator:
    """Software model of sobel_processor.v with cycle accuracy."""

    def __init__(self, width: int, debug: bool = False) -> None:
        self.width = width
        self.flush_threshold = (width * 2) + 1
        self.max_row = (1 << 16) - 1
        self.debug_enabled = debug
        self.window_debug: Optional[List[Tuple[int, int]]] = [] if debug else None
        self.coord_fifo: Deque[Tuple[int, int]] = deque()
        self.reset()

    def reset(self) -> None:
        self.line0 = [0] * self.width
        self.line1 = [0] * self.width
        self.line2 = [0] * self.width

        self.write_addr = 0
        self.write_addr_d0 = 0
        self.write_addr_d1 = 0
        self.col_addr = 0
        self.row_count = 0

        self.pixel_valid_d0 = False
        self.pixel_valid_d1 = False
        self.col_addr_d0 = 0
        self.col_addr_d1 = 0
        self.row_count_d0 = 0
        self.row_count_d1 = 0
        self.pixel_in_d0 = 0
        self.pixel_in_d1 = 0

        self.line0_q_reg = 0
        self.line1_q_reg = 0
        self.line2_q_reg = 0
        self.line0_q_d = 0
        self.line1_q_d = 0
        self.line2_q_d = 0

        self.top_row = [0, 0, 0]
        self.mid_row = [0, 0, 0]
        self.bot_row = [0, 0, 0]

        self.prefill_active = True
        self.fill_count = 0

        self.gray_valid = False
        self.gray_pixel = 0
        self.window_valid = False
        self.sobel_valid = False
        self.gx = 0
        self.gy = 0
        self.edge_valid = False
        self.edge_magnitude = 0

        self.coord_fifo.clear()
        if self.window_debug is not None:
            self.window_debug.clear()

    def step(self, href: bool, rgb_pixel: int) -> List[Tuple[int, Optional[Tuple[int, int]]]]:
        """Advance one clock cycle, returning any edge RGB565 outputs emitted."""
        outputs: List[Tuple[int, Optional[Tuple[int, int]]]] = []

        # Outputs available at the beginning of the cycle (registered last cycle).
        if self.edge_valid:
            coord = self.coord_fifo.popleft() if self.coord_fifo else None
            outputs.append((pack_edge_to_rgb565(self.edge_magnitude), coord))
        else:
            coord = None

        gray_valid_in = self.gray_valid
        gray_pixel_in = self.gray_pixel

        window_valid_out = self.window_valid
        current_window = [self.top_row[:], self.mid_row[:], self.bot_row[:]]

        sobel_valid_out = self.sobel_valid
        gx_reg = self.gx
        gy_reg = self.gy

        addr0 = self.col_addr % self.width
        addr1 = self.col_addr_d0 % self.width
        addr2 = self.col_addr_d1 % self.width
        wad0 = self.write_addr % self.width
        wad1 = self.write_addr_d0 % self.width
        wad2 = self.write_addr_d1 % self.width

        line0_q = self.line0_q_reg
        line1_q = self.line1_q_reg
        line2_q = self.line2_q_reg

        line0_q_reg_next = self.line0[addr0]
        line1_q_reg_next = self.line1[addr1]
        line2_q_reg_next = self.line2[addr2]

        line1_din = 0 if (self.prefill_active and self.row_count_d0 == 0) else self.line0_q_d
        line2_din = 0 if (self.prefill_active and self.row_count_d1 <= 1) else self.line1_q_d

        if gray_valid_in:
            self.line0[wad0] = gray_pixel_in
        if self.pixel_valid_d0:
            self.line1[wad1] = line1_din
        if self.pixel_valid_d1:
            self.line2[wad2] = line2_din

        next_line0_q_d = self.line0_q_d
        next_line1_q_d = self.line1_q_d
        next_line2_q_d = self.line2_q_d
        if self.pixel_valid_d0:
            next_line0_q_d = line0_q
            next_line1_q_d = line1_q
            next_line2_q_d = line2_q

        next_top_row = self.top_row[:]
        next_mid_row = self.mid_row[:]
        next_bot_row = self.bot_row[:]
        if self.pixel_valid_d1:
            if self.prefill_active:
                next_top_row = [0, 0, 0]
                next_mid_row = [0, 0, 0]
                next_bot_row = [0, 0, 0]
            else:
                next_top_row = [self.top_row[1], self.top_row[2], self.line2_q_d]
                next_mid_row = [self.mid_row[1], self.mid_row[2], self.line1_q_d]
                next_bot_row = [self.bot_row[1], self.bot_row[2], self.pixel_in_d1]

        window_valid_next = (
            self.pixel_valid_d1
            and (self.row_count_d1 >= 2)
            and (self.col_addr_d1 >= 1)
            and (not self.prefill_active)
        )

        if window_valid_next:
            win_coord = (self.row_count_d1, self.col_addr_d1)
            self.coord_fifo.append(win_coord)
            if self.window_debug is not None:
                self.window_debug.append(win_coord)

        pixel_valid_d0_next = bool(gray_valid_in)
        pixel_valid_d1_next = bool(self.pixel_valid_d0)

        col_addr_d0_next = self.col_addr_d0
        row_count_d0_next = self.row_count_d0
        pixel_in_d0_next = self.pixel_in_d0
        if gray_valid_in:
            col_addr_d0_next = self.col_addr
            row_count_d0_next = self.row_count
            pixel_in_d0_next = gray_pixel_in

        col_addr_d1_next = self.col_addr_d1
        row_count_d1_next = self.row_count_d1
        pixel_in_d1_next = self.pixel_in_d1
        if self.pixel_valid_d0:
            col_addr_d1_next = self.col_addr_d0
            row_count_d1_next = self.row_count_d0
            pixel_in_d1_next = self.pixel_in_d0

        write_addr_next = self.write_addr
        col_addr_next = self.col_addr
        row_count_next = self.row_count
        if gray_valid_in:
            if self.col_addr == self.width - 1:
                col_addr_next = 0
                write_addr_next = 0
                if self.row_count < self.max_row:
                    row_count_next = self.row_count + 1
            else:
                col_addr_next = self.col_addr + 1
                write_addr_next = (self.write_addr + 1) % self.width

        write_addr_d0_next = self.write_addr_d0
        if gray_valid_in:
            write_addr_d0_next = self.write_addr
        write_addr_d1_next = self.write_addr_d1
        if self.pixel_valid_d0:
            write_addr_d1_next = self.write_addr_d0

        prefill_active_next = self.prefill_active
        fill_count_next = self.fill_count
        if self.prefill_active and gray_valid_in:
            if self.fill_count >= self.flush_threshold - 1:
                prefill_active_next = False
            else:
                fill_count_next = self.fill_count + 1

        gray_result = rgb565_to_gray8(rgb_pixel)
        gray_valid_next = bool(href)

        sobel_valid_next = window_valid_out
        if window_valid_out:
            gx_next, gy_next = sobel_gx_gy(current_window)
        else:
            gx_next, gy_next = (0, 0)

        edge_valid_next = sobel_valid_out
        if sobel_valid_out:
            edge_mag_next = gradients_to_edge_mag(gx_reg, gy_reg)
        else:
            edge_mag_next = 0

        self.gray_valid = gray_valid_next
        self.gray_pixel = gray_result
        self.write_addr = write_addr_next
        self.write_addr_d0 = write_addr_d0_next % self.width
        self.write_addr_d1 = write_addr_d1_next % self.width
        self.col_addr = col_addr_next
        self.row_count = row_count_next

        self.pixel_valid_d0 = pixel_valid_d0_next
        self.pixel_valid_d1 = pixel_valid_d1_next
        self.col_addr_d0 = col_addr_d0_next
        self.col_addr_d1 = col_addr_d1_next
        self.row_count_d0 = row_count_d0_next
        self.row_count_d1 = row_count_d1_next
        self.pixel_in_d0 = pixel_in_d0_next
        self.pixel_in_d1 = pixel_in_d1_next

        self.line0_q_reg = line0_q_reg_next
        self.line1_q_reg = line1_q_reg_next
        self.line2_q_reg = line2_q_reg_next
        self.line0_q_d = next_line0_q_d
        self.line1_q_d = next_line1_q_d
        self.line2_q_d = next_line2_q_d
        self.top_row = next_top_row
        self.mid_row = next_mid_row
        self.bot_row = next_bot_row

        self.prefill_active = prefill_active_next
        self.fill_count = fill_count_next
        self.window_valid = window_valid_next
        self.sobel_valid = sobel_valid_next
        self.gx = gx_next
        self.gy = gy_next
        self.edge_valid = edge_valid_next
        self.edge_magnitude = edge_mag_next

        return outputs


# -----------------------------------------------------------------------------
# Vector generation
# -----------------------------------------------------------------------------


def generate_vectors(width: int, height: int, seed: int) -> Tuple[List[int], List[int]]:
    rnd = random.Random(seed)
    frame = [rnd.getrandbits(16) for _ in range(width * height)]

    debug_enabled = bool(os.environ.get("LINEBUF_DEBUG"))
    sim = SobelPipelineSimulator(width, debug_enabled)

    expected: List[int] = []
    last_pixel = 0
    idx = 0

    for _row in range(height):
        for _col in range(width):
            rgb = frame[idx]
            idx += 1
            last_pixel = rgb
            for value, _coord in sim.step(True, rgb):
                expected.append(value)

        for _ in range(2):
            for value, _coord in sim.step(False, last_pixel):
                expected.append(value)

    for _ in range(200):
        for value, _coord in sim.step(False, last_pixel):
            expected.append(value)

    expected_count = (height - 2) * (width - 1)
    if len(expected) != expected_count:
        raise RuntimeError(f"Expected {expected_count} outputs but observed {len(expected)}")

    if debug_enabled and sim.window_debug is not None:
        rows = {}
        for row, col in sim.window_debug:
            rows.setdefault(row, 0)
            rows[row] += 1
        print(f"[DEBUG] total_windows={len(sim.window_debug)} unique_rows={len(rows)}")
        if rows:
            sorted_rows = sorted(rows)
            for row in sorted_rows[:5]:
                print(f"  row {row}: {rows[row]} windows")
            if len(sorted_rows) > 5:
                for row in sorted_rows[-5:]:
                    print(f"  row {row}: {rows[row]} windows")
            last_row = max(rows)
            last_cols = sorted(col for (row, col) in sim.window_debug if row == last_row)
            if last_cols:
                print(f"  last_row {last_row} columns: {last_cols[:5]} ... {last_cols[-5:]}")

    return frame, expected


def write_mem_hex(path: str, values: List[int]) -> None:
    with open(path, 'w') as f:
        for v in values:
            f.write(f"{v:04x}\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--width', type=int, default=64)
    ap.add_argument('--height', type=int, default=48)
    ap.add_argument('--seed', type=int, default=123)
    args = ap.parse_args()

    frame, expected = generate_vectors(args.width, args.height, args.seed)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'sim', 'golden')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    in_mem_path = os.path.join(out_dir, 'input_rgb565.mem')
    exp_mem_path = os.path.join(out_dir, 'expected_output.mem')
    write_mem_hex(in_mem_path, frame)
    write_mem_hex(exp_mem_path, expected)

    print(f"Wrote {len(frame)} input pixels to {in_mem_path}")
    print(f"Wrote {len(expected)} expected outputs to {exp_mem_path}")


if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Generate golden input/output vectors for Sobel pipeline matching the RTL behavior.
- Input: random RGB565 frame (deterministic with seed)
- Output: two mem files in sim/golden/
    * input_rgb565.mem       (WIDTH*HEIGHT lines, 16-bit hex)
    * expected_output.mem    ((HEIGHT-2)*(WIDTH-1) lines, 16-bit hex)

Border behavior matches RTL line_buffer:
- Valid windows start at row >= 2 and col >= 1
- Right neighbor uses wrap-around (col+1 wraps to 0)
- Top-of-frame not valid until two full rows have been received
- Additional pipeline stages in RTL are handled by comparing only when pixel_valid is asserted,
  and by emitting expected outputs in the order windows become valid.
"""
import argparse
import os
import random

# RGB565 pack/unpack helpers

def expand5to8(v5: int) -> int:
    return ((v5 & 0x1F) << 3) | ((v5 & 0x1F) >> 2)

def expand6to8(v6: int) -> int:
    return ((v6 & 0x3F) << 2) | ((v6 & 0x3F) >> 4)

def rgb565_to_rgb8(rgb: int):
    r5 = (rgb >> 11) & 0x1F
    g6 = (rgb >> 5) & 0x3F
    b5 = rgb & 0x1F
    return expand5to8(r5), expand6to8(g6), expand5to8(b5)

def rgb565_to_gray8(rgb: int) -> int:
    r8, g8, b8 = rgb565_to_rgb8(rgb)
    # Weighted: (77*R + 151*G + 28*B) >> 8
    w = (77 * r8) + (151 * g8) + (28 * b8)
    return (w >> 8) & 0xFF

def pack_edge_to_rgb565(edge8: int) -> int:
    r5 = (edge8 >> 3) & 0x1F
    g6 = (edge8 >> 2) & 0x3F
    b5 = (edge8 >> 3) & 0x1F
    return (r5 << 11) | (g6 << 5) | b5


def sobel_gx_gy(win):
    # win is 3x3 list of ints (0..255)
    p0,p1,p2 = win[0]
    p3,p4,p5 = win[1]
    p6,p7,p8 = win[2]
    gx = -p0 + p2 - 2*p3 + 2*p5 - p6 + p8
    gy = -p0 - 2*p1 - p2 + p6 + 2*p7 + p8
    return gx, gy

def sobel_edge8(win) -> int:
    gx, gy = sobel_gx_gy(win)
    ax = abs(int(gx))
    ay = abs(int(gy))
    s = ax + ay
    s >>= 3  # mirror RTL scaling (shift before saturation)
    if s > 255:
        s = 255
    return s


def generate_vectors(width: int, height: int, seed: int):
    rnd = random.Random(seed)
    # Generate random RGB565 frame
    frame = [rnd.getrandbits(16) for _ in range(width*height)]
    # Precompute grayscale stream
    gray_stream = [rgb565_to_gray8(px) for px in frame]

    # Simulate RTL line_buffer + Sobel tap scheduling cycle-accurately.
    # Mirror the Gowin single-clock SDPB implementation, including warm-up gating.
    zero_px = 0
    flush_threshold = (width * 2) + 1

    # BRAM storage for three lines (true dual-port, synchronous)
    line_mem0 = [0] * width
    line_mem1 = [0] * width
    line_mem2 = [0] * width

    # Address / pipeline registers
    col_addr = 0
    write_addr = 0
    write_addr_d0 = 0
    write_addr_d1 = 0
    row_count = 0
    row_count_d0 = 0
    row_count_d1 = 0
    col_addr_d0 = 0
    col_addr_d1 = 0
    pixel_valid_d0 = False
    pixel_valid_d1 = False
    pixel_in_d0 = 0
    pixel_in_d1 = 0

    # Registered BRAM outputs and 3x3 window shift registers
    line0_q_state = 0
    line1_q_state = 0
    line2_q_state = 0
    line0_q_d = 0
    line1_q_d = 0
    line2_q_d = 0
    top_row = [0, 0, 0]
    mid_row = [0, 0, 0]
    bot_row = [0, 0, 0]

    # Warm-up control mirrors RTL prefill logic
    prefill_active = True
    fill_count = 0

    window_valid_reg = False
    expected = []
    debug_enabled = bool(os.environ.get("LINEBUF_DEBUG"))
    debug_coords = [] if debug_enabled else None

    limit_row = (1 << 16) - 1  # large enough cap for our frame sizes

    def record_window(row_idx: int, col_idx: int, win):
        edge = sobel_edge8(win)
        expected.append(pack_edge_to_rgb565(edge))
        if debug_enabled:
            debug_coords.append((row_idx, col_idx))

    def step(valid: bool, pixel_val: int):
        nonlocal col_addr, col_addr_d0, col_addr_d1
        nonlocal write_addr, write_addr_d0, write_addr_d1
        nonlocal row_count, row_count_d0, row_count_d1
        nonlocal pixel_valid_d0, pixel_valid_d1, pixel_in_d0, pixel_in_d1
        nonlocal line0_q_state, line1_q_state, line2_q_state
        nonlocal line0_q_d, line1_q_d, line2_q_d
        nonlocal top_row, mid_row, bot_row
        nonlocal prefill_active, fill_count, window_valid_reg
        nonlocal line_mem0, line_mem1, line_mem2

        pv_d0 = pixel_valid_d0
        pv_d1 = pixel_valid_d1
        rc_d0 = row_count_d0
        rc_d1 = row_count_d1
        ca_d0 = col_addr_d0
        ca_d1 = col_addr_d1
        wa_d0 = write_addr_d0
        wa_d1 = write_addr_d1
        ca_curr = col_addr
        wa_curr = write_addr
        rc_curr = row_count

        # Synchronous BRAM outputs for this cycle (captured last cycle)
        line0_q = line0_q_state
        line1_q = line1_q_state
        line2_q = line2_q_state

        line1_din = zero_px if (prefill_active and rc_d0 == 0) else line0_q_d
        line2_din = zero_px if (prefill_active and rc_d1 <= 1) else line1_q_d

        next_top_row = top_row[:]
        next_mid_row = mid_row[:]
        next_bot_row = bot_row[:]

        if pv_d1:
            if prefill_active:
                next_top_row = [zero_px, zero_px, zero_px]
                next_mid_row = [zero_px, zero_px, zero_px]
                next_bot_row = [zero_px, zero_px, zero_px]
            else:
                next_top_row = [top_row[1], top_row[2], line2_q_d]
                next_mid_row = [mid_row[1], mid_row[2], line1_q_d]
                next_bot_row = [bot_row[1], bot_row[2], pixel_in_d1]

        next_window_valid = (
            pv_d1
            and (rc_d1 >= 2)
            and (ca_d1 >= 1)
            and (not prefill_active)
        )

        if next_window_valid:
            win = [
                next_top_row[:],
                next_mid_row[:],
                next_bot_row[:],
            ]
            record_window(rc_d1, ca_d1, win)

        if valid:
            line_mem0[wa_curr] = pixel_val
        if pv_d0:
            line_mem1[wa_d0] = line1_din
            line0_q_d = line0_q
            line1_q_d = line1_q
            line2_q_d = line2_q
        if pv_d1:
            line_mem2[wa_d1] = line2_din

        # Update pixel pipelines (order matters)
        if pv_d0:
            pixel_in_d1 = pixel_in_d0
        if valid:
            pixel_in_d0 = pixel_val

        pixel_valid_d1 = pv_d0
        pixel_valid_d0 = valid

        if valid:
            col_addr_d0 = ca_curr
            row_count_d0 = rc_curr
            write_addr_d0 = wa_curr
        if pv_d0:
            col_addr_d1 = ca_d0
            row_count_d1 = rc_d0
            write_addr_d1 = wa_d0

        if prefill_active and valid:
            if fill_count >= flush_threshold - 1:
                prefill_active = False
            else:
                fill_count += 1

        if valid:
            if ca_curr == width - 1:
                col_addr = 0
                write_addr = 0
                if rc_curr < limit_row:
                    row_count = rc_curr + 1
            else:
                col_addr = ca_curr + 1
                write_addr = wa_curr + 1
                row_count = rc_curr
        else:
            col_addr = ca_curr
            write_addr = wa_curr
            row_count = rc_curr

        top_row = next_top_row
        mid_row = next_mid_row
        bot_row = next_bot_row
        window_valid_reg = next_window_valid

        # Prepare BRAM outputs for the next cycle, honoring enable gating
        next_line0_q = line0_q_state
        next_line1_q = line1_q_state
        next_line2_q = line2_q_state
        if valid:
            next_line0_q = line_mem0[col_addr]
        if pv_d0:
            next_line1_q = line_mem1[col_addr_d0]
        if pv_d1:
            next_line2_q = line_mem2[col_addr_d1]

        line0_q_state = next_line0_q
        line1_q_state = next_line1_q
        line2_q_state = next_line2_q

    for gcur in gray_stream:
        step(True, gcur)

    # Flush pipeline bubbles (two extra cycles cover BRAM + shift latency)
    step(False, 0)
    step(False, 0)

    if debug_enabled:
        rows = {}
        for row, col in debug_coords:
            rows.setdefault(row, 0)
            rows[row] += 1
        print(f"[DEBUG] total_windows={len(debug_coords)} unique_rows={len(rows)}")
        for row in sorted(rows)[:5]:
            print(f"  row {row}: {rows[row]} windows")
        if len(rows) > 5:
            for row in sorted(rows)[-5:]:
                print(f"  row {row}: {rows[row]} windows")
        if rows:
            last_row = max(rows)
            cols = sorted(col for (row, col) in debug_coords if row == last_row)
            if cols:
                print(f"  last_row {last_row} columns: {cols[:5]} ... {cols[-5:]}")

    return frame, expected


def write_mem_hex(path: str, values):
    with open(path, 'w') as f:
        for v in values:
            f.write(f"{v:04x}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--width', type=int, default=64)
    ap.add_argument('--height', type=int, default=48)
    ap.add_argument('--seed', type=int, default=123)
    args = ap.parse_args()

    frame, expected = generate_vectors(args.width, args.height, args.seed)

    out_dir = os.path.join(os.path.dirname(__file__), '..', 'sim', 'golden')
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    in_mem_path = os.path.join(out_dir, 'input_rgb565.mem')
    exp_mem_path = os.path.join(out_dir, 'expected_output.mem')
    write_mem_hex(in_mem_path, frame)
    write_mem_hex(exp_mem_path, expected)

    print(f"Wrote {len(frame)} input pixels to {in_mem_path}")
    print(f"Wrote {len(expected)} expected outputs to {exp_mem_path}")

if __name__ == '__main__':
    main()
