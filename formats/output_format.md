# Output Format Specification

This file defines the structured format Claude uses to aggregate results after each turn.

It mirrors `input_format.md`: `input_format` assembles the user's multimodal input into structured JSON, while `output_format` assembles the results of every generation task in the current turn into structured JSON for Claude to present. This format provides complete structured result data; Claude decides how to present it based on context.

---

## Overall Structure

```json
{
  "turn_id": "{current turn identifier}",
  "assets": [
    { ... }   // One object per completed generation task, ordered by completion time
  ],
  "failed": [
    { ... }   // Optional list of failed tasks
  ]
}
```

---

## Asset Object Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_id` | string | Yes | Task ID from the `declare` block, such as `img1` |
| `type` | string | Yes | `"image"` / `"video"` / `"audio"` / `"3d"` / `"document"` / `"code"` |
| `asset_id` | string | Yes | Globally unique asset identifier written to the asset registry for later turns |
| `status` | string | Yes | `"completed"` / `"failed"` / `"cancelled"` |
| `url` | string | Yes | **Absolute local file path** of the generated result, stored under `OMNI_OUTPUT_DIR`; not an HTTP URL |
| `description` | string | Yes | Natural-language description of the result, written in complete sentences for the agent to present to the user |
| `subtype` | string | No | Audio: `"sfx"` / `"music"` / `"speech"`; document: `"ppt"` / `"word"` / `"pdf"` / `"excel"` / `"markdown"`; code: e.g. `"webpage"`; image/video: Expert-assembled result such as `"poster"` / `"produced_video"` |
| `params_used` | object | No | Parameters actually used for generation |
| `depends_on` | string | No | Upstream `task_id` when the task has a dependency |
| `completed_at` | integer | Yes | Completion time as a Unix timestamp in seconds |

---

## Examples by Modality

### Image

```json
{
  "task_id": "img1",
  "type": "image",
  "asset_id": "img_a3f2c1",
  "status": "completed",
  "url": "/Users/alice/OmniIO/img_a3f2c1.png",
  "description": "A generated forest-mist wallpaper in warm yellow tones, with tall trees and mist as the main subjects. The 16:9 landscape image contains no people and conveys a quiet, restorative atmosphere.",
  "params_used": { "aspect_ratio": "16:9", "provider": "fal" },
  "completed_at": 1749520015
}
```

### Video

```json
{
  "task_id": "vid1",
  "type": "video",
  "asset_id": "vid_c7f1a9",
  "status": "completed",
  "url": "/Users/alice/OmniIO/vid_c7f1a9.mp4",
  "description": "A generated 15-second forest-mist video using the wallpaper as its first frame. The camera moves slowly forward, mist drifts among the trees, and the light changes subtly over time. No people appear.",
  "params_used": { "duration_seconds": 15, "aspect_ratio": "16:9", "provider": "wan" },
  "depends_on": "img1",
  "completed_at": 1749520105
}
```

### Audio

```json
{
  "task_id": "mus1",
  "type": "audio",
  "asset_id": "mus_b4e8d2",
  "status": "completed",
  "url": "/Users/alice/OmniIO/mus_b4e8d2.wav",
  "description": "Thirty seconds of generated New Age ambient meditation music, with a piano melody, string pads, natural birdsong, a relaxed tempo of about 72 BPM, and no vocals.",
  "subtype": "music",
  "params_used": { "duration_seconds": 30, "provider": "huggingface" },
  "completed_at": 1749520025
}
```

### 3D Model

```json
{
  "task_id": "3d1",
  "type": "3d",
  "asset_id": "3d_e9a012",
  "status": "completed",
  "url": "/Users/alice/OmniIO/3d_e9a012.glb",
  "description": "A generated GLB model of an elf with long emerald-green hair and light silver armor, standing and facing forward. It can be imported directly into mainstream 3D software.",
  "params_used": { "provider": "tripo" },
  "depends_on": "img1",
  "completed_at": 1749520090
}
```

### Document

```json
{
  "task_id": "ppt1",
  "type": "document",
  "asset_id": "ppt_f2c834",
  "status": "completed",
  "url": "/Users/alice/OmniIO/ppt_f2c834.pptx",
  "description": "An eight-slide project presentation with four sections: background, core solution, data analysis, and next steps, in a professional business style.",
  "subtype": "ppt",
  "params_used": { "style": "professional", "slides": 8 },
  "completed_at": 1749520030
}
```

---

## Complete Assembly Example

This turn generates a wallpaper, background music, and a short video that depends on the wallpaper:

```json
{
  "turn_id": "turn_20260618_1437",
  "assets": [
    {
      "task_id": "mus1",
      "type": "audio",
      "asset_id": "mus_b4e8d2",
      "status": "completed",
      "url": "/Users/alice/OmniIO/mus_b4e8d2.wav",
      "description": "Thirty seconds of generated New Age ambient meditation music, with a piano melody, string pads, natural birdsong, a relaxed tempo of about 72 BPM, and no vocals.",
      "subtype": "music",
      "params_used": { "duration_seconds": 30, "provider": "huggingface" },
      "completed_at": 1749520025
    },
    {
      "task_id": "img1",
      "type": "image",
      "asset_id": "img_a3f2c1",
      "status": "completed",
      "url": "/Users/alice/OmniIO/img_a3f2c1.png",
      "description": "A generated forest-mist wallpaper in warm yellow tones, with tall trees and mist as the main subjects. The 16:9 landscape image contains no people and conveys a quiet, restorative atmosphere.",
      "params_used": { "aspect_ratio": "16:9", "provider": "fal" },
      "completed_at": 1749520015
    },
    {
      "task_id": "vid1",
      "type": "video",
      "asset_id": "vid_c7f1a9",
      "status": "completed",
      "url": "/Users/alice/OmniIO/vid_c7f1a9.mp4",
      "description": "A generated 15-second forest-mist video using the wallpaper as its first frame. The camera moves slowly forward, mist drifts among the trees, and the light changes subtly over time. No people appear.",
      "params_used": { "duration_seconds": 15, "aspect_ratio": "16:9", "provider": "wan" },
      "depends_on": "img1",
      "completed_at": 1749520105
    }
  ],
  "failed": []
}
```

---

## Relationship to the Asset Registry

After the session, every asset in `output_format` with `status: "completed"` is written to the asset registry. Its `asset_id` remains valid in later turns and can be referenced with `asset_ref`. Assets that failed (`failed`) or were cancelled (`cancelled`) are not written to the registry.
