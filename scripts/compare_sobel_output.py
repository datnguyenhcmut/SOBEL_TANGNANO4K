#!/usr/bin/env python3
"""Compare simulation output from the Sobel video flow against a software reference.

The script reconstructs the grayscale input stream from the packed RGB565 stimulus,
runs a software Sobel filter that mirrors the RTL behaviour (same weighting, border
handling, and RGB565 packing), and checks the raw output captured by
`tb_sobel_video`. The comparison prints summary metrics, optionally emits a JSON
report, and can generate a side-by-side diff video for quick visual inspection.

Usage
-----
python scripts/compare_sobel_output.py \
    --input ../data/video_in.rgb \
    --output ../data/video_out.rgb \
    --meta ../data/video_meta.txt \
    --report ../data/video_report.json \
    --diff-video ../data/video_compare.mp4
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Dict, Tuple

import cv2
import numpy as np


def parse_metadata(meta_path: Path) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    with meta_path.open("r", encoding="utf-8") as fh:
        for raw_line in fh:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            meta[key.strip()] = value.strip()
    required = {"frames", "width", "height"}
    missing = required - meta.keys()
    if missing:
        raise ValueError(f"Metadata file {meta_path} missing keys: {sorted(missing)}")
    return meta


def rgb565_to_channels(rgb565: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    r5 = (rgb565 >> 11) & 0x1F
    g6 = (rgb565 >> 5) & 0x3F
    b5 = rgb565 & 0x1F
    r8 = (r5 << 3) | (r5 >> 2)
    g8 = (g6 << 2) | (g6 >> 4)
    b8 = (b5 << 3) | (b5 >> 2)
    return r8.astype(np.uint16), g8.astype(np.uint16), b8.astype(np.uint16)


def rgb565_to_gray(rgb565: np.ndarray) -> np.ndarray:
    r8, g8, b8 = rgb565_to_channels(rgb565)
    # Weighted conversion matches rtl rgb_to_gray (77, 151, 28) >> 8
    weighted = (r8 * 77) + (g8 * 151) + (b8 * 28)
    gray = (weighted >> 8).astype(np.uint8)
    return gray


def sobel_reference(gray_frames: np.ndarray) -> np.ndarray:
    """Compute Sobel magnitude with the same semantics as the RTL pipeline.

    Only rows 1..H-2 and columns 1..W-1 are valid. Column +1 uses wrap-around to
    column 0 for the rightmost pixel to match the line buffer behaviour.
    """
    frames, height, width = gray_frames.shape
    valid_h = height - 2
    valid_w = width - 1
    if valid_h <= 0 or valid_w <= 0:
        raise ValueError("Frame dimensions too small for Sobel kernel")

    sobel_mag = np.empty((frames, valid_h, valid_w), dtype=np.uint8)

    for idx in range(frames):
        g = gray_frames[idx].astype(np.int16)

        top = g[:-2, :]
        mid = g[1:-1, :]
        bot = g[2:, :]

        top_left = top[:, :-1]
        top_center = top[:, 1:]
        top_right = np.roll(top, -1, axis=1)[:, 1:]

        mid_left = mid[:, :-1]
        mid_right = np.roll(mid, -1, axis=1)[:, 1:]

        bot_left = bot[:, :-1]
        bot_center = bot[:, 1:]
        bot_right = np.roll(bot, -1, axis=1)[:, 1:]

        gx = (-top_left + top_right) - (mid_left << 1) + (mid_right << 1) - bot_left + bot_right
        gy = (-top_left - (top_center << 1) - top_right) + bot_left + (bot_center << 1) + bot_right

        mag = np.abs(gx).astype(np.int32) + np.abs(gy).astype(np.int32)
        mag >>= 3
        mag = np.clip(mag, 0, 255).astype(np.uint8)

        sobel_mag[idx] = mag

    return sobel_mag


def magnitude_to_rgb565(mag: np.ndarray) -> np.ndarray:
    r = (mag >> 3).astype(np.uint16)
    g = (mag >> 2).astype(np.uint16)
    b = (mag >> 3).astype(np.uint16)
    return (r << 11) | (g << 5) | b


def embed_roi(roi: np.ndarray, height: int, width: int) -> np.ndarray:
    frame = np.zeros((height, width), dtype=np.uint8)
    frame[1:-1, 1:] = roi
    return frame


def write_diff_video(
    expected_roi: np.ndarray,
    actual_roi: np.ndarray,
    abs_diff_roi: np.ndarray,
    gray_frames: np.ndarray,
    fps: float,
    output_path: Path,
) -> None:
    height, width = gray_frames.shape[1:]
    ensure_parent_dir(output_path)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    frame_size = (width * 3, height)
    writer = cv2.VideoWriter(str(output_path), fourcc, fps, frame_size)
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open video writer at {output_path}")

    for idx in range(expected_roi.shape[0]):
        base_roi = gray_frames[idx, 1:-1, 1:]
        base = embed_roi(base_roi, height, width)
        exp_full = embed_roi(expected_roi[idx], height, width)
        act_full = embed_roi(actual_roi[idx], height, width)
        diff_full = embed_roi(np.clip(abs_diff_roi[idx] * 4, 0, 255).astype(np.uint8), height, width)

        base_bgr = cv2.cvtColor(base.astype(np.uint8), cv2.COLOR_GRAY2BGR)
        exp_bgr = cv2.cvtColor(exp_full, cv2.COLOR_GRAY2BGR)
        act_bgr = cv2.cvtColor(act_full, cv2.COLOR_GRAY2BGR)
        diff_bgr = cv2.cvtColor(diff_full, cv2.COLOR_GRAY2BGR)

        left = cv2.addWeighted(base_bgr, 0.4, exp_bgr, 0.6, 0)
        middle = cv2.addWeighted(base_bgr, 0.4, act_bgr, 0.6, 0)

        panel = np.hstack([left, middle, diff_bgr])
        label = f"frame {idx:03d}"
        cv2.putText(panel, label, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
        writer.write(panel)

    writer.release()


def ensure_parent_dir(path: Path) -> None:
    if path.parent and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Sobel simulation output against software reference")
    parser.add_argument("--input", required=True, help="Path to packed RGB565 stimulus (video_in.rgb)")
    parser.add_argument("--output", required=True, help="Path to RTL output stream (video_out.rgb)")
    parser.add_argument("--meta", required=True, help="Metadata emitted by prep_video_rgb565.py")
    parser.add_argument("--report", help="Optional JSON report path for metrics")
    parser.add_argument("--diff-video", help="Optional MP4 path for visual diff output")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    meta_path = Path(args.meta)

    if not input_path.exists():
        raise FileNotFoundError(f"Input stream not found: {input_path}")
    if not output_path.exists():
        raise FileNotFoundError(f"Simulation output not found: {output_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {meta_path}")

    meta = parse_metadata(meta_path)
    frames = int(meta["frames"])
    width = int(meta["width"])
    height = int(meta["height"])
    fps = float(meta.get("fps", 30))

    total_pixels = frames * height * width
    input_stream = np.fromfile(input_path, dtype="<u2")
    if input_stream.size < total_pixels:
        raise ValueError(
            f"Stimulus size mismatch: expected {total_pixels} samples, found {input_stream.size}"
        )
    input_stream = input_stream[:total_pixels]
    input_frames = input_stream.reshape(frames, height, width)

    gray_frames = rgb565_to_gray(input_frames)

    expected_mag = sobel_reference(gray_frames)
    expected_rgb565 = magnitude_to_rgb565(expected_mag)

    valid_h = height - 2
    valid_w = width - 1
    total_samples = frames * valid_h * valid_w

    actual_stream = np.fromfile(output_path, dtype="<u2")
    if actual_stream.size != total_samples:
        raise ValueError(
            f"RTL output size mismatch: expected {total_samples} samples, found {actual_stream.size}"
        )
    actual_frames = actual_stream.reshape(frames, valid_h, valid_w)

    expected_frames = expected_rgb565.reshape(frames, valid_h, valid_w)

    diff_words = expected_frames.astype(np.int32) - actual_frames.astype(np.int32)
    mismatches = int(np.count_nonzero(diff_words))

    expected_mag_roi = expected_mag
    actual_mag_roi = rgb565_to_gray(actual_frames)
    abs_diff = np.abs(expected_mag_roi.astype(np.int16) - actual_mag_roi.astype(np.int16))
    max_abs_diff = int(abs_diff.max()) if abs_diff.size else 0
    mean_abs_diff = float(abs_diff.mean())
    mse = float(np.mean((expected_mag_roi.astype(np.float32) - actual_mag_roi.astype(np.float32)) ** 2))
    psnr = math.inf if mse == 0.0 else 10.0 * math.log10((255.0 ** 2) / mse)

    print("=== Sobel Video Comparison ===")
    print(f"Frames           : {frames}")
    print(f"Frame size       : {width}x{height} (valid region {valid_w}x{valid_h})")
    print(f"Samples compared : {total_samples}")
    print(f"Mismatches       : {mismatches} ({mismatches / total_samples:.6%})")
    print(f"Max |diff|       : {max_abs_diff}")
    print(f"Mean |diff|      : {mean_abs_diff:.4f}")
    print(f"PSNR             : {'inf' if math.isinf(psnr) else f'{psnr:.2f} dB'}")

    if args.report:
        report_path = Path(args.report)
        ensure_parent_dir(report_path)
        report = {
            "frames": frames,
            "width": width,
            "height": height,
            "valid_width": valid_w,
            "valid_height": valid_h,
            "total_samples": total_samples,
            "mismatches": mismatches,
            "mismatch_rate": mismatches / total_samples,
            "max_abs_diff": max_abs_diff,
            "mean_abs_diff": mean_abs_diff,
            "psnr_db": None if math.isinf(psnr) else psnr,
        }
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {report_path}")

    if args.diff_video:
        diff_video_path = Path(args.diff_video)
        write_diff_video(expected_mag_roi, actual_mag_roi, abs_diff, gray_frames, fps, diff_video_path)
        print(f"Diff video written to {diff_video_path}")

    if mismatches == 0:
        print("Status: PASS")
    else:
        print("Status: FAIL")


if __name__ == "__main__":
    main()
