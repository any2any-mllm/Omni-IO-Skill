---
name: omni-io
description: >
  An omni-modal content generation and understanding skill set. Trigger it automatically when the user needs
  image generation, video production, music or sound-effect generation, 3D models, document generation,
  cross-modal conversion, or related work. It supports any-modality-to-any-modality input and output,
  dependency-aware DAG task scheduling (executing independent tasks in parallel), and cross-turn asset reuse.
  Use this skill whenever a request involves understanding or generating multimedia content.
version: 3.0.0
---

# Omni-IO Entry Point

---

## First-Use Check

**Upon receiving the first multimodal task in each session**, call the `check_config()` tool before executing the task and show the user:

- ✅ Ready features (the corresponding API keys are configured)
- ❌ Features requiring configuration, with pricing information and free alternatives
- 🆓 Features that require no key

If a critical key is missing, recommend the minimum configuration, prioritizing free options, and then continue the current task. Modalities whose keys are missing will be marked as failed; all others will execute normally.

Once this check has run in a session, do not repeat it for subsequent requests in that session.

---

## Workflow

When a request involves multimodal content, follow these steps:

1. Call `set_turn("turn_YYYYMMDD_HHmm")` to tag assets for the current turn. Do this once for every user message; use the current time for `YYYYMMDD_HHmm`.
2. Determine the request type using the routing order in `orchestration/expert_protocol.md`:
   - First compare the request against the trigger examples in the Scenario index. A scenario applies when the user needs a complete set of multiple deliverables rather than a single asset. If a scenario matches, load the corresponding `scenarios/*.md`; the scenario determines whether each deliverable should use an Expert or an atomic skill.
   - If no scenario matches but the user wants a complete deliverable that requires professional multi-step production, assembly, and review—such as a poster with precise text layout or a multi-shot video with narration and music—load the relevant `expert/*/*.md` from the Expert index.
   - If a single generation or understanding operation is sufficient, load the relevant atomic skill directly from the Understanding, Generation, or Utility index.
3. When using an Expert, first tell the user in one brief, natural-language sentence which professional workflow will be used (for example, "I’ll produce this by locking the copy, creating the visual assets, assembling the layout, and reviewing the final result"). Then follow `orchestration/expert_protocol.md` to expand the workflow into existing atomic tasks. Do not display the internal `<declare>` block or introduce new task types.
4. Internally construct a `<declare>` execution graph (**do not show it to the user**) that lists the task breakdown and dependencies.
5. Execute tasks according to the DAG scheduling rules: invoke tools for independent tasks **in parallel**, and wait for upstream tasks before starting dependent tasks.
6. Expert tasks must inspect the final deliverable. If it fails inspection, create incremental tasks only for the problematic parts and inspect it again, for up to two rounds by default.
7. Return results to the user as they become available, showing completed results first. In the final summary, prioritize the complete deliverable and never present intermediate assets as the final output.

---

## Skill Index

This skill has three layers:

- **Atomic skills** (Understanding / Generation / Utility): perform one specific generation, understanding, or code/file operation.
- **Expert skills**: professionally decompose, plan atomic-skill calls, assemble, review, and selectively rework one final deliverable. The output remains a single-modality file.
- **Scenario skills**: handle complex cross-modal scenarios by determining the required set of deliverables, selecting an Expert or atomic skill for each deliverable, and coordinating the complete user request.

The invocation direction is irreversible: **Scenario skill → Expert skill → Atomic skill**. A Scenario or Expert may invoke only lower layers. A Scenario may skip a layer and invoke atomic skills directly. Atomic skills must not invoke Experts; Experts must not invoke Scenarios or other Experts; and atomic skills must not depend on higher-layer skills.

Load the appropriate files on demand based on the request type:

