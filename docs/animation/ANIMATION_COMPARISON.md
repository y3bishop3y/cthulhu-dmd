# Animation Comparison

## AI-Generated Animation (Stable Video Diffusion)

**Pros:**
- Can generate realistic motion from static images
- No manual animation required

**Cons:**
- ❌ Not optimized for character walking/running
- ❌ Can produce artifacts and distortions
- ❌ Very slow on CPU (~38 minutes for 14 frames)
- ❌ Requires large model downloads (~5GB)
- ❌ Results are unpredictable

**Verdict:** Not recommended for character animations

## Simple Animation Effects (create_gif.py)

**Available Effects:**
1. **`breathing`** - Subtle zoom in/out (like breathing)
2. **`parallax`** - Horizontal movement with depth effect
3. **`zoom`** - Simple zoom in/out
4. **`rotate`** - Rotation animation
5. **`move_horizontal`** - Left-to-right movement (good for walking effect)
6. **`turn_3d`** - 3D rotation effect

**Pros:**
- ✅ Fast (seconds, not minutes)
- ✅ Predictable, controllable results
- ✅ No large dependencies
- ✅ Works well for character portraits
- ✅ `move_horizontal` can simulate walking

**Cons:**
- Less "realistic" than AI-generated motion
- Requires manual parameter tuning

**Verdict:** ✅ Recommended for character animations

## Recommendation

For character walking/running animations, use **`move_horizontal`** from `create_gif.py`:

```bash
uv run python scripts/animation/create_gif.py \
    --season season1 \
    --character rasputin \
    --image-type back \
    --coordinates "15%,17%,28%,58%" \
    --effect move_horizontal \
    --move-distance 50 \
    --fps 12 \
    --duration 3.0
```

This creates a smooth left-to-right movement that works well for character animations.

## Alternative: Hybrid Approach

You could also combine simple effects:
- Use `move_horizontal` for walking motion
- Add subtle `breathing` effect for more life
- Use `parallax` for depth

