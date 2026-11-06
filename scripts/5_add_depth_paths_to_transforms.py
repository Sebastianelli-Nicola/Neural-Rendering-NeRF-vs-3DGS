"""
This script was used to generate a depth-enabled version of a Nerfstudio
`transforms.json` file.

The standard dataset preparation pipeline generates a `transforms.json`
containing RGB image paths and camera poses, but does not automatically
reference custom depth maps added to the dataset.

This script creates a new transforms file (for example
`transforms_depth.json`) by adding a `depth_file_path` entry to every frame.

The script:
- Loads an existing Nerfstudio `transforms.json`.
- Matches each RGB frame with a depth map having the same filename.
- Verifies that every referenced depth map exists.
- Adds a `depth_file_path` field to each frame.
- Writes the updated dataset description to a new JSON file without
  modifying the original transforms file.

For example:

    images/frame_00001.png
    depths/frame_00001.png

becomes

    {
        "file_path": "images/frame_00001.png",
        "depth_file_path": "depths/frame_00001.png"
    }

Assumptions:
- The depth maps have already been generated and stored in the dataset
  `depths/` directory.
- RGB images and depth maps share the same filenames.
- The input transforms file already contains valid camera poses and image
  paths produced by the Nerfstudio dataset preparation pipeline.

This script was used to create dataset variants for depth-supervised
experiments while preserving the original RGB-only transforms file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Load transforms.json, add depth_file_path for each frame using the "
            "given depth directory, and save the result without modifying the original."
        )
    )
    parser.add_argument(
        "depth_dir",
        type=Path,
        help="Directory containing depth PNGs named like the RGB frames.",
    )
    parser.add_argument(
        "input_transforms",
        type=Path,
        help="Input transforms.json path.",
    )
    parser.add_argument(
        "output_transforms",
        type=Path,
        help="Output path for the updated JSON, for example transforms_depth.json.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=4,
        help="JSON indentation for the output file. Default: 4",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    depth_dir = args.depth_dir
    transforms_path = args.input_transforms
    output_path = args.output_transforms

    if not depth_dir.is_dir():
        raise SystemExit(f"Depth directory does not exist: {depth_dir}")
    if not transforms_path.is_file():
        raise SystemExit(f"Input transforms file does not exist: {transforms_path}")
    if output_path.exists():
        raise SystemExit(
            f"Output transforms file already exists: {output_path}. "
            "Choose a different path or remove it first."
        )

    with transforms_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    frames = data.get("frames")
    if not isinstance(frames, list):
        raise SystemExit(f"Expected a 'frames' list in {transforms_path}")

    mappings: list[tuple[str, str]] = []
    for frame in frames:
        file_path = frame.get("file_path")
        if not isinstance(file_path, str):
            raise SystemExit(f"Frame is missing a string file_path: {frame}")

        depth_filename = Path(file_path).name
        depth_path = depth_dir / depth_filename
        if not depth_path.is_file():
            raise SystemExit(
                f"Referenced depth file does not exist for RGB '{file_path}': {depth_path}"
            )

        depth_file_path = str(Path(depth_dir.name) / depth_filename)
        frame["depth_file_path"] = depth_file_path
        mappings.append((file_path, depth_file_path))

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=args.indent)
        file.write("\n")

    print(f"Updated {len(frames)} frames")
    print(f"Depth directory used: {depth_dir}")
    print(f"Input transforms: {transforms_path}")
    print(f"Output transforms: {output_path}")
    print("First mappings:")
    for rgb_file_path, depth_file_path in mappings[:5]:
        print(f"  {rgb_file_path} -> {depth_file_path}")


if __name__ == "__main__":
    main()
