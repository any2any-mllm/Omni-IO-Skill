# Scenario: Office Work

## Scenario Description

The user needs an office-document deliverable such as PowerPoint, Word, PDF, or Excel. The work may begin with a meeting or interview recording that needs to be organized, existing materials that need to be distilled and restructured, or a report, course, summary, or workbook planned from scratch. **The deliverable mix is flexible:** the core is usually one structured document, while its format, illustrations, and any prerequisite transcription or source analysis depend on the task.

---

## Trigger Examples

- "Turn this meeting recording into organized minutes in a Word document."
- "Create a company-introduction presentation."
- "Use these materials to prepare a project-summary report as a PDF."
- "Create a training slide deck."
- "Organize this sales data into an Excel workbook with separate sheets by month and region."

---

## Trigger Boundary

**Trigger when:** The user explicitly wants an office-document deliverable in PowerPoint, Word, PDF, or Excel, especially when transcription, distillation, or organization is needed before writing, such as turning audio into minutes, source materials into a report, or data into a workbook.

**Do not trigger when:** The user only wants to understand an existing document, such as "What does this presentation say?" Use `skills/understand/document.md`. If the user wants only an audio transcript and no organized document, use `skills/understand/audio.md`.

**When uncertain:** Confirm whether the user wants a polished document or only the source analysis/transcript.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| Text description | Topic, purpose, and format preferences | Required |
| Audio | Optional meeting or interview recording to transcribe and organize | Optional |
| Document | Optional source material to distill and organize | Optional |

---

## Media and Deliverable Selection Rules

1. **The core deliverable is almost always one document.** First choose the format: presentations and introductions are generally PowerPoint; minutes, reports, and summaries are generally Word or PDF; data, tables, and lists use Excel. Infer from the content when no format is specified, and ask under the Trigger Boundary if still uncertain.
2. **If the input includes a recording**, first call `understand_audio` with `subtype="speech"`. Use the transcript as a source for the document, but have Claude organize and summarize it into a planned `structure` instead of dumping the raw transcript into the document.
3. **If the input includes an existing document**, first call `understand_document` to extract source content. If extracted table data must be reorganized in Excel, map it directly into the `sheets` and `rows` for `generate_excel`.
4. **Illustrations:** Generate an `image` only when the user explicitly requests illustrations or visualization. **Important limitation:** `generate_ppt`, `generate_word`, `generate_pdf`, and `generate_excel` currently accept only structured text or table data; they cannot embed images. Generated illustrations are delivered as **separate files** and do not appear automatically inside the document. State this honestly in the result and never imply that an image has been embedded.
5. **Additional Excel limitation:** `generate_excel` supports headers and data rows only, not formulas, charts, or conditional formatting. If the user asks for a formula-driven budget or automatic totals, explain that the current generator cannot produce it.
6. Organizing, summarizing, and structuring source transcripts or documents into the tool's `structure` is preparation for the call, not a separate deliverable, and does not need to be shown independently.

---

## Reference `declare` Block

This representative example turns a meeting recording into a Word document. Adapt it using the rules above:

```
<declare>
{
  "tasks": [
    {
      "id": "doc1",
      "type": "word",
      "prompt": "Organize the meeting transcript into structured minutes covering the meeting topic, key discussion points, decisions, action items, and owners.",
      "params": { "style": "professional" }
    }
  ]
}
</declare>
```

If the source is audio, call `understand_audio` before `declare` to obtain the transcript; Claude then organizes it to plan `doc1.structure`. An independently requested illustration can run in parallel as an `image` task with no dependency on `doc1`. For an Excel result, change `type` to `"excel"` and plan `structure` as `sheets` / `headers` / `rows`; the rest of the scheduling is unchanged.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| Document (`ppt`, `word`, `pdf`, or `excel`, according to the decision) | Core deliverable with structured content |
| Image, when requested | Separate file; not embedded in the document |
