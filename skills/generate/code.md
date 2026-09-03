# Skill: Code / Webpage Generation

## Trigger

The `declare` block contains a task with `type: "code"`, or the user requests a webpage, script, small utility, or other code deliverable.

---

## Tool

**Claude's native Write/Edit capability; do not call any `generate_*` MCP tool.**

Unlike image, video, and document generation, code and webpages have no specialized generation engine; Claude writes the code itself. This resembles image understanding with Claude's native vision, but with one critical difference: **code is a real file that must be tracked and reused across turns**. After generation, call `register_asset()` to add the file to the asset registry. Otherwise it receives no `asset_id` and cannot be referenced with `asset_ref` in the next turn.

---

## Procedure

1. **Plan:** Determine what the prompt requires—a webpage, script, utility, or other code—and design its structure and implementation.
2. **Write the file:** Use Write to save the code under `OMNI_OUTPUT_DIR`, alongside other generated assets. If the code references an asset from this or a historical turn, such as an image, video, or 3D model, call `get_asset(asset_id)` and embed or reference the returned local path.
3. **Register the asset:** Call `register_asset(asset_type="code", subtype="webpage", url=<file path>, description=<description>, params_used={...})` and obtain its `asset_id`. **This is mandatory.** Without it, the file is an orphan that later turns cannot find or reference.
4. **Return the result:** Report `✅ Code/webpage generated: <path>`.

---

## Modifying Existing Code Across Turns

When the user says, "Change the webpage/script from last time":

1. Find the target `asset_id` from `asset_ref` or conversation context.
2. Call `get_asset(asset_id)` to obtain the local path.
3. Read the current content and modify it with Edit.
4. **Call `register_asset()` again** and set `depends_on` to the original `asset_id` to record version lineage.

**Note:** The asset registry does not support in-place updates. Every `register_asset()` call creates a new `asset_id` for the new file version rather than overwriting the old record. The old record remains in the registry.

---

## Dependencies

A code/webpage task can declare `depends_on` in the `<declare>` graph and wait for upstream assets such as images, 3D models, or video. Its execution is native file writing rather than a generation-tool call, but it follows the same DAG scheduling rules: independent tasks run in parallel and dependent tasks wait. `code` and `markdown` are the only types that allow `depends_on` to be an array. See `orchestration/dependency_rules.md`.

**Important: The array-valued `depends_on` in `declare` and the single-string `depends_on` of `register_asset()` are different fields. Never mix them.**

- **`declare.depends_on`:** A scheduling instruction for Claude. It tells the DAG scheduler which upstream tasks must all finish before writing this `code` file. After the wait, the field has served its purpose. It **must not** be passed unchanged to `register_asset()`, whose parameter accepts one string; passing an array fails validation.
- **`register_asset().depends_on`:** Unrelated to scheduling. It records version lineage only when modifying existing code: the one prior `asset_id` on which the new version is based.
- Therefore, when registering a new webpage that integrates several assets, such as the example in `game_assets.md`, **omit** `depends_on`. Provide it only when one new code version modifies one existing parent version.

---

## Integration with Other Skills

- **Multiple upstream assets**, such as image + 3D model + video: `code`, together with `markdown`, supports array-valued multiple dependencies. An integrated showcase page is the typical case; see `scenarios/game_assets.md`.
- **No downstream integration:** No other type currently depends on code output; `code` is usually the endpoint of a chain.

---

## Output Format

```json
{
  "asset_id": "webpage_a3f2c1",
  "type": "code",
  "subtype": "webpage",
  "status": "completed",
  "url": "/Users/alice/OmniIO/webpage_a3f2c1.html",
  "description": "A game-character showcase page containing concept art, a 3D-model preview, and an embedded promotional video.",
  "params_used": { "framework": "vanilla-html" },
  "completed_at": 1749520030
}
```

---

## Error Handling

| Error | Handling |
|-------|----------|
| `register_asset()` was omitted | The file exists but has no `asset_id` and cannot be referenced with `asset_ref`; call `register_asset()` when the omission is discovered |
| Referenced upstream `asset_id` does not exist | `get_asset()` returns `{"error": ...}`; ask whether the asset was generated or cleaned up |
| Generated code needs external dependencies or a build step | Tell the user honestly; the static file itself does not install dependencies or run a build |
