# Scenario: Event Collateral

## Scenario Description

The user needs invitation, promotional, or commemorative visual/audio materials for a specific event such as a wedding, birthday, party, or announcement. Deliverables may include invitation or poster graphics, ambient music, and teaser or recap videos. **The deliverable mix is flexible** and depends on the event and request.

---

## Trigger Examples

- "Create a wedding invitation."
- "Make ambient background music and an invitation for my birthday party."
- "Create an event teaser video with an invitation poster."
- "Turn these event photos into a recap video."

---

## Trigger Boundary

**Trigger when:** The user wants invitation, promotional, or commemorative materials for a specific event such as a wedding, birthday, or party.

**Do not trigger when:** The user only wants an ordinary poster or image unrelated to a specific event. For an ordinary poster with accurate text and professional layout, call `expert/poster-design/poster-design.md` directly. For an ordinary image, use `skills/generate/image.md`.

**When uncertain:** Confirm the event type, date, time, location, and required collateral.

---

## Typical Input Assets

| Asset Type | Description | Required? |
|------------|-------------|-----------|
| Text description | Event type, theme, style, date, time, location, and related information | Required |
| Image | Optional existing event photos or references for a recap video or style | Optional |

---

## Media and Deliverable Selection Rules

1. **Invitations and posters** generally use `expert/poster-design/poster-design.md`. The Expert locks exact copy such as dates, locations, and names; generates text-free visual assets; uses the existing code path for layout; and checks the final poster. Use the `image` atomic skill directly only for an ordinary event-atmosphere image without precise text layout.
2. Use `generate_music` for ambient background music that matches the event.
3. **Choose video by complexity:** Use the `video` atomic skill for one simple event-atmosphere clip. Use `expert/video-producer/video-producer.md` for a complete teaser or recap that needs multiple shots, photo integration, music, narration, subtitles, or final editing.
4. **Existing photos:** Use native vision to understand the photos first. The Video Producer Expert plans their use, storyboard, and assembly for a complete recap.
5. **Dependencies:** If the final poster becomes the teaser's first frame or visual reference, the Scenario passes the Poster Expert's final poster asset to the Video Producer Expert. The expanded tasks still follow the existing dependency rules.
6. Treat the invitation's time, location, event name, and personal names as locked copy. The Poster Expert typesets them deterministically during assembly rather than asking the image model to render them.

---

## Expert / Atomic Selection Rules

| Deliverable Condition | Execution Method |
|-----------------------|------------------|
| Invitation/poster with exact copy and professional layout | `expert/poster-design/poster-design.md` |
| Ordinary event-atmosphere image | `skills/generate/image.md` |
| Complete multi-shot teaser or recap | `expert/video-producer/video-producer.md` |
| One simple event shot | `skills/generate/video.md` |
| Standalone ambient music | `skills/generate/audio/music.md` |

The Scenario combines these deliverables. The respective Experts own decomposition, assembly, and review inside the poster or video.

---

## Reference `declare` Block

This representative example creates an invitation background and ambient music. Adapt it using the rules above:

```
<declare>
{
  "tasks": [
    {
      "id": "img1",
      "type": "image",
      "prompt": "A minimalist, warm wedding-invitation design in ivory and gold, with floral line-art decoration and open space reserved for the couple's names, date, time, and location.",
      "params": { "aspect_ratio": "3:4" }
    },
    {
      "id": "mus1",
      "type": "music",
      "prompt": "Warm, romantic wedding ambience led by strings and piano, with a gentle tempo and no vocals.",
      "params": { "duration_seconds": 60, "instrumental": true }
    }
  ]
}
</declare>
```

`img1` and `mus1` are independent, separate deliverables.

---

## Expected Outputs

| Asset Type | Description |
|------------|-------------|
| image | Invitation or poster graphic |
| audio (`music`) | Ambient event music |
| video, when needed | Event teaser or recap |
