# Character Animation from 2D Images - Implementation Plan

## Goal

Create a comprehensive system to generate 3D-like animations from 2D character card images, testing multiple approaches and comparing results. Focus on Adam from Season 1 as the initial test case.

## Current Context

- **Character**: Adam (Lord Adam Benchley) from Season 1
- **Available Images**: `front.jpg`, `back.jpg`, `front.webp`, `back.webp` in `data/season1/adam/`
- **Existing Infrastructure**: 
  - OpenCV, PIL/Pillow, numpy already in use
  - Image preprocessing utilities available
  - Character data structure established

## Key Questions to Answer

1. **Do we need to crop the character?**
   - Character cards likely contain text/UI elements
   - Need to isolate the character portrait for best results
   - May need automatic character detection/segmentation

2. **Which animation approach works best?**
   - Different methods have different strengths
   - Need systematic comparison
   - Quality vs. speed trade-offs

3. **What's the output format?**
   - GIF animations?
   - Video files?
   - Rotating mesh views?
   - Depth-based parallax?

## Phase 1: Image Preprocessing & Character Extraction

### 1.1 Character Detection & Cropping

**Status**: ⏳ Planned

**Approach**:
- Analyze character card layout to identify portrait region
- Use edge detection + contour analysis to find character boundaries
- Optionally use ML-based person detection (if available)
- Extract character portrait with padding

**Implementation**:
- Script: `scripts/animation/extract_character.py`
- Functions:
  - `detect_character_region(image_path: Path) -> Tuple[int, int, int, int]`
  - `crop_character(image_path: Path, bbox: Tuple) -> Image`
  - `preprocess_for_animation(image: Image) -> Image`

**Output**: 
- Cropped character images saved to `data/season1/adam/animation/`
- Both original and preprocessed versions

### 1.2 Image Quality Enhancement

**Status**: ⏳ Planned

**Enhancements**:
- Upscaling (if needed) using ESRGAN or similar
- Background removal/transparency
- Noise reduction
- Contrast enhancement

**Tools to Consider**:
- `rembg` for background removal
- `opencv` for enhancement
- `PIL` for resizing/format conversion

## Phase 2: Animation Generation Approaches

### 2.1 Approach 1: Depth Estimation + 2.5D Parallax (Simplest)

**Status**: ⏳ Planned

**Method**: 
- Estimate depth map from 2D image
- Use depth to create parallax/rotation effect
- Pseudo-3D, not true 3D reconstruction

**Libraries**:
- `transformers` - DPT (Dense Prediction Transformer) for depth estimation
- `torch` - PyTorch backend
- `opencv` - Depth map visualization and animation

**Implementation**:
- Script: `scripts/animation/depth_animation.py`
- Model: `Intel/dpt-large` or `Intel/dpt-hybrid-midas`
- Output: Rotating parallax animation (GIF/MP4)

**Pros**:
- Fastest to implement
- No GPU required (CPU inference possible)
- Good for subtle animations

**Cons**:
- Not true 3D
- Limited rotation angles
- May have artifacts

### 2.2 Approach 2: TripoSR - Image to 3D Mesh (Best Quality)

**Status**: ⏳ Planned

**Method**:
- Generate full 3D mesh from 2D image
- Export mesh (OBJ format)
- Render from multiple angles
- Create rotation animation

**Libraries**:
- `tsr` (TripoSR) - 3D mesh generation
- `trimesh` - Mesh manipulation and rendering
- `pyrender` or `blender-python` - Rendering

**Implementation**:
- Script: `scripts/animation/triposr_animation.py`
- Model: `stabilityai/TripoSR`
- Output: 3D mesh + rendered rotation animation

**Pros**:
- Highest quality 3D reconstruction
- True 3D model (can export/use elsewhere)
- Smooth rotation from any angle

**Cons**:
- Requires GPU (CUDA)
- Slower generation
- Larger model size

### 2.3 Approach 3: Zero-1-to-3 - Novel View Synthesis

**Status**: ⏳ Planned

**Method**:
- Generate new views of character at different angles
- Use diffusion model conditioned on rotation
- Combine views into animation

**Libraries**:
- `diffusers` - Hugging Face diffusers
- `torch` - PyTorch
- `transformers` - Model loading

**Implementation**:
- Script: `scripts/animation/zero123_animation.py`
- Model: `stabilityai/zero123-xl` or similar
- Output: Multi-view animation

**Pros**:
- Good quality novel views
- Flexible angle control
- Can generate multiple frames

**Cons**:
- Requires GPU
- May have inconsistencies between frames
- Slower than depth estimation

### 2.4 Approach 4: PIFuHD - Human Character Reconstruction

**Status**: ⏳ Planned (If character is human-like)

**Method**:
- Specifically designed for human characters
- Creates full 3D model of person
- High quality for human figures

**Libraries**:
- `pifuhd` - Facebook Research PIFuHD
- `torch` - PyTorch

**Implementation**:
- Script: `scripts/animation/pifuhd_animation.py`
- Output: 3D human model + animation

**Pros**:
- Excellent for human characters
- High detail
- Well-established method

**Cons**:
- Only works for human-like characters
- Requires GPU
- More complex setup

### 2.5 Approach 5: Stable Video Diffusion - AI-Generated Animation

**Status**: ⏳ Planned

**Method**:
- Generate video frames from single image
- Can condition on camera motion
- Creates smooth animation

**Libraries**:
- `diffusers` - Stable Video Diffusion
- `torch` - PyTorch

**Implementation**:
- Script: `scripts/animation/svd_animation.py`
- Model: `stabilityai/stable-video-diffusion-img2vid`
- Output: Video animation

