# Poltrona Vimini Dataset

At first, a transform file was generated using all the available frames for
this object.

Since training with the full frame set was very expensive, a reduced selection
of 300 frames was later created. A dedicated subset transform JSON was then
generated for this smaller set.

The available transform variants are stored in the `transforms/` directory,
including:

- `transforms_rgb_only.json`, generated from the full dataset.
- `transforms_rgb_only_sub_set_300.json`, generated from the 300-frame subset.
- `transforms_with_masks_sub_set_300.json`, generated from the 300-frame subset
  with masks.
