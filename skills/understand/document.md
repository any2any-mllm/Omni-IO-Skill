# Skill: Document Understanding

## Trigger

The user uploads a document and asks to:

- Extract its content: "Read this PDF."
- Summarize it: "What are the report's main points?"
- Extract structured data: "Organize the data from this table."
- Use it as a generation reference: "Recreate a presentation based on this one."

---

## Tools

- **Preferred free local methods:** `.docx` with macOS `textutil` or `python-docx`; `.pptx` with `python-pptx`; `.xlsx` with `openpyxl` or `pandas`. Invoke them through Bash; none requires an API key.
- **Fallback `understand_document` MCP tool:** Mistral OCR 3, requiring `MISTRAL_API_KEY`. Use only when local extraction cannot handle a scanned/image-based document or a complex layout needing visual OCR.

---

## Tool Selection

Priority: **Claude native Read → free local library → Mistral OCR fallback**. A missing key is no longer a blocker.

| File Type | Tool | Notes |
|-----------|------|-------|
| Plain text such as `.md`, `.txt`, `.csv`, `.py` | Native **Read** | Direct, no API |
| Text-based selectable PDF | Native **Read** | Claude Code supports PDF reading |
| `.docx` | Local `textutil -convert txt -stdout <file>` through Bash | Built into macOS, free. Use `python-docx` for complex paragraph/table structure. |
| `.pptx` | Local `python-pptx` script through Bash | Iterate `slide.shapes` to extract text and tables; free |
| `.xlsx` / `.xls` | Local `openpyxl` or `pandas.read_excel` script through Bash | Extract per sheet; reads values, formula results, and multiple sheets |
| Scanned image-only PDF | `understand_document` MCP tool | Local text extraction cannot OCR scanned pages; uses Mistral |
| Image-heavy PDF/docx/pptx with complex layout or embedded charts needing vision | `understand_document` MCP tool | Local libraries expose only the text layer; use professional OCR/visual parsing |

**When to use OCR:** Try the local method first. If it returns very little content, garbled text, or a document composed mainly of scans/images, switch to `understand_document`; only then ask for `MISTRAL_API_KEY`.

---

## Analysis Dimensions

Choose only what the user needs.

**Full extraction**

- Preserve headings, paragraphs, and lists
- Render tables as Markdown tables

**Summary**

- Main topic and conclusions
- Key data and facts
- Chapter/section outline

**Structured data extraction**

- Table data, including merged rows/columns
- Entities such as key values, dates, and names

**PowerPoint-specific**

- Slide titles and points
- Speaker notes
- Overall narrative structure

---

## Procedure

1. **Identify the file type:** Choose the free local tool from the table; consider MCP only when local methods do not apply.
2. **Determine the goal:** Full extraction, summary, structured data, or generation reference.
3. **Extract:** Prefer `textutil`, `python-docx`, `python-pptx`, or `openpyxl`; clean garbled or misaligned output. Fall back to `understand_document` only when extraction is sparse or the pages are scanned images.
4. **Format the result:** Use the forms below.

---

## Output Formats

**Full extraction:** Complete text preserving Markdown heading hierarchy.

**Summary:**

```
Document type: research report
Core topic: ...
Main conclusions:
  1. ...
  2. ...
Key data: ...
```

**PowerPoint structure:**

```
Slide 1  Title: Project Background
         Points: Market size reached X billion with Y% growth

Slide 2  Title: Core Solution
         Points: Three major modules...
```

**Generation reference:** Output a content outline plus style description for `generate/document`.

---

## Integration with Other Skills

| Follow-Up | Integration |
|-----------|-------------|
| Recreate a presentation | Pass the outline to `generate/document/ppt` |
| Reorganize an Excel table | Pass extracted table data to `generate/document/excel`; note that the generator supports headers + rows only, not formulas/charts |
| Generate an image from the content | Use the document's scene description as the `generate/image` prompt |
