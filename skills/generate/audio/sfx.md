# Skill: Sound-Effect Generation

## Trigger

The `declare` block contains a task with `type: "sfx"`.

---

## Tool

**ElevenLabs Sound Effects API**

- Configuration: `config.yaml → generate.sfx`
- Required key: `ELEVENLABS_API_KEY`
- Call: MCP tool `generate_sfx(prompt, duration_seconds)`

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `prompt` | `declare` block | Complete description of the scene, primary sound sources, spatial character, and intensity |
| `duration_seconds` | `declare.params` or configuration default | Duration from 0.5 to 30 seconds; out-of-range values are clamped automatically |

---

## Procedure

1. **Resolve parameters:** Read the prompt and duration and fill missing values from configuration defaults.
2. **Check the prompt:** Ensure it fully describes atmosphere, dominant sources, spatial character, and intensity layers.
3. **Call the API:** Send the request to ElevenLabs Sound Effects.
4. **Process the result:** Obtain the audio URL, usually MP3.
5. **Return status:** Return an `output_format` asset object.

---

## Output Format

```json
{
  "task_id": "sfx1",
  "type": "audio",
  "asset_id": "sfx_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/sfx_a3f2c1.mp3",
  "description": "A generated {duration}-second {scene} sound effect dominated by {primary source}, with {spatial character} and {atmosphere}.",
  "subtype": "sfx",
  "params_used": { "duration_seconds": 15, "provider": "elevenlabs" },
  "completed_at": 1749520020
}
```

`url` is a local file path under `OMNI_OUTPUT_DIR`, not an HTTP URL.

---

## Defaults

| Parameter | Default |
|-----------|---------|
| `duration_seconds` | `15` |

---

## Prompt Example

```
ElevenLabs prompt: "Rainy cyberpunk Tokyo street ambience at 2:00 a.m., with neon reflected on wet pavement. Rain dominates, with occasional distant cars and footsteps, a broad space, and an oppressive, gloomy mood."
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| API key not configured | Ask for `ELEVENLABS_API_KEY` and mark the task `failed` |
| Duration exceeds API limit | Clamp automatically and notify the user |
| Generation fails | Mark `failed` and ask the user to adjust the prompt |
