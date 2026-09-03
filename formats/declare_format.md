# `<declare>` Execution Graph Specification

`<declare>` is an internal execution graph that Claude constructs before performing any generation task. It encodes the complete task plan as structured JSON so Claude can schedule tool calls in DAG order. **Do not show it to the user.**

---

## When to Construct It

- **Required:** The request includes any generation task.
- **Not required:** The request is understanding-only, such as "What is in this image?" or "Read this PDF for me."

---

## Format

```
<declare>
{
  "tasks": [
    {
      "id": "<unique task identifier>",
      "type": "<task type>",
      "prompt": "<complete, self-contained prompt for this task>",
      "params": { "<optional tool parameters>" },
      "depends_on": "<upstream task ID; omit for an independent task>",
      "asset_ref": "<asset ID from a previous turn; use when reusing an asset>"
    }
  ]
}
</declare>
```

---

## Field Reference

### `tasks[].id`

A unique identifier within the current turn, referenced by `depends_on`.

Naming convention: `img1`, `img2`, `vid1`, `sfx1`, `mus1`, `tts1`, `3d1`, `ppt1`, `code1` for `code`, and `md1` for `markdown`.

### `tasks[].type`

The task type, corresponding to a specific skill under `skills/generate/`.

| type | Description |
|------|-------------|
| `image` | Image generation |
| `video` | Video generation |
| `sfx` | Sound-effect generation |
| `music` | Music generation |
| `speech` | Speech synthesis |
| `3d` | 3D-model generation |
| `ppt` | PowerPoint generation |
| `word` | Word-document generation |
| `pdf` | PDF generation |
| `excel` | Excel-workbook generation |
| `code` | Code/webpage generation. Claude writes the file natively; this is not an MCP tool call. See `skills/generate/code.md`. |
| `markdown` | Markdown-text generation. Claude writes the file natively; this is not an MCP tool call. See `skills/generate/markdown.md`. |

### `tasks[].prompt`

The complete, self-contained generation prompt for this task. Each prompt must state all necessary information independently and must not rely on the content of another task's prompt. When multiple tasks run in parallel, Claude writes their prompts in the same planning context, naturally preserving semantic consistency.

### `tasks[].params`

Optional tool parameters that override defaults in `config.yaml`. Common parameters include:

| Parameter | Applicable Types | Example |
|-----------|------------------|---------|
| `aspect_ratio` | image | `"16:9"` |
| `duration_seconds` | video / sfx / music | `10` |
| `voice` | speech | `"neutral"` |
| `language` | speech | `"en-US"` |
| `instrumental` | music | `true` |

### `tasks[].depends_on`

Declares the upstream task or tasks required by this task. The task starts only after its upstream work is complete.

```json
"depends_on": "img1"                    // Single dependency: used by most task types
"depends_on": ["img1", "3d1", "vid1"] // Multiple dependencies: supported only by type "code" / "markdown"
```

**Single dependency** (`string`): Supported by all task types. The typical case is a chain such as "create a video/3D model from the image just generated." The upstream output is automatically injected into the downstream tool-call parameters:

| Dependency | Automatically Injected Value |
|------------|------------------------------|
| image → video | The upstream image URL as the video's first frame |
| image → 3d | The upstream image URL as the visual reference |

**Multiple dependencies** (`array`, valid only for `type: "code"` or `"markdown"`): Other task types are single MCP calls with fixed parameter signatures and cannot accept a variable number of upstream assets, so they support only one dependency. `code` and `markdown` do not call fixed-signature tools; Claude writes their files natively and can call `get_asset()` for each `asset_id` before writing, so they can genuinely consume multiple dependencies. **Declaring multiple dependencies for any other task type is a planning error.** Split the work into a single-dependency chain or make the tasks independent and parallel.

Claude uses all `depends_on` relationships to build a directed acyclic graph (DAG), then schedules tasks in topological order. Tasks without dependencies start in parallel in the same tool-call turn; dependent tasks wait for their upstream task.

**Dependency rule:** When uncertain, declare the dependency conservatively. A missing dependency can produce incorrect output; an unnecessary dependency only reduces parallel efficiency.

### `tasks[].asset_ref`

References an asset generated in a previous turn. When this field is set, no API call is made; treat the asset as an already-completed node whose output is available to downstream tasks. It is mutually exclusive with `prompt`.

---

## Examples

### Independent Tasks (Parallel Execution)

```
<declare>
{
  "tasks": [
    {
      "id": "img1",
      "type": "image",
      "prompt": "A cyberpunk Tokyo street at 2:00 a.m. Neon lights reflect on wet pavement and the air is full of rain mist. Low-angle shot with cinematic composition.",
      "params": { "aspect_ratio": "16:9" }
    },
    {
      "id": "sfx1",
      "type": "sfx",
      "prompt": "A cyberpunk Tokyo street at 2:00 a.m. Neon lights reflect on wet pavement and the air is full of rain mist. Rain dominates, with occasional distant footsteps; oppressive and somber.",
      "params": { "duration_seconds": 15 }
    }
  ]
}
</declare>
```

### Dependent Tasks (Sequential Execution)

```
<declare>
{
  "tasks": [
    {
      "id": "img1",
      "type": "image",
      "prompt": "An elf character from a fantasy forest, with long emerald-green hair and light silver armor. Full-body front character art on a white background, in a game-character design style."
    },
    {
      "id": "3d1",
      "type": "3d",
      "prompt": "A fantasy-forest elf with long emerald-green hair and light silver armor, standing in a front-facing T-pose, in a stylized-realistic look.",
      "depends_on": "img1"
    }
  ]
}
</declare>
```

### Asset Reuse Across Turns

```
<declare>
{
  "tasks": [
    {
      "id": "img1",
      "type": "image",
      "asset_ref": "img_a3f2c1"
    },
    {
      "id": "vid1",
      "type": "video",
      "prompt": "A cyberpunk Tokyo street at 2:00 a.m. Neon lights reflect on wet pavement and the air is full of rain mist. A slow forward tracking shot down the street with no people.",
      "depends_on": "img1",
      "params": { "duration_seconds": 10 }
    }
  ]
}
</declare>
```
