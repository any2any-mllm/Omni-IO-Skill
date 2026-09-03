# Skill: Video Understanding

## Trigger

The user uploads a video and asks to:

- Summarize its content: "What is this video about?"
- Extract subtitles or dialogue: "Transcribe what is said."
- Analyze a segment: "What happens from 00:30 to 01:00?"
- Identify key frames: "Find the most important shots."
- Use its style as a generation reference

For an understanding-only request with no generation, **do not output a `<declare>` block**.

---

## Tool

**Gemini 2.5 Flash** (Google AI)

- Required key: `GEMINI_API_KEY`
- Call: MCP tool `understand_video(video_url)`
- Input: local file path or HTTP URL
- Return: `{ "description": "overall description", "timeline": [{"time": "00:00-00:15", "description": "..."}] }`

---

## Inputs

| Format | Description |
|--------|-------------|
| MP4 / MOV / AVI | Upload directly; below 500 MB is recommended |
| URL | Directly accessible video URL |
| `asset_id` | Video generated in the current session |
| Time range | Optional segment such as `00:30–01:00` |

---

## Analysis Dimensions

**Content summary**

- Topic and core content
- Timeline structure with segment descriptions
- Key events and turning points

**Speech-to-text (ASR)**

- Complete dialogue or narration transcript
- Sentence-level timestamped subtitles
- Speaker separation when several people speak

**Visual analysis**

- Scene-change detection and segmentation
- Key-frame identification at major content changes
- Visual style: cinematography, color, editing rhythm

**Audio analysis**

- Background-music style
- Environmental-sound characteristics
- Audio-visual synchronization

---

## Procedure

1. **Determine the goal:** Summary, subtitles, key frames, or style reference.
2. **Process the video:** Call `understand_video(video_url)`. Gemini handles visual understanding, speech recognition, and timeline analysis in one call; do not call a separate ASR tool.
3. **Integrate temporal information:** Organize segment results chronologically.
4. **Format the output:** Match the user's requested form.

---

## Output Formats

**Content summary:** A segmented timeline followed by an overall summary.

```
00:00–00:30  Opening: an establishing city view with light music
00:30–02:00  Main content: an interview discussing...
02:00–02:30  Closing and call to action
Overall theme: ...
```

**Subtitles:** SRT or timestamped plain text.

```
[00:00:05] Hello, and welcome to...
[00:00:08] Today we will discuss...
```

**Key frames:** List each timestamp and frame description; capture screenshots when requested.

**Style reference for generation:**

```
Video style: [editing rhythm] + [cinematography] + [color palette] + [musical atmosphere]
Example: "Fast-paced editing, many close-ups, cool blue tones, and electronic music."
```

---

## Integration with Other Skills

| Follow-Up | Integration |
|-----------|-------------|
| Generate a similar video | Add the style description to the `generate/video` prompt |
| Process audio separately | Pass the audio track to `understand/audio` |
| Create a document from subtitles | Pass the transcript to `generate/document` |