**Pros**:
- Smooth animations
- Can add motion effects
- Good for general objects

**Cons**:
- Less control over rotation
- May add unwanted motion
- Requires GPU

## Phase 3: Comparison Framework

### 3.1 Animation Comparison Script

**Status**: ⏳ Planned

**Purpose**: 
- Generate animations using all approaches
- Compare quality, speed, artifacts
- Generate side-by-side comparison

**Implementation**:
- Script: `scripts/animation/compare_animations.py`
- Features:
  - Run all animation methods
  - Measure generation time
  - Assess visual quality (subjective + metrics)
  - Create comparison grid/video
  - Generate report

**Output**:
- Individual animations in `data/season1/adam/animation/outputs/`
- Comparison video/grid
- Comparison report (JSON/Markdown)

### 3.2 Quality Metrics

**Status**: ⏳ Planned

**Metrics to Track**:
- Generation time (per frame, total)
- File size (output)
- Visual artifacts (subjective scoring)
- Smoothness (frame-to-frame consistency)
- 3D realism (if applicable)
- Rotation range (degrees possible)

**Tools**:
- `opencv` for video analysis
- `imageio` for GIF/video handling
- Custom metrics functions

## Phase 4: Script Structure

### Directory Structure

```
scripts/animation/
├── __init__.py
├── extract_character.py          # Character detection & cropping
├── depth_animation.py             # Approach 1: Depth estimation
├── triposr_animation.py           # Approach 2: TripoSR
├── zero123_animation.py           # Approach 3: Zero-1-to-3
├── pifuhd_animation.py            # Approach 4: PIFuHD
├── svd_animation.py                # Approach 5: Stable Video Diffusion
├── compare_animations.py           # Comparison framework
└── utils/
    ├── __init__.py
    ├── image_utils.py              # Image preprocessing helpers
    ├── video_utils.py              # Video/GIF creation helpers
    └── metrics.py                  # Quality metrics
```

### Output Structure

```
data/season1/adam/animation/
├── extracted/
│   ├── character_cropped.jpg
│   ├── character_preprocessed.png
│   └── character_no_bg.png
├── outputs/
│   ├── depth_parallax.gif
│   ├── triposr_rotation.mp4
│   ├── zero123_views.mp4
│   ├── pifuhd_rotation.mp4
│   └── svd_animation.mp4
├── meshes/                         # 3D meshes (if applicable)
│   └── triposr_mesh.obj
└── comparison/
    ├── side_by_side.mp4
    └── comparison_report.json
```

## Phase 5: Dependencies & Setup

### New Dependencies Needed

**Core Animation Libraries**:
- `torch` / `torchvision` - PyTorch (for ML models)
- `transformers` - Hugging Face transformers (for depth/zero123)
- `diffusers` - Hugging Face diffusers (for SVD/Zero123)
- `trimesh` - 3D mesh manipulation
- `imageio` / `imageio-ffmpeg` - Video/GIF creation
- `rembg` - Background removal (optional)

**3D-Specific**:
- `tsr` - TripoSR (if using)
- `pifuhd` - PIFuHD (if using)

**Rendering** (choose one):
- `pyrender` - Python renderer
- `blender-python` - Blender integration (more powerful)

### Installation Strategy

1. **GPU Support**: Check for CUDA availability
2. **Model Downloads**: Cache models locally
3. **Optional Dependencies**: Make GPU-required features optional
4. **Fallback**: CPU-only depth estimation as baseline

## Phase 6: Implementation Order

### Step 1: Character Extraction (Foundation)
1. Implement `extract_character.py`
2. Test on Adam's front image
3. Validate cropping quality
4. Add preprocessing options

### Step 2: Depth Estimation (Quick Win)
1. Implement `depth_animation.py`
2. Test depth map generation
3. Create simple rotation animation
4. Validate output quality

### Step 3: Comparison Framework
1. Implement `compare_animations.py` skeleton
2. Add timing/metrics collection
3. Create comparison visualization

### Step 4: Advanced Methods (GPU Required)
1. Implement TripoSR (if GPU available)
2. Implement Zero-1-to-3
3. Implement Stable Video Diffusion
4. Add PIFuHD if character is human-like

### Step 5: Refinement
1. Optimize parameters for each method
2. Improve character extraction
3. Add more quality metrics
4. Create comprehensive comparison report

## Phase 7: Testing Strategy

### Test Cases

1. **Adam (Season 1)** - Initial test case
2. **Other Season 1 Characters** - Validate generalization
3. **Different Image Qualities** - Test robustness

### Validation

- Visual inspection of outputs
- Comparison with ground truth (if available)
- Performance benchmarking
- Artifact detection

## Phase 8: Documentation

### Documentation Needed

1. **README** - Usage instructions
2. **Method Comparison** - Pros/cons of each approach
3. **Installation Guide** - GPU setup, dependencies
4. **Parameter Tuning** - How to adjust for best results
5. **Troubleshooting** - Common issues and solutions

## Success Criteria

- ✅ Successfully extract character from card image
- ✅ Generate at least 3 different animation types
- ✅ Create comparison framework
- ✅ Document results and recommendations
- ✅ Scripts are reusable for other characters

## Open Questions

1. **Character Type**: Is Adam human-like enough for PIFuHD?
2. **GPU Availability**: Do we have GPU access? (affects which methods are feasible)
3. **Output Format Preference**: GIF vs MP4 vs both?
4. **Animation Length**: How many frames/rotation degrees?
5. **Background**: Remove background or keep it?

## Next Steps

1. Review this plan
2. Answer open questions
3. Set up development environment
4. Begin Phase 1 implementation