### Scenarios
After a scenario matches, follow the Orchestration Rules below to perform the actual scheduling. To add a scenario, use `scenarios/_template.md` as the authoring reference. The template itself is not a triggerable scenario and is not listed here.
- `scenarios/social_media_post.md` — Social media post production. The media mix is flexible: choose image, video, and/or audio based on the request and target platform, together with copy.
- `scenarios/office.md` — Office work, including meeting-minute cleanup and report, courseware, and spreadsheet production; centered on PPT, Word, PDF, and Excel documents.
- `scenarios/job_application.md` — Job-application materials, including resumes, cover letters, and self-introduction presentations, with optional self-introduction audio or video.
- `scenarios/education_sharing.md` — Educational sharing, including courseware and popular-science explanations; centered on PPT, Word, and PDF, with optional illustrations and explanatory audio/video.
- `scenarios/event_materials.md` — Event collateral, including invitations, poster images, ambient music, and teaser or recap videos.
- `scenarios/game_assets.md` — Game-asset production: concept art → 3D model → showcase video, with an optional integrated showcase webpage.

### Experts
Use an Expert only when one final deliverable requires professional multi-step production, assembly, and review. Do not use one when a single atomic call is sufficient.
- `expert/poster-design/poster-design.md` — Posters, invitations, promotional graphics, and social covers with accurate text layout; decomposes visual assets, deterministic typesetting, visual review, and selective rework.
- `expert/video-producer/video-producer.md` — Complete multi-shot videos or videos with narration, music, subtitles, or brand packaging; covers scripting and storyboarding, atomic media generation, assembly, final-video review, and selective rework.

### Understanding
- `skills/understand/image.md` — Image understanding, description generation, and OCR
- `skills/understand/video.md` — Video-scene analysis and subtitle extraction
- `skills/understand/audio.md` — Speech-to-text and audio classification
- `skills/understand/document.md` — PDF / Word / PPT / Excel content extraction
- `skills/understand/3d.md` — 3D point-cloud analysis and geometric description

### Generation
- `skills/generate/image.md`
- `skills/generate/video.md`
- `skills/generate/audio/sfx.md`
- `skills/generate/audio/music.md`
- `skills/generate/audio/speech.md`
- `skills/generate/3d.md`
- `skills/generate/document/ppt.md`
- `skills/generate/document/word.md`
- `skills/generate/document/pdf.md`
- `skills/generate/document/excel.md`
- `skills/generate/code.md` — Code/webpage generation (Claude writes files natively; call `register_asset()` to register them)
- `skills/generate/markdown.md` — Markdown text generation (Claude writes files natively; call `register_asset()` to register them)

### Utilities
- `skills/utility/search.md`
- `skills/utility/browse.md`

---

## Orchestration Rules (Always Apply)

All multimodal requests must follow:

- `orchestration/declare_protocol.md` — How to construct the internal execution graph and schedule tool calls
- `orchestration/dependency_rules.md` — How to infer task dependencies
- `orchestration/asset_registry.md` — Asset tracking, cross-turn reuse, and file persistence
- `orchestration/interruption.md` — How to handle new user instructions during generation
- `orchestration/expert_protocol.md` — Expert routing, atomic-task expansion, assembly, review, and selective rework rules

---

## Global Rules

1. **Always construct the execution graph internally before execution.** Define the task breakdown and dependencies before calling tools. Do not show the graph to the user.
2. **Execute independent tasks in parallel.** Start them in the same tool-call turn instead of waiting for each one sequentially.
3. **Prioritize reuse of existing assets.** Read the asset registry (`registry.json`) before generating anything to avoid duplicate work.
4. **When a dependency is uncertain, decide conservatively.** It is better to declare an extra dependency and sacrifice some parallel efficiency than to omit one and produce an incorrect result.
5. **Return results in real time.** Show each result as soon as it is ready instead of waiting for every task to complete.
6. **Check API keys before calling tools.** If a required key is missing, tell the user and offer alternatives.
7. **Present results** in the following format after generation so the user can open the file themselves:
   - Image: `✅ Image generated: <local path>`
   - Video: `✅ Video generated: <local path>`
   - Audio / sound effect / speech: `✅ Audio generated: <local path>`
   - 3D model: `✅ 3D model generated: <local path>`
   - Document: `✅ Document generated: <local path>`

   Files are saved in the workspace directory configured by the user (see `setup/quickstart.md`).
8. **Experts do not introduce new task types.** An Expert must expand its workflow into existing `<declare>` types; existing atomic skills and MCP interfaces remain unchanged.
9. **Complete deliverables must be reviewed.** Posters, complete videos, and other Expert outputs must be checked using the corresponding understanding capability. Prefer selective rework, with at most two rounds by default.
