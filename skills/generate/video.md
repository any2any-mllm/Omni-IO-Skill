# Skill: Video Generation

## Trigger

The `declare` block contains a task with `type: "video"`.

---

## Tool

**Default: Wan2.7 (DashScope)**, using the Wan video-generation API  
**Alternative: Kling 1.6 via fal.ai** (higher quality)

- Configuration: `config.yaml → generate.video`
- Required API key: `WAN_API_KEY` for the default Wan2.7 provider, or `FAL_API_KEY` after switching to Kling 1.6
- Call: MCP tool `generate_video(prompt, duration_seconds, aspect_ratio, first_frame_url?)`
- **Important Kling-only limitation:** Kling accepts only two durations: values with `duration_seconds >= 8` are rounded to 10 seconds; all others are rounded to 5 seconds. It also accepts only two aspect ratios: `"16:9"` remains unchanged, while every other value becomes `"9:16"`. The provider rewrites these values **silently** without error and does not use the originally requested values. Fine-grained duration and aspect-ratio control is therefore unavailable with Kling. Use the actual values in `params_used` to describe the result instead of copying the request. The default Wan2.7 provider has no such limitation and passes `duration_seconds` and `aspect_ratio` through as requested.

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `prompt` | `declare` block | Complete video description. Wan2.7 can synthesize audio—environmental sound, lip-synced dialogue, and background music—in the same generation from the text prompt. To include sound, describe the desired audio in `prompt`; no separate audio parameter is needed. |
| `duration_seconds` | `declare.params` or configuration default | Video duration in seconds |
| `first_frame_url` | Injected from upstream when depending on an image | Automatically injected from the completed upstream image as the video's first frame |
| `aspect_ratio` | `declare.params` or configuration default | Video aspect ratio |

---

## Procedure

1. **Resolve parameters:** Read the prompt, duration, and aspect ratio and fill missing values from the configuration defaults.
2. **Check the first frame:** If the task depends on an upstream image, wait for it and obtain `first_frame_url` from its result.
3. **Call the API:** Send the request to Wan2.7 by default or Kling 1.6 after switching.
   - Pass the prompt, duration, and aspect ratio.
   - Add `first_frame_url` when present.
4. **Poll:** Video generation is asynchronous. Poll until the status progresses from `pending` to `processing` to `completed`.
5. **Process the result:** Retrieve the video file URL.
6. **Return status:** Record the result as an `output_format` asset object and write it to the asset registry.

---

## Output Format

```json
{
  "task_id": "vid1",
  "type": "video",
  "asset_id": "vid_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/vid_c7f1a9.mp4",
  "description": "A generated {duration}-second {scene description} video, with {first-frame description} and {camera movement}.",
  "params_used": { "duration_seconds": 10, "aspect_ratio": "16:9", "provider": "wan" },
  "depends_on": "img1",
  "completed_at": 1749520105
}
```

`url` is a local file path under `OMNI_OUTPUT_DIR`, not an HTTP URL.

---

## Defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration_seconds` | `10` | Video duration in seconds |
| `aspect_ratio` | `"16:9"` | Landscape |

---

## Integration with Other Skills

- **Upstream image through `depends_on`:** Use the upstream image URL as the first frame to preserve visual continuity.
- **Video Producer Expert:** For a complete video requiring multiple shots, narration, music, subtitles, and final-video review, do not stack several `video` tasks and assemble them ad hoc. Use `expert/video-producer/video-producer.md`. The Expert still uses this tool for individual shots. Only when custom narration/music is needed does assembly remove Wan2.7's native audio and replace it with a `speech`/`music` mix.

---

## Error Handling

| Error | Handling |
|-------|----------|
| API key not configured | Ask the user to set `WAN_API_KEY`, or switch to Kling and set `FAL_API_KEY` |
| Generation exceeds `max_wait_seconds` | Mark `failed` and ask the user to retry or reduce the duration |
| Incompatible first-frame image | Omit the first-frame constraint, fall back to text-to-video, and notify the user |
| API unavailable | Mark `failed` and ask the user to check the service status |
