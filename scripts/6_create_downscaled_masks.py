#!/usr/bin/env python3

"""
Generate Nerfstudio mask mipmaps.

Starting from a masks/ directory, create:
    masks_2/
    masks_4/
    masks_8/

Usage:
    python 11_create_downscaled_masks.py --masks-dir <path_to_masks>

Example:
    python create_downscaled_masks.py \
        --masks-dir nerfstudio_dataset/bauletto_nero_masks/masks
"""

import argparse
from pathlib import Path
from PIL import Image


def create_downscaled_masks(mask_dir: Path):
    scales = [2, 4, 8]

    pngs = list(mask_dir.glob("*.png"))

    if not pngs:
        print(f"No PNG files found in {mask_dir}")
        return

    for scale in scales:
        out_dir = mask_dir.parent / f"{mask_dir.name}_{scale}"
        out_dir.mkdir(exist_ok=True)

        print(f"Creating {out_dir}")

        for img_path in pngs:
            img = Image.open(img_path)

            w, h = img.size
            new_w = max(1, w // scale)
            new_h = max(1, h // scale)

            resized = img.resize(
                (new_w, new_h),
                Image.Resampling.NEAREST
            )

            resized.save(out_dir / img_path.name)

    print("Done.")


def main():
    parser = argparse.ArgumentParser(
        description="Create masks_2, masks_4 and masks_8 folders."
    )

    parser.add_argument(
        "--masks-dir",
        required=True,
        help="Path to masks directory",
    )

    args = parser.parse_args()

    create_downscaled_masks(Path(args.masks_dir))


if __name__ == "__main__":
    main()