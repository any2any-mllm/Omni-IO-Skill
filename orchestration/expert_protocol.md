# Expert Skill Protocol

An Expert Skill is a professional workflow layer between Scenario skills and atomic skills. It completes the entire production loop for one final deliverable: filling essential requirement gaps, decomposing the work, planning atomic-skill calls, assembling assets, reviewing the final result, and selectively reworking problems.

This protocol constrains the agent's execution; it is not a programmatic scheduler. Experts continue to use the existing `<declare>` format and atomic skills.

---

## 1. Layers and Invocation Direction

```text
Scenario Skill → Expert Skill → Atomic Skill
```

- **Scenario Skill:** Determines the business objective and deliverable set, then selects an Expert or atomic skill for each deliverable.
- **Expert Skill:** Owns the professional end-to-end production loop for one final deliverable.
- **Atomic Skill:** Performs one generation, understanding, or code/file operation.

Invocation must remain one-way:

- A Scenario may invoke an Expert or call an atomic skill directly.
- An Expert may invoke only atomic skills and existing asset-management tools.
- An atomic skill must not invoke an Expert or Scenario.
- Experts must not invoke one another directly. If a Scenario needs multiple Experts, the Scenario layer coordinates their final outputs.

---

## 2. Routing Order

Evaluate in this order:

1. **Scenario first:** When the user needs multiple deliverables for one business scenario, load the corresponding `scenarios/*.md`.
2. **Select per deliverable inside the Scenario:** For each deliverable, the Scenario decides between an Expert and a direct atomic skill.
3. **Direct Expert:** If no Scenario matches but the user needs one professional output requiring multi-step production, assembly, and review, load the corresponding `expert/*/*.md`, such as `expert/poster-design/poster-design.md`.
4. **Atomic fallback:** If one atomic call can satisfy the request, load the relevant `skills/*` directly.

Do not over-trigger Experts merely because they cover a modality. Simple images and videos still use atomic skills.

### Observable Routing

After selecting an Expert and before the first generation tool call, tell the user in one brief, natural-language sentence which complete workflow is being used. For example:

- `poster-design`: say the work will follow copy lock → visual assets → layout assembly → final inspection.
- `video-producer`: say the work will follow script/storyboard → shot and audio generation → final assembly → final inspection.

Do not show the internal `<declare>` block. When no Expert is triggered, do not claim to be using one; execute the atomic task directly. This sentence is the main observable signal in manual trigger tests and also helps the user understand why a complete deliverable requires more steps.

---

## 3. Expert Input Contract

An Expert receives from the user request or an upstream Scenario:

- The final deliverable and intended use
- Facts, copy, and brand requirements that must remain exact
- Existing user assets and reusable `asset_id` values
- Output format, dimensions or duration, aspect ratio, and platform
- Style direction and any explicitly prohibited content

Ask only for missing information that would materially change the result. Use reasonable defaults for reversible, low-risk details so a professional workflow does not become a long questionnaire.

---

## 4. Expert Expansion Contract

An Expert does not directly "run another skill file" and does not add new `<declare>` task types. It must expand its professional workflow into existing atomic tasks.

### Allowed Task Types

Use only the types defined in `formats/declare_format.md`:

- `image`
- `video`
- `sfx`
- `music`
- `speech`
- `3d`
- `ppt`
- `word`
- `pdf`
- `excel`
- `code`
- `markdown`

Continue to reference historical assets with `asset_ref`.

Do not create undefined types such as `type: "expert"`, `type: "poster"`, `type: "scene"`, or `type: "assemble"`.

### Expansion Requirements

Every atomic task must specify:

- A unique `id`
- An existing `type`
- A complete, self-contained `prompt`
- Required `params`
- `depends_on` only when it genuinely consumes an upstream file
- The task's explicit purpose in the final deliverable

An Expert generates a flat `<declare>` task fragment. The root Skill merges it with other atomic tasks from the Scenario into one existing execution graph, then schedules the graph according to `declare_protocol.md`.

When a Scenario invokes multiple Experts, use task IDs that distinguish deliverables, such as `poster_bg`, `poster_final`, `promo_scene1`, and `promo_final`, instead of ambiguous repeated numbers.

---

## 5. Execution and Assembly

Atomic generation continues to follow the existing DAG rules:

- Independent tasks execute in the same wave in parallel.
- Dependent tasks wait for upstream success.
- An upstream failure cancels downstream tasks that genuinely depend on it.
- Historical assets are reused through `asset_ref`.

When the final deliverable must consume multiple atomic assets, use the existing `type: "code"` as the assembly node in this phase:

- For posters, the code path combines images with precisely typeset text into PNG/PDF.
- For videos, the code path uses local FFmpeg to combine shots, narration, music, subtitles, and brand elements into MP4.
- A code node may declare multiple dependencies under the existing rules.
- The actual assembled file must be registered with `register_asset()`.

At this stage, do not add permanent assembly scripts, new MCP tools, or changes to atomic skills. If real testing later proves that an assembly operation is repeated frequently and remains unreliable, create a separate project to formalize that script.

---

## 6. Review Loop

An Expert is responsible for the final deliverable and must not deliver immediately after all atomic tasks complete.

### Initial Execution

1. Execute the initial `<declare>` expanded by the Expert.
2. Complete final assembly and register the final asset.
3. Inspect the final file with the corresponding understanding capability: native vision for posters, `understand_video` for videos, and additional audio inspection where necessary.

### Locate Problems

Assign each problem to the smallest responsible layer:

- Atomic visual or shot quality
- Copy, narration, or music content
- Assembly issues such as layout, editing, subtitles, transitions, or mixing
- Overall planning or user-input problems

### Incremental Rework

Review is dynamic and should not be forced into a loop in the initial static `<declare>` block. After a failed inspection, construct an incremental plan containing only the necessary tasks:

- If an atomic asset is wrong, regenerate only that task and reassemble.
- If assembly is wrong, modify only the code task.
- Reuse verified assets and do not pay to regenerate them.
- Inspect every new final file again.

**This system has no in-place updates.** Regenerating any atomic task creates a new `asset_id` and never overwrites the old record. Before reassembly, update the code task's `depends_on` and the paths it resolves through `get_asset()` to point to the new `asset_id`; otherwise the assembly rerun will silently reuse the old asset that already failed inspection.

Perform no more than two autonomous rework rounds by default. If the result still fails after two rounds, explain the remaining issues, provide the best available version, and ask the user for the smallest directional decision needed.

---

## 7. Scenarios Invoking Experts

A Scenario Skill does not copy an Expert's internal process; it declares only selection rules and interfaces:

1. Which deliverables use which Experts
2. Which simple deliverables continue to use atomic skills
3. Whether another deliverable will reuse the Expert's final asset
4. Whether Scenario-level independent tasks can run in parallel with Expert subtasks

For example, an event scenario may choose:

```text
Poster → poster-design Expert
Music → music atomic skill
Complete teaser → video-producer Expert
```

The Scenario coordinates planning for the poster, music, and video. Each Expert owns the professional steps inside its respective poster or video.

---

## 8. Result Presentation

- Prioritize the Expert's final deliverable; never present intermediate assets as the final output.
- Show intermediate assets only when the user requests them, when explaining a failure, or when they have genuine value for later editing.
- If the Scenario will consume an Expert output, use the final deliverable's `asset_id` and local path.
- Clearly distinguish complete deliverables, reusable intermediate assets, and incomplete or failed tasks.
