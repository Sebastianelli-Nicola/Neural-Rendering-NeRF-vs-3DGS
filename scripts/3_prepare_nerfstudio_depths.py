"""
This script was used to generate the contents of the `depths/` directory
inside each Nerfstudio dataset.

The original dataset provided:
- RGB images in HEIF format.
- Depth maps already stored as PNG files.

RGB images and depth maps had matching filenames and identical ordering.

During dataset preparation, the RGB images were converted to PNG format and
processed by COLMAP/Nerfstudio, which produced a dataset where images were
renamed to the `frame_XXXXX.png` convention, and rotated.

The depth maps provided in the original dataset were not processed by colmap so this script was needed.

This script:
- Assumes that RGB images and depth maps are stored in the same order.
- Renames each depth map using the corresponding RGB frame filename produced by colmap.
- Assumes that a 90-degree clockwise rotation was performed by colmap (found empirically looking at the colmap images).
- Rotates depth maps by 90 degrees clockwise to match the orientation of the processed RGB images.
- Resizes depth maps to the RGB image resolution.
- Saves the processed depth maps into the dataset `depths/` directory.

Potential improvement:
- Investigate the exact orientation correction applied during RGB dataset
  preparation and derive the required depth-map transformation automatically,
  instead of relying on a hardcoded 90-degree clockwise rotation.

"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


RESAMPLING_MODES = {
    "nearest": Image.Resampling.NEAREST,
    "bilinear": Image.Resampling.BILINEAR,
}


def pngs_in_order(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.png"), key=lambda path: path.name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rotate, resize, and save depth PNGs from INPUT_DEPTH_DIR to "
            "OUTPUT_DEPTH_DIR using the ordered RGB frame names."
        )
    )
    parser.add_argument(
        "input_depth_dir",
        type=Path,
        help="Folder containing original ordered depth PNGs.",
    )
    parser.add_argument(
        "output_depth_dir",
        type=Path,
        help="Output folder for renamed depth PNGs, usually <dataset>/depths.",
    )
    parser.add_argument(
        "--image-dir",
        type=Path,
        default=None,
        help=(
            "RGB image directory used for target frame names. "
            "Default: <output_depth_dir>/../images"
        ),
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files in the output depth directory.",
    )
    parser.add_argument(
        "--rotate-depth",
        type=int,
        choices=(0, 90, -90, 180),
        default=90,
        help=(
            "Clockwise depth rotation in degrees before resizing. "
            "Default: 90. Pillow positive angles are counterclockwise, so this "
            "is applied internally with the opposite sign."
        ),
    )
    parser.add_argument(
        "--resample",
        choices=tuple(RESAMPLING_MODES),
        default="bilinear",
        help="Resize resampling mode. Default: bilinear",
    )
    parser.add_argument(
        "--examples",
        type=int,
        default=5,
        help="Number of example mappings to print. Default: 5",
    )
    return parser.parse_args()


def open_image_size(path: Path) -> tuple[int, int]:
    try:
        with Image.open(path) as image:
            return image.size
    except OSError as error:
        raise SystemExit(f"Could not open image {path}: {error}") from error


def process_depth_image(
    depth_path: Path,
    output_path: Path,
    rgb_size: tuple[int, int],
    rotate_depth: int,
    resample: Image.Resampling,
) -> tuple[tuple[int, int], tuple[int, int]]:
    try:
        with Image.open(depth_path) as depth_image:
            original_size = depth_image.size
            rotated_depth = depth_image.rotate(-rotate_depth, expand=True)
            resized_depth = rotated_depth.resize(rgb_size, resample=resample)

            if resized_depth.size != rgb_size:
                raise SystemExit(
                    "Processed depth size mismatch for "
                    f"{depth_path}: expected {rgb_size}, got {resized_depth.size}"
                )

            resized_depth.save(output_path)
            return original_size, resized_depth.size
    except OSError as error:
        raise SystemExit(f"Could not process depth image {depth_path}: {error}") from error


def main() -> None:
    args = parse_args()
    input_depth_dir = args.input_depth_dir
    output_depth_dir = args.output_depth_dir
    image_dir = args.image_dir or output_depth_dir.parent / "images"
    resample = RESAMPLING_MODES[args.resample]

    if not input_depth_dir.is_dir():
        raise SystemExit(f"Input depth directory does not exist: {input_depth_dir}")
    if not image_dir.is_dir():
        raise SystemExit(f"RGB image directory does not exist: {image_dir}")

    rgb_images = pngs_in_order(image_dir)
    depth_images = pngs_in_order(input_depth_dir)

    print(f"RGB images:   {len(rgb_images)} in {image_dir}")
    print(f"Depth images: {len(depth_images)} in {input_depth_dir}")
    print(f"Depth rotation: clockwise {args.rotate_depth} degrees")
    print(f"Resize resampling: {args.resample}")

    if len(rgb_images) != len(depth_images):
        raise SystemExit(
            "RGB/depth count mismatch; refusing to copy. "
            f"Found {len(rgb_images)} RGB images and {len(depth_images)} depth images."
        )

    output_depth_dir.mkdir(parents=True, exist_ok=True)

    mappings: list[tuple[Path, Path, tuple[int, int], tuple[int, int]]] = []
    for rgb_path, depth_path in zip(rgb_images, depth_images, strict=True):
        output_path = output_depth_dir / rgb_path.name
        if output_path.exists() and not args.overwrite:
            raise SystemExit(
                f"Output already exists: {output_path}. Re-run with --overwrite to replace it."
            )
        rgb_size = open_image_size(rgb_path)
        original_depth_size, final_depth_size = process_depth_image(
            depth_path=depth_path,
            output_path=output_path,
            rgb_size=rgb_size,
            rotate_depth=args.rotate_depth,
            resample=resample,
        )
        if final_depth_size != rgb_size:
            raise SystemExit(
                f"Output depth size mismatch for {output_path}: "
                f"expected RGB size {rgb_size}, got {final_depth_size}"
            )
        mappings.append((depth_path, output_path, original_depth_size, final_depth_size))

    print(f"Processed {len(mappings)} depth images to {output_depth_dir}")
    print("Example mappings:")
    for source, target, original_size, final_size in mappings[: max(args.examples, 0)]:
        print(f"  {source.name} -> {target.name}; {original_size} -> {final_size}")


if __name__ == "__main__":
    main()
