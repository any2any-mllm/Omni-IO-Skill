# Skill: PowerPoint Generation

## Trigger

The `declare` block contains a task with `type: "ppt"`.

---

## Tool

MCP tool `generate_ppt`, rendered internally with **python-pptx**, a local Python library requiring no API key.

- Configuration: `config.yaml → generate.document`
- The current calling agent—Claude, Codex, or another host model—**plans the content itself** and passes the result as structured JSON in `structure`. The MCP server only renders; it calls no LLM and does not require `OPENAI_API_KEY`.
- In Claude Code, Claude plans the content. In Codex or another host, that host model plans it. The planner is always the calling agent, never the MCP server.

---

## Inputs

| Field | Source | Description |
|-------|--------|-------------|
| `structure` | Planned by the agent from `declare.prompt` | `{"title": "Title", "slides": [{"title": "Slide title", "points": ["Point 1", "Point 2"]}, ...]}` |
| `style` | `declare.params` or configuration default | `"professional"` / `"academic"` / `"creative"` |

---

## Procedure

1. **Plan content in the agent:** From `declare.prompt`, plan the title, every slide title and its points, and the slide count—about eight by default, adjusted to the content. Assemble `structure` without calling an external model.
2. **Call the tool:** Pass `structure` and `style` to `generate_ppt`. The tool handles page size, colors, fonts, and per-slide layout.
3. **Return the result:** The tool returns an asset object and registers it automatically. Report `✅ Document generated: <path>`.

---

## Output Format

```json
{
  "task_id": "ppt1",
  "type": "document",
  "asset_id": "ppt_{6-digit-hex}",
  "status": "completed",
  "url": "/Users/alice/OmniIO/ppt_f2c834.pptx",
  "description": "A generated {topic} presentation with {N} slides covering {section summary}, in a {style} style.",
  "subtype": "ppt",
  "params_used": { "style": "professional", "slides": 8 },
  "completed_at": 1749520030
}
```

---

## Defaults and Styles

| Parameter | Default | Description |
|-----------|---------|-------------|
| `style` | `"professional"` | Professional business style |

| style | Colors | Typography | Best For |
|-------|--------|------------|----------|
| `professional` | Navy + white + gray | Sans-serif / Arial | Business reports |
| `academic` | Dark green + white + cream | Serif / Times New Roman | Academic reports |
| `creative` | Gradients + large color blocks | Rounded / sans-serif | Creative proposals |

---

## Error Handling

| Error | Handling |
|-------|----------|
| `structure.slides` is empty | The tool errors; the agent must complete the content plan and retry |
| python-pptx is not installed | Ask the user to run `pip install python-pptx` and mark `failed` |
| Tool-call error | Read the message, correct `structure` or parameters, and retry |
| File write fails | Check `OMNI_OUTPUT_DIR` permissions and try an alternative path |
| Font renders incorrectly | Use a built-in system font or ask the user to install the needed font |
