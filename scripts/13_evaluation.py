#!/usr/bin/env python3
"""Collect Nerfstudio eval metrics and optional no-reference image metrics."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_DATA = REPO_ROOT / "project_data"
DEFAULT_EVAL_DIR = PROJECT_DATA / "evals"
DEFAULT_RENDER_DIR = PROJECT_DATA / "renders"
DEFAULT_OUTPUT = PROJECT_DATA / "results" / "raw_results.csv"

RESULT_COLUMNS = [
    "model",
    "psnr",
    "psnr_std",
    "ssim",
    "ssim_std",
    "lpips",
    "lpips_std",
    "num_rays_per_sec",
    "num_rays_per_sec_std",
    "fps",
    "fps_std",
    "depth_mse",
    "depth_mse_std",
    "brisque_mean",
    "clip_iqa_mean",
    "render_num",
]


def load_no_reference_tools(device_name: str | None) -> tuple[Any, Any, Any, Any]:
    try:
        import piq
        import torch
        from torchvision import transforms
    except ImportError as error:
        raise RuntimeError(
            "Missing dependencies for BRISQUE/CLIP-IQA. "
            "Install scripts/requirements.txt or use --skip-no-reference."
        ) from error

    if device_name:
        device = torch.device(device_name)
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        device = torch.device("mps")
    else:
        device = torch.device("cpu")

    clipiqa_metric = piq.CLIPIQA().to(device)
    clipiqa_metric.eval()

    return piq, torch, transforms, (device, clipiqa_metric)


def image_files(render_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in render_dir.iterdir()
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg"}
    )


def calculate_no_reference_metrics(
    render_dir: Path,
    piq: Any,
    torch: Any,
    transforms: Any,
    device: Any,
    clipiqa_metric: Any,
    size: tuple[int, int] = (512, 512),
) -> tuple[float | None, float | None, int]:
    if not render_dir.is_dir():
        print(f"[INFO] Render directory not found: {render_dir}")
        return None, None, 0

    images = image_files(render_dir)
    render_num = len(images)

    if render_num == 0:
        print(f"[INFO] No images found in: {render_dir}")
        return None, None, 0

    transform = transforms.Compose(
        [
            transforms.Resize(size),
            transforms.ToTensor(),
        ]
    )

    brisque_scores: list[float] = []
    clipiqa_scores: list[float] = []

    print(f"[INFO] Computing no-reference metrics on {render_num} images: {render_dir}")

    for index, image_path in enumerate(images, start=1):
        try:
            image = Image.open(image_path).convert("RGB")
            tensor = transform(image).unsqueeze(0).to(device)
        except Exception as error:
            print(f"  [!] Could not load {image_path.name}: {error}")
            continue

        try:
            with torch.no_grad():
                brisque_scores.append(float(piq.brisque(tensor, data_range=1.0).item()))
        except Exception as error:
            print(f"  [BRISQUE] Skipped {image_path.name}: {error}")

        try:
            with torch.no_grad():
                clipiqa_scores.append(float(clipiqa_metric(tensor).item()))
        except Exception as error:
            print(f"  [CLIP-IQA] Skipped {image_path.name}: {error}")

        if index % 10 == 0 or index == render_num:
            print(f"  Processed {index}/{render_num} images")

    brisque_mean = float(np.mean(brisque_scores)) if brisque_scores else None
    clipiqa_mean = float(np.mean(clipiqa_scores)) if clipiqa_scores else None

    return brisque_mean, clipiqa_mean, render_num


def read_eval(eval_path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(eval_path.read_text(encoding="utf-8"))
    except Exception as error:
        print(f"[!] Could not read {eval_path}: {error}")
        return None


def collect_results(
    eval_dir: Path,
    render_dir: Path,
    skip_no_reference: bool,
    device_name: str | None,
) -> list[dict[str, Any]]:
    if not eval_dir.is_dir():
        raise FileNotFoundError(f"Eval directory not found: {eval_dir}")

    metric_tools = None
    if not skip_no_reference:
        piq, torch, transforms, metric_state = load_no_reference_tools(device_name)
        device, clipiqa_metric = metric_state
        metric_tools = (piq, torch, transforms, device, clipiqa_metric)
        print(f"[INFO] No-reference metrics device: {device}")

    results: list[dict[str, Any]] = []

    for eval_path in sorted(eval_dir.glob("*.json")):
        model_eval = read_eval(eval_path)
        if model_eval is None:
            continue

        eval_results = model_eval.get("results", {})
        experiment_name = model_eval.get("experiment_name") or eval_path.stem.removesuffix("_eval")

        result = {
            "model": experiment_name,
            "psnr": eval_results.get("psnr"),
            "psnr_std": eval_results.get("psnr_std"),
            "ssim": eval_results.get("ssim"),
            "ssim_std": eval_results.get("ssim_std"),
            "lpips": eval_results.get("lpips"),
            "lpips_std": eval_results.get("lpips_std"),
            "num_rays_per_sec": eval_results.get("num_rays_per_sec"),
            "num_rays_per_sec_std": eval_results.get("num_rays_per_sec_std"),
            "fps": eval_results.get("fps"),
            "fps_std": eval_results.get("fps_std"),
            "depth_mse": eval_results.get("depth_mse"),
            "depth_mse_std": eval_results.get("depth_mse_std"),
        }

        if metric_tools is None:
            brisque_mean, clipiqa_mean, render_num = None, None, 0
        else:
            experiment_render_dir = render_dir / experiment_name / "test" / "rgb"
            brisque_mean, clipiqa_mean, render_num = calculate_no_reference_metrics(
                experiment_render_dir,
                *metric_tools,
            )

        result["brisque_mean"] = brisque_mean
        result["clip_iqa_mean"] = clipiqa_mean
        result["render_num"] = render_num
        results.append(result)

    return results


def write_results(results: list[dict[str, Any]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(results, columns=RESULT_COLUMNS)
    df.to_csv(output_path, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a CSV with metrics from project_data/evals and project_data/renders."
    )
    parser.add_argument("--eval-dir", type=Path, default=DEFAULT_EVAL_DIR)
    parser.add_argument("--render-dir", type=Path, default=DEFAULT_RENDER_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--skip-no-reference",
        action="store_true",
        help="Do not compute BRISQUE/CLIP-IQA on rendered images.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "mps"),
        help="Device to use for BRISQUE/CLIP-IQA. Default: auto.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results = collect_results(
        eval_dir=args.eval_dir,
        render_dir=args.render_dir,
        skip_no_reference=args.skip_no_reference,
        device_name=args.device,
    )

    if not results:
        print("[INFO] No results to save.")
        return

    write_results(results, args.output)
    print(f"[INFO] Saved {len(results)} models to: {args.output}")


if __name__ == "__main__":
    main()
