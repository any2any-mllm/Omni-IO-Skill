# Feature List

During initial setup, show this list to the user exactly as written and ask which features they want to enable. Do not proactively request configuration for modalities the user does not mention.

---

## Available Immediately Without Configuration

- 🆓 Image understanding (Claude's native vision)
- 🆓 Document generation (PPT / Word / PDF / Excel, using local libraries)
- 🆓 Code / webpage generation (Claude's native capabilities)
- 🆓 Markdown generation (Claude's native capabilities)
- 🆓 Speech synthesis (Microsoft Edge TTS, enabled by default in `config.yaml`)
- 🆓 Web browsing (local Playwright)

## Requires a Free Account or Payment

| Feature | Default Provider | Cost |
|---------|------------------|------|
| Image generation | fal.ai | 🟢 US$10 free credit upon registration |
| Sound-effect generation | ElevenLabs | 🟢 Free monthly allowance |
| Music generation | Hugging Face | 🟢 Free inference allowance |
| 3D generation | Tripo3D | 🟢 Free credits upon registration |
| Video understanding | Gemini | 🟢 1M tokens free per day |
| Document OCR | Mistral | 🟢 Free tier |
| Audio analysis | Qwen (DashScope) | 🟢 Free allowance |
| Web search | Brave Search | 🟢 2,000 free requests per month |
| Video generation | Wan2.7 (DashScope) | 💰 Free allowance for new users, then pay-as-you-go |
| Speech recognition | Whisper (OpenAI) | 💰 Pay-as-you-go |

For alternative providers, instructions for obtaining keys, and switching methods, see [`setup/api_guide.md`](api_guide.md).
