#!/usr/bin/env python3
"""Generate a simple synthetic video with moving objects for Sobel testing.

The video contains multiple bright squares moving across a darker background to
exercise edge responses. Frames default to 640x480 at 30 FPS.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import math
import cv2
import numpy as np


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def draw_scene(frame_idx: int, width: int, height: int, total_frames: int) -> np.ndarray:
    t = frame_idx / max(total_frames - 1, 1)
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    # Moving horizontal bar
    bar_y = int((0.2 + 0.5 * math.sin(2 * math.pi * t)) * height)
    cv2.rectangle(frame, (0, bar_y), (width, bar_y + 20), (40, 150, 255), thickness=-1)

    # Diagonal moving square
    square_size = 80
    sq_x = int((0.1 + 0.7 * t) * (width - square_size))
    sq_y = int((0.6 + 0.3 * math.cos(2 * math.pi * t)) * (height - square_size))
    cv2.rectangle(frame, (sq_x, sq_y), (sq_x + square_size, sq_y + square_size), (255, 255, 255), thickness=-1)

    # Pulsing circle
    radius = int(40 + 20 * math.sin(4 * math.pi * t))
    cx = int(0.75 * width)
    cy = int(0.3 * height)
    cv2.circle(frame, (cx, cy), max(radius, 5), (255, 200, 40), thickness=-1)

    # Background gradient
    gradient = np.tile(np.linspace(20, 80, width, dtype=np.uint8), (height, 1))
    frame = cv2.add(frame, cv2.merge([gradient, gradient // 2, gradient // 4]))

    return frame


def generate_video(output: Path, width: int, height: int, frames: int, fps: int) -> None:
    ensure_dir(output.parent)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(output), fourcc, fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Unable to open video writer at {output}")

    for idx in range(frames):
        frame = draw_scene(idx, width, height, frames)
        writer.write(frame)

    writer.release()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic moving object video")
    parser.add_argument("--output", default="data/moving_object.mp4", help="Output video path")
    parser.add_argument("--width", type=int, default=640, help="Frame width")
    parser.add_argument("--height", type=int, default=480, help="Frame height")
    parser.add_argument("--frames", type=int, default=90, help="Number of frames to generate")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    args = parser.parse_args()

    output_path = Path(args.output)
    generate_video(output_path, args.width, args.height, args.frames, args.fps)
    print(f"Synthetic motion video written to {output_path} ({args.frames} frames @ {args.fps} fps)")


if __name__ == "__main__":
    main()
