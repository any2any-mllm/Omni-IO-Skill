# Skill: PDF Generation

## Trigger

The `declare` block contains a task with `type: "pdf"`.

---

## Tool

MCP tool `generate_pdf`, rendered internally with **ReportLab**, a local Python library requiring no API key.

- Configuration: `config.yaml → generate.document`
- The calling agent **plans the content itself** and passes structured JSON in `structure`. The MCP server only renders and calls no LLM, so it does not require `OPENAI_API_KEY`.
- The planner is always the calling agent—Claude in Claude Code, Codex in Codex—not the MCP server.

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `structure` | Planned by the agent from `declare.prompt` | `{"title": "Title", "sections": [{"heading": "Section", "paragraphs": ["Paragraph 1", ...]}, ...]}` |
| `style` | `declare.params` or configuration default | `professional` / `academic` |

The renderer currently supports a title, section headings, and body paragraphs only, with no tables, headers, or footers. **`style` currently does not affect rendering**, unlike PowerPoint or Excel. It is merely recorded in `params_used`; fonts, colors, and layout are identical across values. Do not promise visual differences between styles.

---

## Procedure

1. **Plan content in the agent:** Plan the title, section headings, and paragraphs from `declare.prompt`, and assemble `structure` without an external model.
2. **Call the tool:** Pass `structure` and `style` to `generate_pdf`; the tool handles margins, font sizes, and paragraph spacing.
3. **Return the result:** The tool returns an asset object and registers it automatically. Report `✅ Document generated: <path>`.

---

## Output Format

```json
{
  "task_id": "pdf1",
  "type": "document",
  "asset_id": "pdf_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/pdf_b4e8d2.pdf",
  "description": "A generated PDF about {topic}, with {N} pages. {Content summary}.",
  "subtype": "pdf",
  "params_used": { "style": "professional" },
  "completed_at": 1749520040
}
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| `structure.sections` is empty | The tool errors; the agent must complete the content plan and retry |
| ReportLab is not installed | Ask the user to run `pip install reportlab` and mark `failed` |
| Tool-call error | Read the message, correct `structure` or parameters, and retry |
| Font is unavailable | Use a built-in system font or ask the user to install the needed font |
