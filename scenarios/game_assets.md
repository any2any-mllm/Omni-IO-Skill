# Scenario: Game-Asset Production

## Scenario Description

The user needs game assets such as concept art for a character, prop, or environment; a 3D model; a showcase or promotional video; and sometimes a webpage integrating those assets. The core chain is often concept art → 3D model based on the concept → showcase video, with an optional webpage as the integrated presentation layer. **The deliverable mix is flexible**, and the user's needs determine where the chain ends.

---

## Trigger Examples

- "Design a fantasy elf character, starting with concept art and then turning it into a 3D model."
- "Use this character concept to generate a 3D model and a rotating showcase video."
- "Create a complete prop package: concept art + 3D model + showcase video + presentation page."
- "Create a promotional video for this weapon model."

---

## Trigger Boundary

**Trigger when:** The user wants to produce a game character, prop, environment, or other asset involving the concept-art → 3D-model chain, or explicitly asks for a game-asset package.

**Do not trigger when:** The user wants only character concept art and no 3D conversion; use `skills/generate/image.md`. If the user already has a reference image and wants only a 3D model, use `skills/generate/3d.md` directly without expanding the full chain.

**When uncertain:** Confirm how far the chain should go: concept art only, through 3D, or also a showcase video/page.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| Text description | Character, prop, or environment concept and style | Required |
| Image | Optional existing concept or reference; may skip image generation and start with 3D | Optional |

---

## Media and Deliverable Selection Rules

1. **Core chain:** Concept art (`image`) → 3D model (`3d`, using the concept as a reference) → showcase/promotional video. Any step may be the endpoint, depending on the request.
2. If the user provides a reference image, skip concept-image generation and begin with 3D.
3. **Choose video by complexity:** Use the `video` atomic skill for a simple rotation or one-shot concept clip. Use `expert/video-producer/video-producer.md` for a multi-shot character/prop trailer or a complete edit with narration, music, or subtitles.
4. **Dependencies use the two existing real injection rules:** `image → 3d` injects `reference_image_url`; `image → video` injects `first_frame_url`. Both are single dependencies. The Video Producer Expert still expands only into existing atomic tasks.
5. **For an integrated presentation webpage**, use `skills/generate/code.md`: create `type: "code"` and set `depends_on` to every required upstream `asset_id`, such as `["img1", "3d1", "vid1"]`. This is a multiple dependency and is supported only by `code` and `markdown`. Before writing the HTML natively, Claude calls `get_asset()` for every upstream `asset_id` and embeds the returned paths. After writing, it **must** call `register_asset()` or the page cannot be modified by `asset_ref` in a later turn.
6. If the page needs an interactive 3D preview rather than a static screenshot, Claude chooses an appropriate frontend solution while coding, such as `<model-viewer>`; the Scenario does not prescribe one.

---

## Expert / Atomic Selection Rules

| Deliverable Condition | Execution Method |
|-----------------------|------------------|
| Complete multi-shot game-character or prop trailer | `expert/video-producer/video-producer.md` |
| One-shot rotating showcase or concept clip | `skills/generate/video.md` |
| Concept art and 3D model | Corresponding `image` / `3d` atomic skill |
| Integrated showcase webpage | `skills/generate/code.md` |

The Game-Asset Scenario owns the combination of concept art, 3D, video, and webpage. The Video Producer Expert owns only production and review inside a complete promotional video.

---

## Reference `declare` Block

This representative example builds concept art → 3D model + showcase video → integrated page. Adapt it using the rules above:

```
<declare>
{
  "tasks": [
    {
      "id": "img1",
      "type": "image",
      "prompt": "Fantasy elf character concept art: long emerald-green hair, light silver armor, full-body front view on a white background, in a game-character design style.",
      "params": { "aspect_ratio": "1:1" }
    },
    {
      "id": "3d1",
      "type": "3d",
      "prompt": "A fantasy-forest elf with long emerald-green hair and light silver armor, in a front-facing T-pose with a stylized-realistic look.",
      "depends_on": "img1"
    },
    {
      "id": "vid1",
      "type": "video",
      "prompt": "A 360-degree rotating showcase of the elf character under soft background lighting that emphasizes the armor's detail and materials.",
      "params": { "duration_seconds": 10 },
      "depends_on": "img1"
    },
    {
      "id": "code1",
      "type": "code",
      "prompt": "A game-character showcase page integrating the concept art, interactive 3D-model preview, and rotating showcase video.",
      "depends_on": ["img1", "3d1", "vid1"]
    }
  ]
}
</declare>
```

Scheduling: Wave 0 = `img1`; Wave 1 = `3d1` and `vid1` in parallel; Wave 2 = `code1` after all three upstream tasks complete.

`vid1` is a simple rotating showcase and therefore uses the video atomic skill. If the user requests multiple shots, narration, music, subtitles, or a complete promotional edit, replace `vid1` with the task fragment expanded by the Video Producer Expert. The final page then depends on the complete video asset returned by that Expert.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| image | Character or prop concept art |
| 3d | 3D model file in GLB format |
| video, when requested | Showcase or promotional video |
| code, when requested | Integrated showcase webpage registered in the asset registry for later modification |
