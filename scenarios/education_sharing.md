# Scenario: Education and Knowledge Sharing

## Scenario Description

The user needs educational or knowledge-sharing content for teachers, trainers, educators, or knowledge creators: explaining a topic, teaching a skill, or communicating popular science. The core is explanatory content, optionally supported by illustrations, diagrams, narration, or an instructional video. **The deliverable mix is flexible** and depends on content depth and audience.

---

## Trigger Examples

- "Create an introductory Python slide deck."
- "Make a popular-science video explaining photosynthesis."
- "Add an explanatory diagram and spoken narration for this concept."
- "Organize a set of new-employee training materials."

---

## Trigger Boundary

**Trigger when:** The user wants educational, tutorial, or popular-science content that combines courseware, illustrations, and/or explanatory audio/video, or explicitly asks for a course, tutorial, or educational explainer.

**Do not trigger when:** The user only wants to understand existing teaching material, such as "What does this course say?" Use `skills/understand/document.md`. If the user needs only one asset, such as one diagram, use the corresponding atomic skill.

**When uncertain:** Confirm whether the user wants a complete set of explanatory materials or only one component.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| Text description | Topic, audience, and required depth | Required |
| Document | Optional existing textbook or outline to distill and restructure | Optional |
| Image | Optional reference material | Optional |

---

## Media and Deliverable Selection Rules

1. **Choose the core form:** Systematic courses and training usually use PowerPoint. A single-topic explainer or popular-science piece intended for publication is often a narrated video. A text-and-image explanation may use Word or PDF plus separate images. Infer from the content when the user is not specific, and ask under the Trigger Boundary if still uncertain.
2. **Generate `image` when a diagram or visual aid will materially improve understanding.** **Important limitation:** `generate_ppt`, `generate_word`, and `generate_pdf` accept text-only `structure` and cannot embed images. Illustrations are delivered as separate files and do not automatically appear inside the courseware or document. State this honestly.
3. Use the `speech` atomic skill for narration alone, and the `video` atomic skill for one simple demonstration shot. For a complete instructional video requiring a script, multiple shots, narration, music, subtitles, and final editing, load `expert/video-producer/video-producer.md`.
4. When the source is an existing textbook or outline, call `understand_document` first and use its extracted content as source material.
5. Breaking down concepts and designing the teaching sequence are Claude's content-planning work used to prepare `structure` and prompts, not independent deliverables.

---

## Expert / Atomic Selection Rules

| Deliverable Condition | Execution Method |
|-----------------------|------------------|
| Complete popular-science, course, or training video | `expert/video-producer/video-producer.md` |
| One short conceptual demonstration | `skills/generate/video.md` |
| Standalone explanatory narration | `skills/generate/audio/speech.md` |
| Courseware, documents, and separate illustrations | Corresponding document or image atomic skills |

The Education Scenario owns the knowledge structure and deliverable mix. The Video Producer Expert turns the settled knowledge structure into a complete video workflow and inspects the finished video.

---

## Non-Tool Outputs

If the user only wants explanatory text or popular-science copy, without courseware or audio/video, Claude writes it directly in the response without a tool or generated file.

---

## Reference `declare` Block

This representative example creates a PowerPoint course and a separate explanatory image. Adapt it using the rules above:

```
<declare>
{
  "tasks": [
    {
      "id": "ppt1",
      "type": "ppt",
      "prompt": "Create an introductory Python course covering variables and data types, conditionals, loops, and basic functions, with a code example for every concept.",
      "params": { "style": "academic" }
    },
    {
      "id": "img1",
      "type": "image",
      "prompt": "A clean programming-education diagram visualizing variable assignment, with an arrow pointing to a memory location, suitable as courseware artwork.",
      "params": { "aspect_ratio": "16:9" }
    }
  ]
}
</declare>
```

`ppt1` and `img1` are independent. The image cannot be embedded in the courseware, so the two tasks produce separate files in parallel.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| Document (`ppt`, `word`, or `pdf`, according to the decision) | Core courseware or explanatory material |
| Image, when a diagram is needed | Separate file, not embedded in the document |
| Speech/video, when requested | Independently delivered explanatory media |
