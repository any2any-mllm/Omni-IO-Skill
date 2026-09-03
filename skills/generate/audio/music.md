# Skill: Music Generation

## Trigger

The `declare` block contains a task with `type: "music"`.

---

## Tool

**Default: ElevenLabs Eleven Music v2** (highest quality, up to 10 minutes, vocals and multiple languages, commercial license; requires a paid ElevenLabs subscription with Music access)  
**Fallback: Hugging Face MusicGen** (free inference allowance, up to 30 seconds, cold-start latency)  
**Fallback: Replicate MusicGen Large** (paid, higher quality, up to 60 seconds, no cold start)

- Configuration: `config.yaml → generate.music`
- Required key: `ELEVENLABS_API_KEY` by default, shared with sound effects and TTS; `HUGGINGFACE_API_KEY` for Hugging Face; or `REPLICATE_API_TOKEN` for Replicate
- Call: MCP tool `generate_music(prompt, duration_seconds, instrumental)`
- A valid `ELEVENLABS_API_KEY` does not guarantee Music API access, which is currently limited to paid subscriptions. Accounts without Music access receive HTTP 401/403. Upgrade the plan or switch `generate.music.provider` in `config.yaml` to `huggingface` or `replicate`.

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `prompt` | `declare` block | Musical style, mood, instrumentation, and scene |
| `duration_seconds` | `declare.params` or configuration default | Duration; maximum 600 seconds for ElevenLabs, 30 for Hugging Face, and 60 for Replicate |
| `instrumental` | `declare.params` or configuration default | Whether the track is instrumental, with no vocals |

---

## Procedure

1. **Resolve parameters:** Read the prompt, duration, and vocal/instrumental setting and fill missing values from configuration defaults.
2. **Check the prompt:** Ensure it fully specifies atmosphere, genre, instruments, and BPM range.
3. **Call the API:** Send the request through the provider configured in `config.yaml`.
4. **Process the result:** Obtain the local MP3/WAV path.
5. **Return status:** Return an `output_format` asset object.

---

## Output Format

```json
{
  "task_id": "mus1",
  "type": "audio",
  "asset_id": "mus_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/mus_b4e8d2.mp3",
  "description": "Thirty seconds of generated meditation music using Eleven Music v2 from ElevenLabs. Style: {prompt description}.",
  "subtype": "music",
  "params_used": { "duration_seconds": 30, "provider": "elevenlabs" },
  "completed_at": 1749520025
}
```

---

## Defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| `duration_seconds` | `30` | Music duration in seconds |
| `instrumental` | `true` | Instrumental by default |

---

## Prompt Example

```
"A forest at dawn, filled with mist and warm, diffused yellow light; quiet and restorative. New Age ambient music led by piano with string pads and natural birdsong, relaxed at about 70 BPM, with no vocals."
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| API key not configured | Ask for `ELEVENLABS_API_KEY`, or switch to Hugging Face/Replicate and request the corresponding key |
| ElevenLabs returns HTTP 401/403 | Explain that the key is valid but the plan lacks Music API access; upgrade or switch to Hugging Face/Replicate |
| Hugging Face cold start returns 503 | Retry up to six times, approximately 2.5 minutes, then suggest Replicate |
| Duration exceeds provider limit | Truncate to 600/30/60 seconds for ElevenLabs/Hugging Face/Replicate and notify the user |
| Generation timeout | Mark `failed` and ask the user to retry |
