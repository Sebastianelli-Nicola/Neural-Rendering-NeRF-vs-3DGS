# Neural Rendering of Woven Artifacts: Comparative Analysis of NeRF and 3D Gaussian Splatting

[![Framework: Nerfstudio](https://img.shields.io/badge/Framework-Nerfstudio-blue.svg)](#software-stack--tooling)
[![Method: NeRF vs 3DGS](https://img.shields.io/badge/Method-NeRF_%7C_3DGS-orange.svg)](#theoretical-foundations)
[![Course: Computer Graphics](https://img.shields.io/badge/Course-Computer_Graphics_%26_Multimedia-003366.svg)](#authors--academic-context)
[![Datasets: Woven Handcrafts](https://img.shields.io/badge/Domain-Woven_Crafts_(Bottega_Intreccio)-green.svg)](#experimental-benchmark--tested-artifacts)
[![Report: PDF](https://img.shields.io/badge/Report-PDF_(ITA)-red.svg)](./docs/relazione_nerfstudio.pdf)
[![Slides: PDF](https://img.shields.io/badge/Slides-PDF_(ITA)-yellow.svg)](./docs/presentazione_nerfstudio.pdf)

End-to-end 3D digitization and comparative benchmark evaluating **Neural Radiance Fields (NeRF)** and **3D Gaussian Splatting (3DGS)** on complex woven artisanal objects, carried out in collaboration with *Bottega Intreccio*.

Developed for the *Computer Graphics & Multimedia* Master's course at **Università Politecnica delle Marche (UNIVPM)** (A.Y. 2024/2025).

> Project Deliverables & Reports:
> * Technical Report (PDF, Italian): [relazione_nerfstudio.pdf](./docs/relazione_nerfstudio.pdf)
> * Presentation Slides (PDF, Italian): [presentazione_nerfstudio.pdf](./docs/presentazione_nerfstudio.pdf)
> * 360° Orbital Video Renders: [video/](./video/)
> * Original Group Development Repository: [fppcng/nerfstudio-project](https://github.com/fppcng/nerfstudio-project)

---

## Project Overview & Challenges

Digitizing handcrafted woven artifacts represents an open challenge for photogrammetry and neural volumetric reconstruction due to:
* **Thin Geometries:** Intricate yarn, wicker strands, and fine woven patterns that challenge ray sampling and point initialization.
* **Severe Self-Occlusions & Cavities:** Hollow interiors and recurrent micro-holes that obscure continuous surfaces.
* **Repetitive Textures:** High-frequency visual symmetries that impede Structure-from-Motion (SfM) feature matching.
* **View-Dependent Reflections:** Specular highlights across polished cane and synthetic fibers.

This project establishes a standardized pipeline within **Nerfstudio** to ingest raw multi-view captures (HEIF RGB images, LiDAR depth maps, camera parameters) and evaluates volumetric implicit representations against explicit rasterized primitives.

---

## Theoretical Foundations

### 1. Neural Radiance Fields (NeRF)
NeRF models the scene as a continuous implicit function parameterized by a multi-layer perceptron (MLP):

$$F_\Theta: (\mathbf{x}, \mathbf{d}) \to (\mathbf{c}, \sigma)$$

Given a 3D coordinate $\mathbf{x} = (x, y, z)$ and viewing direction $\mathbf{d} = (\theta, \phi)$, the network predicts RGB color $\mathbf{c}$ and volume density $\sigma$. Image formation relies on numerical quadrature along camera rays:

$$C(\mathbf{r}) = \sum_{i=1}^{N} T_i (1 - \exp(-\sigma_i \delta_i)) \mathbf{c}_i, \quad T_i = \exp\left(-\sum_{j=1}^{i-1} \sigma_j \delta_j\right)$$

* Implementations Evaluated: `nerfacto` (RGB baseline) and `depth-nerfacto` (depth-supervised with LiDAR loss).

### 2. 3D Gaussian Splatting (3DGS)
3DGS discards neural network evaluations in favor of explicit 3D Gaussian primitives initialized from sparse SfM point clouds:

$$G(\mathbf{x}) = \exp\left(-\frac{1}{2} (\mathbf{x} - \boldsymbol{\mu})^T \boldsymbol{\Sigma}^{-1} (\mathbf{x} - \boldsymbol{\mu})\right)$$

Each primitive maintains centroid $\boldsymbol{\mu}$, anisotropic covariance $\boldsymbol{\Sigma} = \mathbf{R} \mathbf{S} \mathbf{S}^T \mathbf{R}^T$ (scaling $\mathbf{S}$, rotation $\mathbf{R}$ via quaternions), opacity $\alpha$, and spherical harmonics coefficients for view-dependent radiance.
* Rendering Mechanism: High-throughput differentiable tile-based rasterization (alpha-blending ordered splats directly on the image plane) achieving real-time frame rates ($>30\text{ FPS}$).
* Implementations Evaluated: `splatfacto` and `splatfacto-big`.

---

## Reconstruction Pipeline

```
[Raw Scanner / Mobile Capture]
        │
        ├── RGB Photos (HEIF) ──> [Format Conversion] ──> PNG (Maintained Resolution)
        │                                                     │
        ├── Depth Maps (PNG)  ──> [Rotate 90° CW + Scale] ──> Alignment / Downscaling
        │                                                     │
        └── Camera JSONs      ──> [COLMAP SfM / Ingestion] ─> transforms.json
                                                              │
                                       ┌──────────────────────┴──────────────────────┐
                                       ▼                                             ▼
                             [Nerfstudio Training]                         [Object Segmentation]
                        (nerfacto / depth / splatfacto)                   (YOLO-World + SAM Masks)
                                       │
                                       ▼
                       [Quantitative & Visual Benchmarking]
                       Full-Ref: PSNR, SSIM, LPIPS, Depth MSE
                       No-Ref:   BRISQUE, CLIP-IQA, Rendering FPS
```

1. **Format Ingestion & Conversion:** Batch-converted Apple HEIF captures into lossless PNG preserving native sensor resolution.
2. **LiDAR Depth Map Alignment:** Addressed sensor aspect ratio discrepancies by rotating depth frames $90^\circ$ clockwise and generating resolution-matched downscaled versions (`depths_2/`, `depths_4/`).
3. **Geometric Registration:**
   * Handled coordinate frame remapping (OpenCV/COLMAP convention vs. iOS world coordinates) and normalized focal lengths $(f_x, f_y)$ and principal points $(c_x, c_y)$ into absolute pixel units.
   * Built unified `transforms.json` incorporating camera extrinsics and intrinsics.
4. **Foreground Object Masking:** Segmented targets from complex background environments using a two-stage promptable pipeline (**YOLO-World** bounding box detection + **Segment Anything Model (SAM)** mask generation).

---

## Experimental Benchmark & Tested Artifacts

The pipeline was executed across three woven objects exhibiting varying geometric structural complexity:
1. **Bauletto Nero (Black Woven Handbag):** Dense, dark synthetic crochet weave; prone to high absorption and depth ambiguity.
2. **Cestino Medio (Woven Basket with Leather Handle):** Regular natural wicker weaving with metallic clasp and leather textures.
3. **Poltrona in Vimini (Wicker Armchair):** Openwork wicker framework with pronounced gaps, hollow curved ribs, and high self-occlusion.

---

## Quantitative Results

Evaluations were performed across **Full-Reference metrics** (PSNR $\uparrow$, SSIM $\uparrow$, LPIPS $\downarrow$, Depth MSE $\downarrow$) and **No-Reference perceptual quality metrics** (BRISQUE $\downarrow$, CLIP-IQA $\uparrow$, Frame Rates).

### 1. Bauletto Nero (Black Bag) Benchmark

| Model Configuration | Iterations | PSNR (dB) $\uparrow$ | SSIM $\uparrow$ | LPIPS $\downarrow$ | FPS $\uparrow$ | BRISQUE $\downarrow$ | CLIP-IQA $\uparrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `nerfacto` (RGB) | 100k | 17.41 | 0.66 | 0.40 | 0.41 | 28.94 | 0.23 |
| `depth-nerfacto` (LiDAR) | 100k | 19.17 | 0.67 | 0.38 | 0.42 | 27.51 | 0.25 |
| `splatfacto` (3DGS) | 100k | 22.45 | 0.82 | 0.32 | **37.18** | 30.58 | **0.37** |
| `splatfacto` (3DGS) | 200k | 22.73 | 0.83 | 0.32 | 36.06 | 30.58 | **0.37** |
| `splatfacto-big` (3DGS) | 100k | **23.31** | **0.84** | **0.28** | 29.07 | **26.78** | **0.37** |

### 2. Cestino Medio (Basket) Benchmark

| Model Configuration | Iterations | PSNR (dB) $\uparrow$ | SSIM $\uparrow$ | LPIPS $\downarrow$ | FPS $\uparrow$ | BRISQUE $\downarrow$ | CLIP-IQA $\uparrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `nerfacto` | 100k | 16.21 | 0.54 | 0.41 | 0.39 | **38.28** | 0.33 |
| `splatfacto` | 100k | **21.91** | **0.80** | **0.28** | **28.87** | 43.78 | **0.45** |
| `splatfacto-big` | 100k | 19.27 | 0.74 | 0.35 | 20.06 | 39.87 | **0.45** |

### 3. Poltrona in Vimini (Armchair) Benchmark

| Model Configuration | Iterations | PSNR (dB) $\uparrow$ | SSIM $\uparrow$ | LPIPS $\downarrow$ | FPS $\uparrow$ | BRISQUE $\downarrow$ | CLIP-IQA $\uparrow$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `nerfacto` (300-subset) | 100k | 16.37 | 0.55 | 0.47 | 0.39 | 33.99 | **0.64** |
| `splatfacto` | 100k | **20.57** | **0.71** | 0.37 | **33.85** | 33.95 | 0.61 |
| `splatfacto-big` | 100k | 20.35 | 0.70 | **0.34** | 25.21 | **31.62** | 0.62 |

---

## 360° Video Demos

Demonstrative $360^\circ$ orbital renderings, generated using 3D Gaussian Splatting (`splatfacto` at 100k iterations), are available in the video folder:
* Bauletto Nero (Black Bag) Demo: [video/bauletto_splatfacto_100k_video.mp4](./video/bauletto_splatfacto_100k_video.mp4)
* Poltrona in Vimini (Wicker Armchair) Demo: [video/poltrona_splatfacto_100k_video.mp4](./video/poltrona_splatfacto_100k_video.mp4)

---

## Key Findings & Critical Analysis

* **Rendering Efficiency:** 3D Gaussian Splatting (`splatfacto`) consistently achieved real-time throughput (~28–38 FPS), rendering orders of magnitude faster than volumetric NeRF raymarching (~0.4 FPS).
* **Reconstruction Quality:** 3DGS outperformed NeRF across all objects in image fidelity (+4 to +6 dB PSNR gain and +0.15 to +0.20 higher SSIM).
* **LiDAR Depth Supervision:** In NeRF architectures, integrating depth maps (`depth-nerfacto`) provided strong geometric regularization, improving PSNR from 17.41 dB to 19.17 dB on dark, ambiguous surfaces.
* **Failure Modes on Thin Struts:** On the wicker armchair, repetitive patterns and thin circular canes caused COLMAP feature tracking to drop >400 candidate camera poses, creating visible floater artifacts in regions with sparse ray intersection.

---

## Software Stack & Tooling

* **Framework:** Nerfstudio (v1.0+)
* **Volumetric & Splat Engines:** `nerfacto`, `depth-nerfacto`, `splatfacto`, `gsplat`
* **Structure-from-Motion (SfM):** COLMAP
* **Zero-Shot Segmentation:** YOLO-World, Segment Anything Model (SAM)
* **Languages & Core Libraries:** Python 3.9+, PyTorch, TorchVision, NumPy, OpenCV, Pillow

---

## Authors & Academic Context

Master's degree project for **Computer Graphics & Multimedia** (A.Y. 2025/2026) — M.Sc. in Computer and Automation Engineering at **Università Politecnica delle Marche (UNIVPM)**.

* **Nicola Sebastianelli** — [GitHub](https://github.com/Sebastianelli-Nicola)
* **Filippo Cingolani**
* **Alessandro Pettinari**
* *Industrial Partner:* Bottega Intreccio
