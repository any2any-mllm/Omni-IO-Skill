# Scenario: Social Media Post Production

## Scenario Description

The user provides a topic, product, or reference material and wants a complete post for a social platform such as Xiaohongshu, TikTok/Douyin, Instagram, or Weibo. Choose a flexible combination of image, video, and/or audio for the specific request and target platform, together with platform-appropriate copy. **The media mix is not fixed**; the request and platform determine which atomic skills to use.

---

## Trigger Examples

- "Create a short video with a misty forest-at-dawn atmosphere for Xiaohongshu and add meditation music." (video + music + copy)
- "Make a set of product images and captions for Xiaohongshu." (images + copy)
- "Turn this into a podcast clip with copy for the platform." (audio + copy)
- "Write a Douyin-style short-video script for this product and create a cover image." (image + video + copy)

---

## Trigger Boundary

**Trigger when:** The user explicitly mentions publishing to a social/content platform or requests a packaged post, image-and-text post, or other publishable content containing both media and copy.

**Do not trigger when:** The user requests one media asset without copy, such as a single image, or explicitly says no copy is needed. Use the corresponding atomic skill and do not add unrequested copy.

**When uncertain:** Ask which media types and whether copy are needed instead of expanding to the full workflow by default.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| Text description | Topic, target platform, style, selling points, and related details | Required |
| Image | Optional reference or product image | Optional |
| Document | Optional brand voice or product information | Optional |

---

## Media and Deliverable Selection Rules

This is the core of the Scenario. It is not a fixed call chain; decide again for every request:

1. **Prioritize explicitly requested media**, such as video, image, music, or voice-over, which map directly to `video`, `image`, `music`, or `speech`.
2. **When only a platform is named, follow platform conventions:** Xiaohongshu is primarily image-and-text, so favor `image`; Douyin and video-first platforms favor `video`, generally with `music`; podcast platforms favor `speech` and `sfx`. If the conventional choice remains uncertain, follow the Trigger Boundary and ask.
3. **Decide whether an Expert is required:** Use `image` directly for ordinary illustrations. Use the Poster Expert for a cover with accurately typeset titles, selling points, dates, or calls to action. Use `video` directly for one simple clip. Use the Video Producer Expert for a complete edit with multiple shots, narration, music, or subtitles.
4. **Dependencies still follow `orchestration/dependency_rules.md`.** If a video must begin with a particular image or final cover, declare the dependency and complete the upstream task first.
5. The result may use one medium or combine several; do not assume a fixed number.

---

## Expert / Atomic Selection Rules

| Deliverable Condition | Execution Method |
|-----------------------|------------------|
| Social cover or promotional card with accurate text hierarchy | `expert/poster-design/poster-design.md` |
| Ordinary photograph, illustration, or product-atmosphere image | `skills/generate/image.md` |
| Complete multi-shot video with narration, music, or subtitles | `expert/video-producer/video-producer.md` |
| One simple short-video clip | `skills/generate/video.md` |
| Standalone music, speech, or sound effect | Corresponding audio atomic skill |

The Scenario remains responsible for platform copy and the deliverable mix. The Expert owns only the poster/cover or complete video itself.

---

## Non-Tool Outputs

Claude writes the post copy directly. It **uses no MCP tool, creates no file, and is not written to the asset registry**. It is part of the turn's response and is presented with the media assets. Match the target platform's voice, such as conversational text and emoji for Xiaohongshu, concise and punchy copy for Douyin, or formal and succinct copy for a professional platform. The copy must remain semantically consistent with the delivered media.

---

## Reference `declare` Block

The media mix is flexible. This representative example combines an image, video, and music. Add or remove tasks dynamically according to the selection rules:

```
<declare>
{
  "tasks": [
    {
      "id": "img1",
      "type": "image",
      "prompt": "A forest at dawn, filled with mist and warm, diffused yellow light among tall trees. Quiet and restorative, in a vertical composition with no people, suitable as a video cover.",
      "params": { "aspect_ratio": "9:16" }
    },
    {
      "id": "mus1",
      "type": "music",
      "prompt": "A misty forest at dawn with warm, diffused yellow light and a quiet, restorative atmosphere. New Age ambient music led by piano with string pads and natural birdsong, approximately 70 BPM, no vocals.",
      "params": { "duration_seconds": 30, "instrumental": true }
    },
    {
      "id": "vid1",
      "type": "video",
      "prompt": "A forest at dawn, filled with mist and warm, diffused yellow light among tall trees. The camera moves slowly forward as mist drifts between the trees and the light changes subtly. No people or dialogue.",
      "params": { "duration_seconds": 15, "aspect_ratio": "9:16" },
      "depends_on": "img1"
    }
  ]
}
</declare>
```

Copy does not appear in `declare` because it is not a tool task; return it as ordinary text with the results.

The cover and video in this example are simple assets, so they use atomic skills directly. If the user requests accurate title layout or a complete edit, replace `img1` or `vid1` with the atomic task fragment expanded by the corresponding Expert. Do not copy the Expert's internal steps into the Scenario file.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| Media assets selected for the request | A flexible number and combination of images, videos, and audio |
| Copy | Platform-appropriate text shown directly with the results; no file created |
