import argparse
import json
import random
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Create a subset transforms.json for Nerfstudio."
    )
    parser.add_argument("--input", required=True, help="Path to original transforms.json")
    parser.add_argument("--output", required=True, help="Path to new subset transforms.json")
    parser.add_argument("--num-images", type=int, default=None, help="Number of images to keep")
    parser.add_argument("--step", type=int, default=None, help="Keep one image every N frames")
    parser.add_argument("--random", action="store_true", help="Randomly sample frames")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    with open(input_path, "r") as f:
        data = json.load(f)

    frames = data["frames"]
    total = len(frames)

    if args.step is not None:
        selected_frames = frames[::args.step]
    elif args.num_images is not None:
        if args.num_images > total:
            raise ValueError(f"num-images={args.num_images} is greater than total frames={total}")

        if args.random:
            random.seed(args.seed)
            selected_frames = random.sample(frames, args.num_images)
            selected_frames = sorted(
                selected_frames,
                key=lambda x: x.get("colmap_im_id", x.get("file_path", ""))
            )
        else:
            step = total / args.num_images
            indices = [int(i * step) for i in range(args.num_images)]
            selected_frames = [frames[i] for i in indices]
    else:
        raise ValueError("Use either --num-images or --step")

    data["frames"] = selected_frames

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=4)

    print(f"Original frames: {total}")
    print(f"Selected frames: {len(selected_frames)}")
    print(f"Saved subset JSON to: {output_path}")


if __name__ == "__main__":
    main()