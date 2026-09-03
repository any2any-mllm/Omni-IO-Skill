# Poster Design Expert

Create one polished static composition by planning the design, delegating visual generation to existing atomic skills, assembling exact copy and assets with the existing code path, and inspecting the final artifact before delivery.

Follow `../../orchestration/expert_protocol.md`. Do not introduce a new task type and do not modify an atomic skill.

## Decide whether to use this Expert

Use this Expert when the requested deliverable is a designed communication artifact, including:

- a poster, invitation, event notice, promotional graphic, or campaign key visual;
- a social cover or announcement card with exact title, date, price, address, CTA, or brand copy;
- a static composition that combines supplied assets, generated visuals, typography, and layout;
- a revision to a previously produced poster where the final composition must be inspected again.

Use `skills/generate/image.md` directly instead when the user wants only a photo, illustration, wallpaper, background, concept image, or other single visual without accurate typesetting and multi-element layout.

## Produce one locked brief

Extract the following before planning:

- purpose and target audience;
- exact copy, preserving spelling, punctuation, numbers, dates, prices, addresses, names, and CTA;
- output size, aspect ratio, platform, and PNG/PDF requirements;
- brand colors, logo, supplied photos, reference images, and prohibited elements;
- desired tone and the one message that must dominate visually.

Ask only for missing information that materially changes the result. Infer reversible details such as minor decorative choices. Never invent factual event or commercial information.

Treat approved copy as locked. Keep it separate from image-generation prompts so the image model is never responsible for final text accuracy.

## Establish the visual direction

Write a concise internal visual philosophy before generating assets. Define:

- the aesthetic idea and emotional tone;
- spatial structure, negative space, scale, rhythm, and hierarchy;
- palette, material, texture, and image treatment;
- typography character and the relationship between display and supporting text;
- the subtle conceptual reference that gives the poster coherence.

Use the philosophy as a decision system, not as a user-facing essay. Favor one strong visual idea over unrelated decoration. Keep the composition intentional and original; do not imitate a living artist or reproduce a copyrighted composition.

## Plan only necessary visual assets

Decide which inputs already exist and which must be generated. Prefer the smallest useful asset set:

1. Reuse supplied or registered assets when they satisfy the brief.
2. Generate one strong background or hero visual when a single image can carry the composition.
3. Generate a separate foreground, texture, or ornament only when it needs independent placement or revision.
4. Avoid splitting a poster into many generated fragments that cannot be cleanly isolated with current tools.

For every `image` atomic task:

- write a complete, self-contained prompt;
- require no letters, words, numbers, logos, watermarks, labels, or pseudo-text;
- describe the negative space required for later typography;
- describe subject placement relative to the planned information areas;
- use the final poster aspect ratio for full-canvas backgrounds and a suitable ratio for isolated supporting art.

## Expand into existing atomic tasks

Build a flat fragment for the existing `<declare>` plan. Use only existing task types.

- Use `image` for generated backgrounds, hero visuals, illustrations, textures, or ornaments.
- Use an `asset_ref` node when reusing a registered visual asset.
- Use `code` as the final assembly task when exact typography or multiple assets must be combined.
- Use the existing dependency rules; let the `code` assembly task depend on every asset it actually consumes. Use a single string for one upstream asset and an array only when genuinely combining multiple upstream assets.

Do not emit `type: "expert"`, `type: "poster"`, or another unsupported type.

Example fragment:

```json
{
  "tasks": [
    {
      "id": "poster_bg",
      "type": "image",
      "prompt": "A text-free contemporary music-festival poster background in deep indigo and fluorescent orange. Abstract sound waves create the main rhythm, with the visual weight concentrated in the lower half and a large area of clean negative space above. No letters, words, numbers, logos, watermarks, labels, or pseudo-text.",
      "params": { "aspect_ratio": "3:4" }
    },
    {
      "id": "poster_final",
      "type": "code",
      "prompt": "Use poster_bg and the locked copy to create a 3:4 poster. Typeset the title, time, location, and CTA precisely. Export PNG and, when requested, PDF.",
      "depends_on": "poster_bg"
    }
  ]
}
```

## Assemble the poster

After all upstream assets complete:

1. Resolve every upstream `asset_id` to a local path.
2. Use the existing `code` execution path to create the actual composition.
3. Render all locked copy deterministically; never copy text from an AI-generated image.
4. Use a Unicode font that covers every required character, especially Chinese text.
5. Preserve safe margins, alignment, contrast, reading order, and output dimensions.
6. Output a PNG by default and a PDF when requested.
7. Save final files under `OMNI_OUTPUT_DIR`.
8. Call `register_asset()` for the final composition with `asset_type="image"`, `subtype="poster"`, the final local path, and a complete description. `register_asset()`'s `depends_on` takes only a single string and means something different from the declare-block dependency array used to build this composition — it is not for listing consumed upstream assets. See `skills/generate/code.md`. Leave it unset unless this call is itself a revision of one specific prior poster version, in which case set it to that prior `asset_id`.

The assembly implementation may use locally available drawing or document libraries. Do not add a permanent project script in this phase; use the existing code-task path and keep any task-specific implementation scoped to the generated artifact.

## Inspect before delivery

Open the final PNG with native vision. If PDF is the only output, render or inspect its page before delivery. Check every item:

- Copy: exact wording, punctuation, numbers, dates, prices, addresses, names, and CTA.
- Hierarchy: one clear entry point, readable secondary information, and controlled detail.
- Layout: consistent alignment, spacing, margins, balance, and intentional negative space.
- Legibility: sufficient contrast, appropriate text size, and no collision or clipping.
- Visuals: correct subject, no unwanted pseudo-text, no obvious distortion, and no low-quality scaling.
- Brand: correct logo treatment, palette, tone, and supplied-asset usage.
- Output: correct aspect ratio, dimensions, file format, and canvas boundaries.
- Craft: cohesive rather than decorative accumulation; polished at normal and thumbnail size.

Do not deliver a first draft merely because all atomic tasks completed.

## Revise only the faulty layer

Classify each failed check and create the smallest useful incremental plan:

| Failure | Revision |
|---------|----------|
| Wrong copy, font, spacing, alignment, contrast, or clipping | Modify only the `code` assembly task |
| Weak or distorted generated visual | Regenerate only the responsible `image` task, then rerun assembly |
| Incorrect supplied asset | Resolve the correct asset with the user, then rerun assembly |
| Entire visual direction is wrong | Re-plan the philosophy and affected visual tasks; preserve verified copy |

There is no in-place update anywhere in this system — regenerating an `image` task always produces a brand-new `asset_id`, never overwrites the old one. Before rerunning assembly, repoint the `code` task's `depends_on` (and the asset paths it resolves via `get_asset()`) at the new `asset_id`; rerunning assembly unchanged would silently reuse the stale asset.

Inspect again after every revision. Perform at most two autonomous revision rounds. If the result still fails, explain the remaining issue and ask for the smallest decision needed to continue.

## Return the result

Present the final poster path first. Mention PNG/PDF variants when both exist. Do not overwhelm the user with intermediate assets unless they requested them or they are useful for further editing.

When invoked by a scenario skill, return the final poster asset as the Expert's output endpoint so other scenario deliverables can reuse it, for example as a video first frame.
