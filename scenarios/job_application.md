# Scenario: Job-Application Materials

## Scenario Description

The user needs job-application or professional self-presentation materials such as a resume, cover letter, self-introduction presentation, spoken introduction, or short video. **Both the core format and deliverable mix are flexible:** application submissions use documents such as resumes and cover letters; interview or recruiting presentations may use PowerPoint; and some applications need a spoken or video introduction.

---

## Trigger Examples

- "Create a product-manager resume as a PDF."
- "Make a job-interview introduction presentation highlighting my projects."
- "Write a cover letter."
- "Write a spoken self-introduction and synthesize the audio."
- "Use my experience to create a resume and a short self-introduction video."

---

## Trigger Boundary

**Trigger when:** The user explicitly wants a job-application or professional self-presentation deliverable such as a resume, cover letter, presentation, or introduction audio/video, or wants personal experience organized into those formats.

**Do not trigger when:** The user wants only a portrait or profile image unrelated to job applications; use `skills/generate/image.md`. If the user only wants prose polished and no file, handle it as a plain-text task without this Scenario's document tools.

**When uncertain:** Confirm the final format and purpose: application document, interview presentation, or spoken script.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| Text description | Experience, target role/purpose, and style preferences | Required |
| Document | Optional existing resume or materials to polish/restructure | Optional |

---

## Media and Deliverable Selection Rules

1. **Choose the core format by purpose, not by assuming a resume:** Use Word or PDF for applications such as resumes and cover letters; PowerPoint for interview or recruiting presentations; and `speech` or `video` for spoken/video introductions. Ask under the Trigger Boundary when the purpose is unclear.
2. If the user supplies an existing document, call `understand_document` first and use the extracted content as source material for polishing and restructuring.
3. Plan a self-introduction presentation around experience, for example: cover, strengths, education, projects, skills, and outlook. Use `professional` or `creative` styling; `academic` is generally inappropriate here.
4. Use the `speech` atomic skill for narration alone and the `video` atomic skill for one simple visual clip. For a complete self-introduction video requiring a script, multiple shots, narration, music, subtitles, and final editing, load `expert/video-producer/video-producer.md`.
5. **Important limitation:** `generate_image` currently supports text-to-image only and **cannot edit or stylize the user's existing photo**. If the user asks for a professional headshot based on their photo, the tool cannot do it. It can only generate a new fictional image that is not the user; state this clearly.
6. **Important limitation:** `generate_ppt`, `generate_word`, and `generate_pdf` accept only structured text and cannot embed images. Project screenshots or personal photos requested for an introduction presentation can only be delivered as separate files; state this honestly.

---

## Expert / Atomic Selection Rules

| Deliverable Condition | Execution Method |
|-----------------------|------------------|
| Complete self-introduction or personal-brand video | `expert/video-producer/video-producer.md` |
| Standalone spoken introduction | `skills/generate/audio/speech.md` |
| One simple video asset | `skills/generate/video.md` |
| Resume, cover letter, or self-introduction presentation | Corresponding document atomic skill |

The Job-Application Scenario owns the experience content, target role, and deliverable mix. The Video Producer Expert owns only production and review of the complete video.

---

## Non-Tool Outputs

If the user wants only a spoken-introduction script or the text of a cover letter, without audio, video, or a file, Claude writes it directly in the response without any tool or generated file.

---

## Reference `declare` Blocks

The purpose determines the format. These are two representative examples; adapt them using the rules above.

**Application submission** (resume + introduction audio):

```
<declare>
{
  "tasks": [
    {
      "id": "doc1",
      "type": "pdf",
      "prompt": "Use the user's experience to create a product-manager resume covering education, work experience, core skills, and project highlights.",
      "params": { "style": "professional" }
    },
    {
      "id": "tts1",
      "type": "speech",
      "prompt": "Read a 30-second self-introduction in a confident, friendly tone suitable for a job application.",
      "params": { "voice": "warm", "language": "en-US" }
    }
  ]
}
</declare>
```

**Interview presentation** (self-introduction PowerPoint):

```
<declare>
{
  "tasks": [
    {
      "id": "ppt1",
      "type": "ppt",
      "prompt": "Use the user's experience to create a job-interview introduction presentation with a cover, personal strengths, education, projects, skill highlights, and outlook.",
      "params": { "style": "creative" }
    }
  ]
}
</declare>
```

The tasks in both examples are independent and require no dependencies.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| Document (`word`, `pdf`, or `ppt`, according to purpose) | Core resume, cover-letter, or presentation deliverable |
| Speech/video, when requested | Independently delivered self-introduction audio or video |
