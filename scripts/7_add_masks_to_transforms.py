#!/usr/bin/env python3

"""
Add Nerfstudio mask annotations to transforms.json.

This script creates a new transforms file where each frame contains
a mask_path entry pointing to the corresponding segmentation mask.

Typical use case:
    1. Generate masks in masks/
    2. Create masks_2/, masks_4/, masks_8/
    3. Add mask_path entries to transforms.json
    4. Train Nerfacto or Splatfacto using the masked dataset

Usage:
    python 10_add_masks_to_transforms.py \
        --input transforms.json \
        --mask-dir masks

Output:
    transforms_mask.json
"""

import json
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Add mask_path entries to a Nerfstudio transforms.json file."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to original transforms.json",
    )

    parser.add_argument(
        "--output",
        default=None,
        help="Path to output transforms_mask.json",
    )

    parser.add_argument(
        "--mask-dir",
        default="masks",
        help="Mask directory relative to the dataset root",
    )

    parser.add_argument(
        "--check-exists",
        action="store_true",
        help="Check that every mask file exists",
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if args.output is None:
        output_path = input_path.parent / "transforms_mask.json"
    else:
        output_path = Path(args.output)

    dataset_root = input_path.parent

    with open(input_path, "r", encoding="utf-8") as f:
        transforms = json.load(f)

    missing_masks = []

    for frame in transforms["frames"]:
        image_path = Path(frame["file_path"])
        image_name = image_path.name

        mask_path = Path(args.mask_dir) / image_name
        frame["mask_path"] = str(mask_path).replace("\\", "/")

        if args.check_exists:
            full_mask_path = dataset_root / mask_path
            if not full_mask_path.exists():
                missing_masks.append(str(mask_path))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(transforms, f, indent=4)

    print(f"Saved: {output_path}")
    print(f"Frames updated: {len(transforms['frames'])}")

    if missing_masks:
        print("\nMissing masks:")
        for mask in missing_masks:
            print(mask)


if __name__ == "__main__":
    main()