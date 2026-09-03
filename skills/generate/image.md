# Skill: Image Generation

## Trigger

The `declare` block contains a task with `type: "image"`.

---

## Tool

**Default: fal.ai FLUX.1-schnell** (US$10 free credit for new users)  
**Alternative: OpenAI gpt-image-2** (higher quality)

- Configuration: `config.yaml → generate.image`
- Required API key: `FAL_API_KEY` by default, or `OPENAI_API_KEY` after switching
- Call: MCP tool `generate_image(prompt, aspect_ratio, quality)`

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `prompt` | `declare` block | Complete, self-contained image description, including the overall atmosphere and image-specific details |
| `aspect_ratio` | `declare.params` or configuration default | Image aspect ratio, such as `"16:9"`, `"1:1"`, `"9:16"`, `"4:3"`, or `"3:4"` |
| `quality` | `declare.params` or configuration default | `"standard"` by default or `"hd"` |

---

## Procedure

1. **Resolve parameters:** Read `prompt` and `params` from `declare` and fill missing values from the configuration defaults.
2. **Call the API:** Use the provider configured in `config.yaml`, fal by default.
3. **Process the result:** Retrieve the generated image and save it to the local workspace.
4. **Return status:** Record the result as an `output_format` asset object and write it to the asset registry.

---

## Output Format

```json
{
  "task_id": "img1",
  "type": "image",
  "asset_id": "img_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/img_a3f2c1.png",
  "description": "A generated {scene description}, with {color palette}, {composition}, and {characteristics}.",
  "params_used": { "aspect_ratio": "16:9" },
  "completed_at": 1749520015
}
```

The MCP server generates `description` automatically. It calls GPT-4o-mini when `OPENAI_API_KEY` is configured; otherwise it uses the image path as the description.

---

## Defaults

From `config.yaml → defaults.image`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `aspect_ratio` | `"1:1"` | Square |
| `quality` | `"standard"` | `"standard"` / `"hd"` |

---

## Integration with Other Skills

- **Downstream video:** Automatically inject the completed image URL as the downstream video's first-frame parameter.
- **Downstream 3D:** Automatically inject the completed image URL as the downstream 3D task's reference-image parameter.

---

## Error Handling

| Error | Handling |
|-------|----------|
| API key not configured | Ask the user to set `FAL_API_KEY`, or switch the provider to OpenAI and set `OPENAI_API_KEY` |
| Prompt violates content policy | Ask the user to revise the prompt and mark the task `failed` |
| Network timeout | Retry once; if it still fails, mark the task `failed` |
