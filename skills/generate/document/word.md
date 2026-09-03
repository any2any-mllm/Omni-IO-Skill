# Skill: Word-Document Generation

## Trigger

The `declare` block contains a task with `type: "word"`.

---

## Tool

MCP tool `generate_word`, rendered internally with **python-docx**, a local Python library requiring no API key.

- Configuration: `config.yaml → generate.document`
- The calling agent **plans the content itself** and passes structured JSON in `structure`. The MCP server only renders and calls no LLM, so it does not require `OPENAI_API_KEY`.
- The planner is always the calling agent—Claude in Claude Code, Codex in Codex—not the MCP server.

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `structure` | Planned by the agent from `declare.prompt` | `{"title": "Title", "sections": [{"heading": "Section", "paragraphs": ["Paragraph 1", ...]}, ...]}` |
| `style` | `declare.params` or configuration default | `"professional"` / `"academic"` / `"report"` |

The renderer currently supports first-level headings and body paragraphs only, with no tables or bulleted-list objects. Prefix paragraph text with `"• "` to simulate a list. **`style` currently does not affect rendering**, unlike PowerPoint or Excel. It is merely recorded in `params_used`; fonts, colors, and layout are identical across values. Do not promise visual differences between styles.

---

## Procedure

1. **Plan content in the agent:** Plan the title, section headings, and paragraphs from `declare.prompt`, and assemble `structure` without an external model.
2. **Call the tool:** Pass `structure` and `style` to `generate_word`; the tool creates the document, heading hierarchy, and paragraphs.
3. **Return the result:** The tool returns an asset object and registers it automatically. Report `✅ Document generated: <path>`.

---

## Output Format

```json
{
  "task_id": "word1",
  "type": "document",
  "asset_id": "word_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/word_a3f2c1.docx",
  "description": "A generated Word document about {topic}, with {N} pages covering {section summary}.",
  "subtype": "word",
  "params_used": { "style": "report" },
  "completed_at": 1749520035
}
```

---

## Default

| Parameter | Default |
|-----------|---------|
| `style` | `"professional"` |

---

## Error Handling

| Error | Handling |
|-------|----------|
| `structure.sections` is empty | The tool errors; the agent must complete the content plan and retry |
| python-docx is not installed | Ask the user to run `pip install python-docx` and mark `failed` |
| Tool-call error | Read the message, correct `structure` or parameters, and retry |
| Font renders incorrectly | Use a built-in system font or ask the user to install the needed font |
