# Nerfstudio Dataset

This directory contains the Nerfstudio-ready datasets used for the different
objects and experiments in the project.

The complete datasets are large, so the public GitHub repository only keeps the
lightweight transform JSON files and dataset notes. Image folders, depth maps,
masks, COLMAP outputs, sparse point clouds, and other generated dataset assets
are intentionally excluded from version control.

Each object directory contains the data needed by Nerfstudio, typically:

- `images/` and the downscaled `images_2/`, `images_4/`, `images_8/`
  directories generated with `ns data` and COLMAP.
- `colmap/`, `sparse_pc.ply`, and the base reconstruction files produced by
  the Nerfstudio/COLMAP pipeline.
- `depths/` and the downscaled `depths_2/`, `depths_4/`, `depths_8/`
  directories, when available. These were generated with the dedicated depth
  scripts.
- `masks/` and the downscaled `masks_2/`, `masks_4/`, `masks_8/`
  directories, when available. These were generated with the dedicated mask
  scripts.
- `transforms.json`, the transform file currently used by Nerfstudio for that
  object or experiment.

Object directories also contain a `transforms/` folder. This folder stores
the different transform variants prepared for that object. When a specific
transform variant has to be used for an experiment, copy or move that file into
the root of the corresponding object directory and rename it to
`transforms.json`.

For example, to use a transform variant for `bauletto_nero`, the selected file
from `bauletto_nero/transforms/` must be placed directly inside
`bauletto_nero/` as:

```text
project_data/nerfstudio_dataset/bauletto_nero/transforms.json
```

Nerfstudio will then read that `transforms.json` together with the images,
depth maps, masks, and COLMAP data available in the same object directory.
