# AI Animation Tools for 2D Character Animation

## Open-Source AI Tools for Image-to-Video Animation

### 1. **Stable Video Diffusion** (Recommended)
- **What it does**: Converts static images to short video clips
- **Open Source**: Yes (Stability AI)
- **Python Library**: `diffusers` (Hugging Face)
- **Model**: `stabilityai/stable-video-diffusion-img2vid` or `stabilityai/stable-video-diffusion-img2vid-xt`
- **Requirements**: GPU recommended (CUDA), but can run on CPU (slower)
- **Use Case**: Can animate static character images with motion

**Installation**:
```bash
pip install diffusers transformers accelerate torch torchvision
```

**Pros**:
- High quality video generation
- Good for general motion/animation
- Well-documented
- Active development

**Cons**:
- May not specifically create walking cycles
- Requires GPU for best performance
- Can be slow on CPU

### 2. **AnimateDiff**
- **What it does**: Image-to-video generation with motion control
- **Open Source**: Yes
- **Python Library**: `diffusers` or `animatediff-cli-prompt-travel`
- **Model**: Various community models available
- **Requirements**: GPU recommended

**Pros**:
- Good motion control
- Can condition on motion prompts
- Active community

**Cons**:
- Less specifically for character animation
- May require fine-tuning for walking cycles

### 3. **OpenPose + Animation**
- **What it does**: Extracts skeletal keypoints from images, can be used to drive animations
- **Open Source**: Yes (CMU)
- **Python Library**: `openpose-python` or `mediapipe`
- **Use Case**: Extract pose data, then use it to animate character

**Pros**:
- Can extract pose information
- Useful for rigging-based animation
- Real-time capable

**Cons**:
- Requires additional animation pipeline
- Not direct image-to-animation

### 4. **ControlNet + Video Generation**
- **What it does**: Controlled image generation, can be extended to video
- **Open Source**: Yes
- **Python Library**: `controlnet-aux`, `diffusers`
- **Use Case**: More control over generated animations

## Recommended Approach

For your use case (animating character cards), I recommend:

1. **Start with Stable Video Diffusion** - Best balance of quality and ease of use
2. **Use motion conditioning** - Can prompt for "walking" or "running" motion
3. **Post-process** - Extract frames and create GIF

## Implementation Options

I can create a script that:
- Uses Stable Video Diffusion to generate video from character image
- Conditions on motion prompts (walking, running, etc.)
- Converts video frames to animated GIF
- Handles GPU/CPU fallback

Would you like me to implement this?

