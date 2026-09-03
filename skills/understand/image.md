# Skill: Image Understanding

## Trigger

The user uploads an image and asks to:

- Describe its content: "What is in this image?"
- Extract specific information: "What text is shown?" or "How many people are there?"
- Analyze style or emotion: "What style is this image?"
- Use it as a reference for generation: "Create something based on this image."

For an understanding-only request with no generation, **do not output a `<declare>` block**. Analyze and respond directly.

---

## Input and Tool Selection

Claude has native vision and **does not need an MCP tool**:

| Input Source | Handling |
|--------------|----------|
| Image uploaded by the user | Analyze directly with native vision |
| Web image URL | Analyze directly with native vision |
| Local file path | Read the path with the **Read tool** so Claude receives the image visually |
| `asset_id` of an image generated in this turn | Call `get_asset(asset_id)` for the local path, then read it |

---

## Analysis Dimensions

Choose dimensions relevant to the user's intent; do not always cover all of them.

**Content description**

- Scene type: indoor, outdoor, natural, urban
- Main subjects and their relationships
- Spatial arrangement and composition

**Text extraction (OCR)**

- Extract all readable text
- Preserve original structure, such as tables and heading hierarchy

**Style analysis**

- Visual style: realistic, illustration, anime, oil painting, etc.
- Color and lighting: warm/cool, light/dark, time of day
- Camera characteristics: apparent focal length, depth of field, angle

**Object and attribute recognition**

- Object categories, counts, colors, and materials
- People: age, clothing, expression, and pose
- Brands, logos, and symbols

**Emotion and atmosphere**

- Overall emotional tone: warm, austere, tense, calm, etc.
- Narrative interpretation: what story the image conveys

---

## Procedure

1. **Determine the goal:** Identify the requested dimensions and skip irrelevant ones.
2. **Observe the image:** Analyze each selected dimension.
3. **Organize the output:** Choose a format appropriate to the request.
4. **Prepare downstream generation:** If the analysis will feed a generation task, rewrite key observations into prompt-ready form.

---

## Output Formats

**Question answering**, such as "What is in the image?": A concise natural-language paragraph.

**Information extraction**, such as OCR or counts: A structured list or table.

**Generation reference**, such as "Create something in this style": A standardized style description that can prefix a generation prompt:

```
Style description: [color palette] + [lighting] + [visual style] + [composition]
Example: "Warm yellow palette, side lighting at sunset, realistic photography, shallow-depth-of-field portrait composition."
```

---

## Integration with Other Skills

| Follow-Up | Integration |
|-----------|-------------|
| Generate a similar image | Add the style description to the `generate/image` prompt |
| Generate a 3D model | Pass the subject description to `generate/3d` as `prompt` |
| Create a video | Add the scene description to the `generate/video` prompt |
