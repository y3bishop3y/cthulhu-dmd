# Animation Scripts Directory

This directory contains scripts for generating 3D-like animations from 2D character card images. The system tests multiple animation approaches and provides comparison tools to evaluate different methods.

## Overview

The animation system extracts character portraits from card images and generates various types of animations:
- **Depth-based parallax** - 2.5D rotation effects using depth estimation
- **3D mesh generation** - Full 3D models using TripoSR
- **Novel view synthesis** - New camera angles using Zero-1-to-3
- **Human reconstruction** - PIFuHD for human-like characters
- **Video generation** - AI-generated animations using Stable Video Diffusion

## Structure

```
scripts/animation/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── extract_character.py         # Character detection & cropping
├── depth_animation.py           # Depth estimation + parallax
├── triposr_animation.py         # TripoSR 3D mesh generation
├── zero123_animation.py         # Zero-1-to-3 novel views
├── pifuhd_animation.py          # PIFuHD human reconstruction
├── svd_animation.py             # Stable Video Diffusion
├── compare_animations.py        # Comparison framework
└── utils/                       # Utility modules
    ├── __init__.py
    ├── image_utils.py           # Image preprocessing helpers
    ├── video_utils.py           # Video/GIF creation helpers
    └── metrics.py               # Quality metrics
```

## Usage

### Character Extraction

Extract and preprocess character portraits from card images:

```bash
uv run ./scripts/animation/extract_character.py \
    --character-dir data/season1/adam \
    --output-dir data/season1/adam/animation/extracted
```

### Generate Animations

Generate animations using different methods:

```bash
# Depth-based parallax (CPU-friendly)
uv run ./scripts/animation/depth_animation.py \
    --input data/season1/adam/animation/extracted/character_cropped.jpg \
    --output data/season1/adam/animation/outputs/depth_parallax.gif

# TripoSR 3D mesh (requires GPU)
uv run ./scripts/animation/triposr_animation.py \
    --input data/season1/adam/animation/extracted/character_cropped.jpg \
    --output data/season1/adam/animation/outputs/triposr_rotation.mp4

# Compare all methods
uv run ./scripts/animation/compare_animations.py \
    --character-dir data/season1/adam \
    --output-dir data/season1/adam/animation/comparison
```

## Implementation Status

See the [implementation plan](../../../memory-bank/tasks/animation/00-character-animation-plan.md) for detailed status and roadmap.

**Current Status**: ⏳ Planning Phase

- [ ] Character extraction module
- [ ] Depth estimation animation
- [ ] TripoSR integration
- [ ] Zero-1-to-3 integration
- [ ] PIFuHD integration
- [ ] Stable Video Diffusion integration
- [ ] Comparison framework

## Dependencies

### Core (Required)
- `opencv-python` - Image processing
- `pillow` - Image manipulation
- `numpy` - Array operations
- `click` - CLI interface
- `rich` - Terminal output

### ML Models (Optional, GPU Recommended)
- `torch` / `torchvision` - PyTorch backend
- `transformers` - Hugging Face transformers
- `diffusers` - Hugging Face diffusers
- `trimesh` - 3D mesh manipulation
- `imageio` / `imageio-ffmpeg` - Video/GIF creation

### Model-Specific
- `tsr` - TripoSR (if using)
- `pifuhd` - PIFuHD (if using)
- `rembg` - Background removal (optional)

## Output Structure

Animations are organized in character-specific directories:

```
data/season1/adam/animation/
├── extracted/                   # Extracted character images
│   ├── character_cropped.jpg
│   ├── character_preprocessed.png
│   └── character_no_bg.png
├── outputs/                     # Generated animations
│   ├── depth_parallax.gif
│   ├── triposr_rotation.mp4
│   ├── zero123_views.mp4
│   ├── pifuhd_rotation.mp4
│   └── svd_animation.mp4
├── meshes/                      # 3D meshes (if applicable)
│   └── triposr_mesh.obj
└── comparison/                  # Comparison results
    ├── side_by_side.mp4
    └── comparison_report.json
```

## Code Standards

All scripts follow project coding standards:

- **Pydantic Models** - All data structures use Pydantic with encapsulation
- **Type Hints** - Full type annotations throughout
- **Click CLI** - Consistent CLI interface using Click
- **Rich Output** - User-friendly terminal output with Rich
- **Error Handling** - Graceful error handling with helpful messages
- **Constants** - Use `Final[str]` for constants (no magic strings)
- **Documentation** - Comprehensive docstrings and comments

See `.cursor/rules/experts/scripts/core.mdc` for detailed coding standards.

## Examples

### Extract Character from Card

```python
from scripts.animation.extract_character import CharacterExtractor

extractor = CharacterExtractor()
character_image = extractor.extract_from_card(
    image_path=Path("data/season1/adam/front.jpg")
)
character_image.save("extracted_character.jpg")
```

### Generate Depth Animation

```python
from scripts.animation.depth_animation import DepthAnimator

animator = DepthAnimator()
animation = animator.create_rotation_animation(
    image_path=Path("character.jpg"),
    rotation_degrees=360,
    num_frames=60
)
animation.save("rotation.gif")
```

## Troubleshooting

### GPU Not Available

Some methods require GPU. The depth estimation method works on CPU as a fallback:

```bash
# This will use CPU if GPU unavailable
uv run ./scripts/animation/depth_animation.py --input character.jpg
```

### Model Download Issues

Models are downloaded automatically on first use. If downloads fail:

1. Check internet connection
2. Verify sufficient disk space
3. Check Hugging Face authentication (if using private models)

### Character Detection Issues

If character extraction fails:

1. Check image quality and format
2. Try manual cropping with `--manual-crop` option
3. Adjust detection parameters in `extract_character.py`

## Related Documentation

- [Animation Implementation Plan](../../../memory-bank/tasks/animation/00-character-animation-plan.md) - Detailed implementation plan
- [Scripts Expert Rules](../../../.cursor/rules/experts/scripts/core.mdc) - Coding standards
- [OCR Utilities](../utils/ocr.py) - Image preprocessing patterns

---

**Last Updated:** 2024-12-19

