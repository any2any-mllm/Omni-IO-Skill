# Video Producer Expert

Turn a brief into one reviewed final video by planning the narrative, delegating media generation to existing atomic skills, assembling the returned assets with the existing code path, and repairing only the failed parts.

Follow `../../orchestration/expert_protocol.md`. Do not introduce a new task type and do not modify an atomic skill.

## Decide whether to use this Expert

Use this Expert when the user requests a finished video that involves one or more of:

- multiple scenes or a duration that benefits from several generated clips;
- script, storyboard, voiceover, music, subtitles, logo, CTA, or brand packaging;
- product promotion, explainer, advertisement, training, testimonial, brand story, or social-video production;
- supplied images or clips that must be incorporated into a coherent final video;
- final review and selective regeneration of failed scenes.

Use `skills/generate/video.md` directly when one short Wan2.7 clip satisfies the request and the user does not need a production workflow, external narration/music, subtitles, branding, or assembly.

## Build one production brief

Extract or infer:

- purpose, audience, platform, and CTA;
- target duration, aspect ratio, and delivery format;
- core message, required facts, and prohibited claims;
- visual tone, pacing, brand constraints, and supplied assets;
- audio strategy, language, voice character, music direction, and subtitle need.

Ask only for missing choices that materially change the result. Do not force a long questionnaire when the request already provides enough direction. Treat approved facts, product claims, names, prices, and CTA as locked copy.

## Choose the production path

### Direct atomic path

If one simple clip is sufficient, stop using this Expert and route to the existing `video` atomic skill.

### Native-audio production

Use Wan2.7-generated audio when the value comes from scene ambience, sound effects, short dialogue, or synchronized cinematic action. Describe desired sound explicitly inside each video prompt. Preserve native clip audio during assembly unless inspection finds a problem.

### Custom-audio production

Use existing `speech` and/or `music` atomic skills when the final video needs a controlled narrator, consistent brand voice, unified music bed, or precise script. Remove or suppress generated clip audio during the `code` assembly task, then mix the custom tracks.

Do not add an unsupported audio parameter to the frozen `video` atomic interface.

**Provider caveat**: precise per-scene `duration_seconds` and `aspect_ratio` control (as assumed by the storyboard rules below) only holds on the default Wan2.7 provider, which honors requested values exactly. If `generate.video.provider` is switched to Kling, the atomic tool silently rounds every requested duration to either 5s or 10s and coerces every aspect ratio other than `"16:9"` to `"9:16"` — see `skills/generate/video.md` for the exact rule. Under Kling, fine-grained duration/aspect-ratio control described in this document is not achievable; check the actual `params_used` returned by each scene and adjust the storyboard/assembly plan to the real durations rather than the requested ones.

## Write the script and storyboard

Create an internal script before generating media:

1. Define the hook, development, proof or explanation, and ending CTA.
2. Divide the story into the smallest useful number of scenes.
3. Keep each Wan2.7 generation within the supported atomic task duration used by this project.
4. Assign each scene a purpose, duration, visual action, camera behavior, subject state, audio role, and transition intention.
5. Make the sum of scene durations compatible with the target duration after transitions and trimming.

Write each scene prompt as a complete production instruction. Repeat shared continuity anchors where needed:

- subject identity and stable visual traits;
- wardrobe, product geometry, palette, lighting, environment, and time of day;
- camera language, frame rate feel, motion intensity, and aspect ratio;
- required sound for native-audio scenes;
- forbidden changes, unwanted text, watermarks, or extra subjects.

Use generated or supplied keyframes only when they materially improve composition or identity consistency. Do not generate a keyframe for every scene by default.

## Expand into existing atomic tasks

Build a flat fragment for the existing `<declare>` plan. Use only existing task types:

- `image` for optional keyframes, product stills, title-card backgrounds, or visual references;
- `video` for each generated scene;
- `speech` for controlled narration;
- `music` for a unified music bed;
- `code` for final video/audio assembly, subtitles, logo, title cards, trimming, transitions, and export;
- `asset_ref` for reusable registered assets.

Let independent scenes and audio tasks run in parallel when their prompts are self-contained. Declare dependencies only when a scene truly consumes a generated keyframe or another required asset.

Do not emit `type: "expert"`, `type: "scene"`, `type: "assemble"`, or another unsupported type.

Example custom-audio fragment:

```json
{
  "tasks": [
    {
      "id": "promo_scene1",
      "type": "video",
      "prompt": "A six-second opening for a premium headphone product. Against a black background, cool white rim light gradually reveals the silhouette as the camera pushes in slowly. Restrained, high-end technology-advertising style; no subtitles or watermarks.",
      "params": { "duration_seconds": 6, "aspect_ratio": "16:9" }
    },
    {
      "id": "promo_scene2",
      "type": "video",
      "prompt": "An eight-second feature showcase for premium headphones. Preserve the black metal finish and cool white rim light while the camera orbits to reveal the ear cups and folding structure. Modern technology-advertising style; no subtitles or watermarks.",
      "params": { "duration_seconds": 8, "aspect_ratio": "16:9" }
    },
    {
      "id": "promo_voice",
      "type": "speech",
      "prompt": "Immersive sound. Effortless comfort. Bring every listening moment back to its purest form.",
      "params": { "voice": "authoritative", "language": "en-US" }
    },
    {
      "id": "promo_music",
      "type": "music",
      "prompt": "Restrained, modern, precise electronic ambient music with gentle low frequencies, suitable for a premium technology product advertisement, with no vocals.",
      "params": { "duration_seconds": 20, "instrumental": true }
    },
    {
      "id": "promo_final",
      "type": "code",
      "prompt": "Join the two video clips in storyboard order, remove their original audio, mix in narration and background music, duck the music under speech, add accurate subtitles and a closing CTA, and export the final MP4.",
      "depends_on": ["promo_scene1", "promo_scene2", "promo_voice", "promo_music"]
    }
  ]
}
```

## Assemble the final video

After all required upstream assets complete:

1. Resolve every consumed `asset_id` to a local path.
2. Verify that local FFmpeg is available before promising an assembled MP4.
3. Use the existing `code` execution path to assemble the video; do not add a permanent project script in this phase.
4. Normalize clip dimensions, frame rate, codecs, and audio format when needed.
5. Order, trim, and transition scenes according to the storyboard.
6. For native audio, preserve useful clip audio and smooth audible boundaries.
7. For custom audio, remove clip audio, mix narration and music, duck music under speech, and apply appropriate fades.
8. Add locked subtitles, title cards, logo, and CTA only when requested or required by the brief.
9. Export MP4 under `OMNI_OUTPUT_DIR` with the requested aspect ratio and target duration.
10. Call `register_asset()` with `asset_type="video"`, `subtype="produced_video"`, the final local path, and a complete description. `register_asset()`'s `depends_on` takes only a single string and means something different from the declare-block dependency array used above (which is a scheduling instruction only, never passed through as-is) — it is not for listing consumed upstream assets. See `skills/generate/code.md`. Leave `depends_on` unset here unless this call is itself a revision of one specific prior video version, in which case set it to that prior `asset_id`.

If FFmpeg is unavailable, do not claim that separate clips are a finished video. Report the missing assembly capability and preserve completed atomic assets.

## Inspect before delivery

Call `understand_video` on the final MP4 and review the returned description and timeline. Inspect audio separately when the video analysis is insufficient. Check:

- Content: every required message, fact, product feature, and CTA is present and accurate.
- Structure: hook, development, and ending follow the storyboard and fit the target duration.
- Visual quality: no obvious anatomy, geometry, identity, flicker, jump, watermark, or accidental-text problem.
- Continuity: subjects, product appearance, palette, lighting, environment, and motion feel coherent enough across scenes.
- Edit: ordering, trimming, transitions, title cards, logo, and ending are intentional.
- Audio: narration is complete and intelligible; music does not mask speech; levels and boundaries are controlled.
- Subtitles: text matches narration, timing is plausible, and nothing is clipped.
- Delivery: aspect ratio, duration, file format, and platform intent are correct.

Do not deliver a first assembly merely because every atomic task completed.

## Revise only the faulty layer

Classify each failed check and create the smallest useful incremental plan:

| Failure | Revision |
|---------|----------|
| One scene has visual defects or wrong content | Regenerate only that `video` task, then rerun assembly |
| Keyframe or supplied still is wrong | Replace or regenerate only that `image` input and its dependent scene |
| Narration wording, pronunciation, or tone is wrong | Regenerate only `speech`, then rerun audio assembly |
| Music style or energy is wrong | Regenerate only `music`, then remix |
| Subtitle, trim, transition, logo, CTA, or volume is wrong | Modify only the `code` assembly task |
| Overall story is wrong | Revise the storyboard and only the scenes/audio affected by that revision |

There is no in-place update anywhere in this system — regenerating a `video`, `image`, `speech`, or `music` task always produces a brand-new `asset_id`, never overwrites the old one. Before rerunning assembly, repoint the `code` task's `depends_on` (and the asset paths it resolves via `get_asset()`) at every new `asset_id`; rerunning assembly unchanged would silently reuse the stale asset.

Inspect the new final MP4 after every revision. Perform at most two autonomous revision rounds. If the result still fails, explain the remaining issue and request the smallest decision needed to continue.

## Return the result

Present the final MP4 path first, followed by a concise description of duration, aspect ratio, audio strategy, and content. Do not present scene clips as equivalent final deliverables unless the user asked for them.

When invoked by a scenario skill, return the final video asset as the Expert's output endpoint so the scenario can deliver or reuse the completed production.
