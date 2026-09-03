# Skill: Excel-Workbook Generation

## Trigger

The `declare` block contains a task with `type: "excel"`.

---

## Tool

MCP tool `generate_excel`, rendered internally with **openpyxl**, a local Python library requiring no API key.

- Configuration: `config.yaml → generate.document`
- The calling agent **plans the content itself** and passes structured JSON in `structure`. The MCP server only renders and calls no LLM, so it does not require `OPENAI_API_KEY`.
- The planner is always the calling agent—Claude in Claude Code, Codex in Codex—not the MCP server.

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `structure` | Planned by the agent from `declare.prompt` | `{"title": "Title", "sheets": [{"name": "Sheet name", "headers": ["Column 1", "Column 2"], "rows": [["Value 1", "Value 2"], ...]}, ...]}` |
| `style` | `declare.params` or configuration default | `"professional"` / `"academic"` / `"creative"`; affects only the header background color |

The renderer supports structured tables with headers and data rows only: no formulas, charts, or conditional formatting. Cell types come directly from the JSON values in `rows`; provide numbers rather than strings for columns used in calculations.

---

## Procedure

1. **Plan content in the agent:** Plan each sheet's name, headers, and rows from `declare.prompt`, and assemble `structure` without an external model.
2. **Call the tool:** Pass `structure` and `style` to `generate_excel`; the tool creates multiple sheets, styles headers, and auto-sizes columns.
3. **Return the result:** The tool returns an asset object and registers it automatically. Report `✅ Document generated: <path>`.

---

## Output Format

```json
{
  "task_id": "excel1",
  "type": "document",
  "asset_id": "excel_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/excel_f2c834.xlsx",
  "description": "A generated Excel workbook about {topic}, with {N} sheets and {M} data rows.",
  "subtype": "excel",
  "params_used": { "style": "professional", "sheets": 2 },
  "completed_at": 1749520030
}
```

---

## Defaults and Styles

| Parameter | Default | Description |
|-----------|---------|-------------|
| `style` | `"professional"` | Navy header |

| style | Header Background |
|-------|-------------------|
| `professional` | Navy |
| `academic` | Dark green |
| `creative` | Purple |

---

## Error Handling

| Error | Handling |
|-------|----------|
| `structure.sheets` is empty | The tool errors; the agent must complete the content plan and retry |
| openpyxl is not installed | Ask the user to run `pip install openpyxl` and mark `failed` |
| Tool-call error | Read the message, correct `structure` or parameters, and retry |
| Sheet name is too long | The tool truncates it to Excel's 31-character limit |
| Duplicate sheet names | openpyxl appends numeric suffixes such as `Sheet1`; it does not error, but the result may differ from the plan, so make names unique during planning |
