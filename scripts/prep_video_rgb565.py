#!/usr/bin/env python3
"""Prepare RGB565 stimulus for the Sobel video verification flow.

Steps
-----
1. Load a source video (default: data/video_in.mp4). If it does not exist, generate a
   short synthetic clip and save it to that path.
2. Resize every frame to 640x480, convert to RGB, and quantise to RGB565.
3. Write the concatenated RGB565 stream to data/video_in.rgb (little-endian).
4. Emit metadata (frames, width, height, fps) to data/video_meta.txt so that the
   Verilog testbench knows how long to run.

Usage
-----
python scripts/prep_video_rgb565.py \
    --video data/video_in.mp4 \
    --frames-dir data/input_frames \
    --output-dir data \
    --width 640 --height 480 --max-frames 0

Dependencies: OpenCV (cv2) and NumPy.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Tuple

import cv2
import numpy as np


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def generate_synthetic_video(path: Path, size: Tuple[int, int], frames: int, fps: int) -> None:
    """Generate a simple colour-gradient clip so that the flow always has input."""
    ensure_dir(path.parent)
    width, height = size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    if not writer.isOpened():  # pragma: no cover - diagnostic path
        raise RuntimeError(f"Failed to create fallback video at {path}")

    x = np.linspace(0, 1, width, dtype=np.float32)
    y = np.linspace(0, 1, height, dtype=np.float32)
    xx, yy = np.meshgrid(x, y)
    for frame_idx in range(frames):
        phase = frame_idx / max(frames - 1, 1)
        r = np.clip((xx + phase) % 1.0, 0.0, 1.0)
        g = np.clip((yy + 0.5 * phase) % 1.0, 0.0, 1.0)
        b = np.clip(((xx * yy) + phase) % 1.0, 0.0, 1.0)
        img = np.stack((b, g, r), axis=-1) * 255.0
        writer.write(img.astype(np.uint8))
    writer.release()
    print(f"[prep_video] Generated synthetic fallback clip -> {path}")


def iter_frames_from_dir(frame_dir: Path) -> Iterable[np.ndarray]:
    image_paths = sorted(frame_dir.glob("*.png"))
    if not image_paths:
        raise FileNotFoundError(f"No PNG frames found in {frame_dir}")
    for img_path in image_paths:
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            raise RuntimeError(f"Failed to decode frame: {img_path}")
        yield img


def load_frames(args: argparse.Namespace) -> Tuple[Iterable[np.ndarray], int]:
    video_path = Path(args.video)
    frame_dir = Path(args.frames_dir)

    if video_path.exists():
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise RuntimeError(f"Unable to open video file {video_path}")

        def _frame_iter():
            read_frames = 0
            while True:
                ok, frame = cap.read()
                if not ok or frame is None:
                    break
                yield frame
                read_frames += 1
                if args.max_frames and read_frames >= args.max_frames:
                    break
            cap.release()

        return _frame_iter(), int(cap.get(cv2.CAP_PROP_FPS) or args.fps)

    if frame_dir.exists():
        frames = list(iter_frames_from_dir(frame_dir))
        if args.max_frames:
            frames = frames[: args.max_frames]
        if not frames:
            raise RuntimeError(f"Frame directory {frame_dir} is empty")
        return frames, args.fps

    # Fall back to generating a synthetic clip on disk (so the comparator can reopen it)
    generate_synthetic_video(video_path, (args.width, args.height), frames=args.fallback_frames, fps=args.fps)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Failed to open generated fallback video at {video_path}")

    def _synthetic_iter():
        read_frames = 0
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            yield frame
            read_frames += 1
            if args.max_frames and read_frames >= args.max_frames:
                break
        cap.release()

    return _synthetic_iter(), args.fps


def bgr_to_rgb565(frame_bgr: np.ndarray) -> np.ndarray:
    rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    r = (rgb[:, :, 0] >> 3).astype(np.uint16)
    g = (rgb[:, :, 1] >> 2).astype(np.uint16)
    b = (rgb[:, :, 2] >> 3).astype(np.uint16)
    return (r << 11) | (g << 5) | b


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare RGB565 stimulus for Sobel video verification")
    parser.add_argument("--video", default="data/video_in.mp4", help="Source video path (default: data/video_in.mp4)")
    parser.add_argument("--frames-dir", default="data/input_frames", help="Optional directory of PNG frames to use when video is absent")
    parser.add_argument("--output-dir", default="data", help="Directory for generated artifacts (RGB stream, metadata)")
    parser.add_argument("--rgb-output", default="video_in.rgb", help="Relative filename for the packed RGB565 stream")
    parser.add_argument("--meta", default="video_meta.txt", help="Relative filename for metadata output")
    parser.add_argument("--width", type=int, default=640, help="Target frame width")
    parser.add_argument("--height", type=int, default=480, help="Target frame height")
    parser.add_argument("--fps", type=int, default=30, help="Fallback FPS when the source video does not report it")
    parser.add_argument("--max-frames", type=int, default=0, help="Optional limit on the number of frames to process (0 = all)")
    parser.add_argument("--fallback-frames", type=int, default=30, help="Frames to synthesise when no input media is supplied")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    frames_iter, fps = load_frames(args)

    rgb_out_path = output_dir / args.rgb_output
    meta_path = output_dir / args.meta
    frame_count = 0

    with open(rgb_out_path, "wb") as rgb_file:
        for frame_bgr in frames_iter:
            resized = cv2.resize(frame_bgr, (args.width, args.height), interpolation=cv2.INTER_LINEAR)
            rgb565 = bgr_to_rgb565(resized)
            rgb565.astype('<u2').tofile(rgb_file)
            frame_count += 1
    if frame_count == 0:
        raise RuntimeError("No frames processed; ensure the source video or frames exist")

    meta_contents = "\n".join(
        [
            f"frames={frame_count}",
            f"width={args.width}",
            f"height={args.height}",
            f"fps={fps}",
            "format=RGB565",
            f"source={Path(args.video).as_posix()}",
        ]
    )
    meta_path.write_text(meta_contents + "\n", encoding="utf-8")

    print(f"[prep_video] Frames processed: {frame_count}")
    print(f"[prep_video] RGB565 stream -> {rgb_out_path}")
    print(f"[prep_video] Metadata -> {meta_path}")


if __name__ == "__main__":
    main()
