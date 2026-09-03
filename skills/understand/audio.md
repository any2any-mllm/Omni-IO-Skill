# Skill: Audio Understanding

## Trigger

The user uploads audio and asks to:

- Transcribe speech
- Identify a musical style
- Analyze environmental sounds
- Use the audio as a reference for new generation

---

## Tool

**One call: `understand_audio(audio_url, subtype)`**. The tool chooses the provider internally; Claude does not switch it manually.

Priority: **Gemini API → subtype-specific fallback provider**

### Preferred: Gemini API for All Audio Types

Required key: `GEMINI_API_KEY`, shared with video understanding.

When configured, Gemini `gemini-2.5-flash` handles speech, music, and SFX in one tool call, performing transcription or style analysis without separate code paths or manually written request code.

### Fallback: Specialized Provider by Subtype

If `GEMINI_API_KEY` is missing or Gemini fails/times out, the tool automatically uses:

- `subtype = "speech"` → **Whisper**, the paid OpenAI cloud API using `OPENAI_API_KEY`
- `subtype = "music"` or `"sfx"` → **Qwen2-Audio via DashScope**, using `QWEN_API_KEY`; the same DashScope account used for `WAN_API_KEY` can be reused

Claude calls `understand_audio(audio_url, subtype)` once and does not decide the provider.

---

## Inputs

| Format | Description |
|--------|-------------|
| WAV / MP3 / M4A / FLAC | Upload directly |
| `asset_id` | Audio generated in the current session |
| Video file | Extract and analyze its audio track |

---

## Determine the Audio Type

Classify the primary content before analysis:

```
Speech, dominated by voices    → speech-recognition path
Music, dominated by melody     → music-analysis path
Environmental sound / SFX      → soundscape-analysis path
Mixed speech + music           → separate and process each
```

---

## Analysis by Path

### Speech Recognition

- Complete ASR transcript
- Speaker separation for multiple speakers
- Timestamped subtitles
- Language identification
- Emotion and tone: calm, excited, questioning, etc.

### Music Analysis

- Genre: pop, electronic, classical, jazz, folk, etc.
- Mood: cheerful, melancholy, calm, tense, uplifting, etc.
- BPM estimate
- Up to three principal instruments
- Presence of vocals

Prefer Gemini. Fall back to Qwen2-Audio with `QWEN_API_KEY` when Gemini is unavailable.

### Soundscape Analysis

- Dominant sounds: rain, crowd, traffic, nature, etc.
- Foreground/background layers
- Spatial character: indoor/outdoor, enclosed/open
- Overall emotional atmosphere

---

## Procedure

1. **Classify:** Determine the main type from the user's description or content: speech → `subtype="speech"`; music → `"music"`; sound effects/environment → `"sfx"`.
2. **Call `understand_audio(audio_url, subtype)`:** The tool automatically prefers Gemini and falls back to Whisper or Qwen.
3. **Format the output:** Match the user's need.
4. **Prepare a generation reference:** If the user wants new content based on the audio, produce a standardized prompt-ready description.

---

## Output Formats

**Speech transcript:**

```
[00:02] Hello everyone. Today we'll talk about...
[00:08] First, the initial question is...
```

**Music analysis:**

```
Genre: electronic pop
Mood: energetic with a trace of melancholy
BPM: approximately 128
Main instruments: synthesizer, drum machine, bass
Vocals: ethereal female voice
```

**Environmental sound:**

```
Dominant sound: rain at medium intensity
Background: occasional thunder and distant traffic
Space: open outdoor environment
Overall atmosphere: gloomy, oppressive, rainy night
```

**Generation reference:**

```
Sound-effect description: [dominant sound] + [layers] + [space] + [emotion]
Example: "Heavy rain with occasional thunder, a broad outdoor space, and an oppressive rainy-night atmosphere."
```

---

## Integration with Other Skills

| Follow-Up | Integration |
|-----------|-------------|
| Generate a similar sound effect | Use the soundscape description as the `generate/sfx` prompt |
| Generate similar music | Use the music analysis as the `generate/music` prompt |
| Create a document from speech | Pass the transcript to `generate/document` |
| Combine with video understanding | Integrate the audio analysis with the visual analysis |
