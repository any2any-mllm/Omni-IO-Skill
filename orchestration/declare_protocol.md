# Declare Protocol

`<declare>` is an **internal execution graph** that Claude constructs before performing any generation task. It plans the task breakdown, dependencies, and scheduling order. It is never shown to the user and exists only as Claude's execution guide.

---

## 1. When to Construct an Execution Graph

| Request Type | Construct a Graph? |
|--------------|--------------------|
| Includes any generation task | **Required** |
| Understanding-only request (read an image, document, etc.) | No; analyze and respond directly |
| Mixed request (understanding + generation) | **Required**, for the generation portion only |

---

## 2. Execution Graph Format

```
<declare>
{
  "tasks": [
    {
      "id": "<unique task identifier>",
      "type": "<task type>",
      "prompt": "<complete, self-contained prompt for this task>",
      "params": { "<optional tool parameters>" },
      "depends_on": "<upstream task ID; omit for an independent task>",
      "asset_ref": "<asset ID from a previous turn; use when reusing an asset>"
    }
  ]
}
</declare>
```

See `formats/declare_format.md` for format details.

---

## 3. DAG Scheduling Rules

After constructing the graph, Claude executes it according to these rules.

### Step 1: Divide the Graph into Topological Waves

Group tasks into execution waves based on their dependencies:

- **Wave 0:** Tasks without `depends_on`, including `asset_ref` tasks, which are treated as already completed
- **Wave N:** Tasks whose direct dependencies were all completed in earlier waves

```
Example (image → 3D, with independent music):
  Wave 0: [img1, mus1]   → parallel
  Wave 1: [3d1]          → starts after img1 completes
```

### Step 2: Execute Wave 0 in Parallel

**Start every Wave 0 MCP tool call in the same tool-call turn.** Claude Code supports concurrent tool calls in one turn, which is essential for true parallelism. Do not wait for them sequentially.

### Step 3: Advance Through Later Waves

After every Wave 0 task completes, identify tasks whose dependencies are now all satisfied, place them in Wave 1, and start them in parallel. Continue until every task is complete.

### Step 4: Inject Upstream Results

When a task finishes, its output URL and `asset_id` are automatically used in downstream tool-call parameters without user intervention. See `orchestration/dependency_rules.md` for the injection rules.

### Exception: `type: "code"` and `"markdown"`

The steps above normally execute each task by calling its corresponding `generate_*` MCP tool once. `code` and `markdown` are currently the only exceptions. They still occupy ordinary nodes in a wave and wait for dependencies, including multiple dependencies as described in `orchestration/dependency_rules.md`. During execution, however, Claude writes the file natively with Write/Edit instead of calling a generation tool, then calls `register_asset()` to register the result. See `skills/generate/code.md` and `skills/generate/markdown.md`. The scheduling rules are unchanged; only the work performed inside those nodes differs.

---

## 4. Error Handling

| Condition | Handling |
|-----------|----------|
| One task's tool call fails | Mark the task failed and continue other independent tasks; cancel downstream tasks that depend on it |
| The asset referenced by `asset_ref` does not exist | Ask whether the user wants to regenerate it |
| Self-check finds a cyclic dependency | Tell the user there is a dependency problem and replan |
| An API key is missing | Ask the user to configure the corresponding key and mark the task failed |

---

## 5. Sequence Diagram

```
User request
  │
  ▼
Claude analyzes intent
  │
  ├─ [Understanding only] → analyze directly; no execution graph
  │
  └─ [Includes generation] → construct internal <declare> graph
                                  │
                                  ▼
                          Topological grouping
                          Wave 0 / Wave 1 / ...
                                  │
                            ┌─────┴──────────┐
                            ▼                ▼
                       Wave 0 task A    Wave 0 task B
                       (parallel call)  (parallel call)
                            │
                      After all complete,
                       check downstream
                            │
                            ▼
                       Wave 1 tasks
                 (start in parallel when ready)
                            │
                            ▼
                  All tasks complete → update asset registry → show results
```
