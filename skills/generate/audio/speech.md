# Skill: Speech Synthesis (TTS)

## Trigger

The `declare` block contains a task with `type: "speech"`.

---

## Tool

**Default: Microsoft Edge TTS** (completely free; no API key)  
**Alternatives: OpenAI TTS / ElevenLabs TTS**

- Configuration: `config.yaml → generate.speech`
- Required key: none for default `edge_tts`; `OPENAI_API_KEY` for OpenAI; `ELEVENLABS_API_KEY` for ElevenLabs
- Call: MCP tool `generate_speech(text, voice, language, speed)`

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `text` | `declare.prompt` | Text to read |
| `voice` | `declare.params` or configuration default | Two forms are accepted: (1) one of six semantic categories—`"neutral"`, `"male"`, `"female"`, `"warm"`, `"authoritative"`, or `"cheerful"`—which all providers map to preset voices, with Edge also using `language`; or (2) a provider-native voice identifier, such as Edge's `zh-CN-YunjianNeural` or an ElevenLabs custom/cloned voice ID, which passes through unchanged. When the user describes a voice naturally, such as "male" or "warmer," classify it into one of the six semantic categories instead of asking for a technical voice name. |
| `language` | `declare.params` or configuration default | Language code such as `"zh-CN"` or `"en-US"`; only Edge uses it to select a language-specific semantic map. Uncovered languages fall back to the `zh-CN` map. |
| `speed` | `declare.params` or configuration default | Speed from 0.5 to 2.0; 1.0 is normal |

---

## Procedure

1. **Resolve parameters:** Read the text, voice, language, and speed.
2. **Choose the tool:** Use Edge TTS by default. If `config.yaml` selects OpenAI or ElevenLabs, use that provider.
3. **Call the API:** Send the TTS request.
4. **Process the result:** Obtain the local MP3 path.
5. **Return status:** Return an `output_format` asset object.

---

## Output Format

```json
{
  "task_id": "tts1",
  "type": "audio",
  "asset_id": "tts_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/tts_c7f1a9.mp3",
  "description": "Synthesized speech using Edge TTS. Content: {text summary}…",
  "subtype": "speech",
  "params_used": { "voice": "en-US-AriaNeural", "language": "en-US", "speed": 1.0 },
  "completed_at": 1749520030
}
```

---

## Defaults

| Parameter | Default | Description |
|-----------|---------|-------------|
| `voice` | `"neutral"` | Edge → XiaoxiaoNeural for `zh-CN` or AriaNeural for `en-US`; OpenAI → alloy; ElevenLabs → Rachel |
| `language` | `"zh-CN"` | Mandarin; affects only Edge's semantic-category map |
| `speed` | `1.0` | Normal speed |

---

## Semantic Category → Provider Voice Map

| Category | Edge (`zh-CN`) | Edge (`en-US`) | OpenAI | ElevenLabs |
|----------|----------------|----------------|--------|------------|
| `neutral` | XiaoxiaoNeural | AriaNeural | alloy | Rachel |
| `male` | YunxiNeural | GuyNeural | echo | Adam |
| `female` | XiaoxiaoNeural | JennyNeural | shimmer | Bella |
| `warm` | XiaoxiaoNeural | EmmaNeural | nova | Domi |
| `authoritative` | YunyangNeural | ChristopherNeural | onyx | Arnold |
| `cheerful` | XiaoyiNeural | AnaNeural | fable | Elli |

The Edge map was checked against the locally available voices returned by `edge_tts.list_voices()`. The ElevenLabs voice IDs were not verified with a real API call because `ELEVENLABS_API_KEY` was not configured locally. They are expected to work but may require manual replacement if the API returns 400/404.

---

## Error Handling

| Error | Handling |
|-------|----------|
| API key missing for a non-Edge provider | Ask for the corresponding key or switch back to Edge in `config.yaml` |
| Text exceeds the API limit | Split it into segments, synthesize them, merge them, and notify the user |
| `voice` is neither a semantic category nor a valid native voice | The tool raises an error such as Edge's `ValueError`; retry with a semantic category |
