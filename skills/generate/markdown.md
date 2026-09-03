# Skill: Markdown Generation

## Trigger

The `declare` block contains a task with `type: "markdown"`, or the user requests Markdown content such as documentation, a README, notes, a report draft, or a knowledge-base entry.

---

## Tool

**Claude's native Write/Edit capability; do not call any `generate_*` MCP tool.**

Markdown is plain text, and Claude can write it natively. Unlike `ppt`, `word`, `pdf`, or `excel`, it does not require a `structure` dictionary followed by binary-format rendering. Write the file directly. This uses the same execution mode as `code`, but `markdown` is an independent task type rather than a subtype of `code`. Its rules are defined here separately. Corresponding rules duplicated in `skills/generate/code.md` must be kept in sync when changed.

**As with code**, Markdown is a real file that must be tracked and reused across turns. After generation, call `register_asset()` to add the file to the asset registry. Otherwise it receives no `asset_id` and cannot be referenced with `asset_ref` in the next turn.

---

## Procedure

1. **Plan:** Determine the Markdown content and structure from the prompt, including heading levels, lists, tables, and code blocks.
2. **Write the file:** Use Write to create a `.md` file under `OMNI_OUTPUT_DIR`, alongside other generated assets. If it references assets from this or historical turns, such as images, videos, or 3D models, call `get_asset(asset_id)` and reference the returned local path, for example with Markdown image syntax `![](path)`.
3. **Register the asset:** Call `register_asset(asset_type="document", subtype="markdown", url=<file path>, description=<description>, params_used={...})` and obtain its `asset_id`. **This is mandatory.** Without it, the file is an orphan that later turns cannot find or reference.
4. **Return the result:** Report `✅ Document generated: <path>`.

---

## Modifying Existing Markdown Across Turns

When the user says, "Change the notes/document from last time":

1. Find the target `asset_id` from `asset_ref` or conversation context.
2. Call `get_asset(asset_id)` to obtain the local path.
3. Read the current content and modify it with Edit.
4. **Call `register_asset()` again** and set `depends_on` to the original `asset_id` to record version lineage.

**Note:** The asset registry does not support in-place updates. Every `register_asset()` call creates a new `asset_id` for the new file version rather than overwriting the old record. The old record remains in the registry.

---

## Dependencies

A Markdown task can declare `depends_on` in the `<declare>` graph and wait for upstream assets such as images, videos, or audio transcripts. Its execution is native file writing rather than a generation-tool call, but it follows the same DAG scheduling rules. `markdown` and `code` are the only types that allow `depends_on` to be an array. See `orchestration/dependency_rules.md`.

**Important: The potentially array-valued `depends_on` in `declare` and the single-string `depends_on` of `register_asset()` are different fields. Never mix them.**

- **`declare.depends_on`:** A scheduling instruction for Claude. It tells the DAG scheduler which upstream tasks must all finish before writing this Markdown file. After the wait, the field has served its purpose. It **must not** be passed unchanged to `register_asset()`, whose parameter accepts one string; passing an array fails validation.
- **`register_asset().depends_on`:** Unrelated to scheduling. It records version lineage only when modifying existing Markdown: the one prior `asset_id` on which the new version is based.
- Therefore, when registering a new report that integrates several assets, **omit** `depends_on`. Provide it only when one new Markdown version modifies one existing parent version.

---

## Integration with Other Skills

- **Multiple upstream assets**, such as image + video + audio transcript: `markdown` supports array-valued multiple dependencies and can consolidate several sources into one report.
- **No downstream integration:** No other type currently depends on Markdown output.

---

## Output Format

```json
{
  "asset_id": "markdown_a3f2c1",
  "type": "document",
  "subtype": "markdown",
  "status": "completed",
  "url": "/Users/alice/OmniIO/markdown_a3f2c1.md",
  "description": "Meeting-minute summary containing key decisions and action items.",
  "params_used": {},
  "completed_at": 1749520030
}
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| `register_asset()` was omitted | The file exists but has no `asset_id` and cannot be referenced with `asset_ref`; call `register_asset()` when the omission is discovered |
| Referenced upstream `asset_id` does not exist | `get_asset()` returns `{"error": ...}`; ask whether the asset was generated or cleaned up |
