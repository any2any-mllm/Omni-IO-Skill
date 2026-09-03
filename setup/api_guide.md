# API Key Guide

Each modality provides two provider options. Switch between them with the `provider` field in `config/config.yaml`.

---

## Quick Start: Zero-Cost Features

The following features require no payment; register free accounts where indicated:

| Feature | Provider | How to Enable |
|---------|----------|---------------|
| 🆓 Image understanding | Claude native | No configuration required |
| 🆓 Speech synthesis | Microsoft Edge TTS | No configuration required; enabled by default in `config.yaml` |
| 🆓 Document generation (PPT/Word/PDF/Excel) | Local libraries | No configuration required |
| 🆓 Code/webpage generation | Claude native | No configuration required; call `register_asset()` after generation |
| 🆓 Markdown generation | Claude native | No configuration required; call `register_asset()` after generation |
| 🆓 Web browsing | Local Playwright | No configuration required |
| 🟢 Image generation | fal.ai FLUX.1-schnell | Register with fal.ai; new users receive US$10 in free credit |
| 🟢 Sound-effect generation | ElevenLabs | Register with ElevenLabs; includes a free monthly allowance |
| 🟢 Music generation | Hugging Face MusicGen | Register with Hugging Face; includes a free inference allowance |
| 🟢 Video understanding | Gemini 2.5 Flash | Register with Google AI Studio; 1M tokens free per day |
| 🟢 Document understanding (OCR) | Mistral | Register with Mistral; free allowance available |
| 🟢 3D generation | Tripo3D | Register with Tripo3D; free credits included |
| 🟢 Web search | Brave Search | Register with Brave; 2,000 free requests per month |

---

## Provider Details by Modality

### Image Generation

#### Default: fal.ai (FLUX.1-schnell) — 🟢 Free allowance
- **Cost:** US$10 free credit for new users, then approximately US$0.003 per image
- **Quality:** High quality and fast (3–8 seconds per image)
- **Get a key:** Register at fal.ai → Console → API Keys → Create Key
- **Configuration:** `FAL_API_KEY=<your-key>`

#### Alternative: OpenAI (gpt-image-2) — 💰 Paid
- **Cost:** Approximately US$0.04–0.08 per image at standard quality
- **Quality:** Among the highest-quality options currently available
- **Get a key:** Register at OpenAI Platform → Add credit → API Keys → Create Key
- **Configuration:** `OPENAI_API_KEY=<your-key>`
- **Switch:** Set `generate.image.provider` in `config.yaml` to `openai`

---

### Video Generation

#### Default: Wan2.7 (DashScope) — 💰 Free allowance for new users
- **Cost:** DashScope provides free usage to new users, then charges by the second
- **Quality:** Smooth motion and strong results for Chinese-language scenes
- **Get a key:** Register with Alibaba Cloud Model Studio (DashScope) → API Key Management → Create Key
- **Configuration:**
  ```
  WAN_API_KEY=<your-key>
  WAN_WORKSPACE_ID=<your-workspace-id>
  ```
- **Get the Workspace ID:** Open the dropdown in the upper-left of the Model Studio console → Current Workspace → Copy ID. The format is `ws-xxxxxxxxxxxxxxxx`.
- **⚠️ Required for the international service (Singapore):** The international API uses a workspace-specific domain (`{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com`) and returns HTTP 401 if the ID is omitted. The field may be left blank for the mainland China service.

#### Alternative: Kling 1.6 (via fal.ai) — 🟢 Uses the same `FAL_API_KEY`
- **Cost:** Uses fal.ai credit; US$10 in free credit generates approximately 5–10 videos
- **Quality:** One of the best all-around video-generation models currently available
- **Get a key:** Uses the same `FAL_API_KEY` as image generation; no additional registration
- **Switch:** Set `generate.video.provider` in `config.yaml` to `kling`

---

### Music Generation

#### Default: Hugging Face MusicGen — 🟢 Free
- **Cost:** Free Hugging Face inference allowance, with rate limits and slower responses
- **Quality:** General-purpose quality suitable for quick validation; supports about 30 seconds at most
- **Get a key:** Register with Hugging Face → Settings → Access Tokens → Create Token
- **Configuration:** `HUGGINGFACE_API_KEY=<your-token>`

#### Alternative: ElevenLabs Eleven Music v2 — 💰 Paid subscription
- **Cost:** Requires an ElevenLabs paid subscription with Music API access; ordinary API keys do not include this permission. Uses the same `ELEVENLABS_API_KEY` as sound-effect generation and speech synthesis.
- **Quality:** Highest quality; supports up to 10 minutes, vocals, multiple languages, and commercial licensing
- **Get a key:** Register with ElevenLabs → Upgrade to a plan that includes Music → Profile → API Keys
- **Configuration:** `ELEVENLABS_API_KEY=<your-key>`
- **Switch:** Set `generate.music.provider` in `config.yaml` to `elevenlabs`

---

### Sound-Effect Generation

#### Only option: ElevenLabs Sound Effects — 🟢 Free tier available
- **Cost:** A free monthly allowance is included at registration; excess usage is charged by character
- **Quality:** Currently among the best sound-effect generation options
- **Get a key:** Register with ElevenLabs → Profile in the upper-right → API Key → Copy
- **Configuration:** `ELEVENLABS_API_KEY=<your-key>`

---

### Speech Synthesis (TTS)

#### Default: Microsoft Edge TTS — 🆓 Completely free
- **Cost:** Free, with no key or usage limit
- **Quality:** Excellent Chinese voices, including XiaoxiaoNeural; English is also supported
- **Configuration:** None; enabled by default in `config.yaml`
- **Optional custom voice:** Change `generate.speech.providers.edge_tts.voice` in `config.yaml`
  - Chinese female: `zh-CN-XiaoxiaoNeural` (default), `zh-CN-XiaoyiNeural`
  - Chinese male: `zh-CN-YunxiNeural`, `zh-CN-YunjianNeural`

#### Alternative: OpenAI TTS — 💰 Paid
- **Cost:** Approximately US$0.015 per 1,000 characters for `tts-1`; uses `OPENAI_API_KEY`
- **Quality:** Highly natural, with several English voices
- **Switch:** Set `generate.speech.provider` in `config.yaml` to `openai`

#### Alternative: ElevenLabs TTS — 🟢 Free tier available
- **Cost:** 10,000 characters free per month; uses `ELEVENLABS_API_KEY`
- **Quality:** Highest quality, with emotion control
- **Switch:** Set `generate.speech.provider` in `config.yaml` to `elevenlabs`

---

### 3D Generation

#### Default: Tripo3D v2 — 🟢 Free credits upon registration
- **Cost:** Free credits upon registration, then paid
- **Quality:** High-quality PBR materials and image-to-3D support
- **Get a key:** Register at tripo3d.ai → Console → API Keys
- **Configuration:** `TRIPO_API_KEY=<your-key>`

#### Alternative: Meshy v2 — 🟢 Free tier available
- **Cost:** Free tier with a limited number of uses per month
- **Quality:** Fast with good quality
- **Get a key:** Register at meshy.ai → Console → API Keys
- **Configuration:** `MESHY_API_KEY=<your-key>`
- **Switch:** Set `generate.3d.provider` in `config.yaml` to `meshy`

---

### Understanding Tools

| Modality | Provider | Cost | Configuration Variable |
|----------|----------|------|------------------------|
| Image understanding | Claude native vision | 🆓 No configuration | — |
| Document understanding (plain text / text-based PDF) | Claude native Read | 🆓 No configuration | — |
| Document understanding (.docx / .pptx / scanned PDF) | Mistral OCR | 🟢 Free tier | `MISTRAL_API_KEY` |
| Video understanding | Gemini 2.5 Flash | 🟢 Free tier | `GEMINI_API_KEY` |
| Speech recognition / audio analysis (preferred) | Gemini 2.5 Flash (one call covers speech/music/SFX) | 🟢 Free tier | `GEMINI_API_KEY` (shared with video understanding) |
| Speech recognition (fallback when Gemini is unavailable) | Whisper (OpenAI) | 💰 US$0.006/minute | `OPENAI_API_KEY` |
| Audio analysis (fallback when Gemini is unavailable) | Qwen2-Audio (DashScope) | 🟢 Free allowance | `QWEN_API_KEY` |
| 3D analysis | trimesh (local; uses Blender for rendering when installed, otherwise matplotlib) | 🆓 Free | No configuration |

**Get Gemini:** Go to Google AI Studio → "Get API key" → Create a project and generate a key.

**⚠️ Gemini notes:**

- The SDK is the newer `google-genai`, not the deprecated `google-generativeai`.
- Current model: `gemini-2.5-flash`; `gemini-2.0-flash` has been retired in some regions/projects.
- The new Google AI Studio key format begins with `AQ.`, not the older `AIza` prefix.
- An error containing `limit: 0` means billing is not enabled or the free allowance is zero for that Google Cloud project. Enable billing in Google Cloud Console.
- One `GEMINI_API_KEY` enables both video understanding and audio understanding (speech recognition plus music/sound-effect analysis).

**Get Mistral:** Register at console.mistral.ai → API Keys → Create Key.

---

### Audio Analysis

#### Only option: Qwen2-Audio (DashScope) — 🟢 Free allowance
- **Capabilities:** Genre recognition, mood detection, BPM estimation, and instrument recognition for music; dominant-sound detection, spatial characteristics, and ambience descriptions for environmental sounds and effects
- **Cost:** DashScope provides a free allowance; see the Alibaba Cloud Model Studio console for details
- **Get a key:** Register with [Alibaba Cloud Model Studio](https://dashscope.aliyuncs.com) → API Key Management → Create Key
- **Configuration:** `QWEN_API_KEY=<your-key>`
- **Reuse tip:** If `WAN_API_KEY` is already configured for Wan2.7 video generation, both services use the **same platform**, Alibaba Cloud DashScope. You can enter the same key without registering again.

---

### Public File Hosting (Cloudinary)

Some generation APIs, such as Meshy image-to-3D, accept only public HTTP URLs and not local paths. In these cases, Cloudinary automatically uploads a local generated file and returns a publicly accessible URL.

- **Cost:** Free tier with 25 GB/month; no credit card required
- **When used:** Called automatically only when needed, such as image-to-3D with the Meshy provider
- **Get credentials:** Register at cloudinary.com → Dashboard, where the Cloud name, API Key, and API Secret are displayed
- **Configuration:**
  ```
  CLOUDINARY_CLOUD_NAME=<your-cloud-name>
  CLOUDINARY_API_KEY=<your-api-key>
  CLOUDINARY_API_SECRET=<your-api-secret>
  ```

> Cloudinary is not required when Meshy is not used. The default Tripo provider does not need it.

---

## Switching Providers

1. Open `config/config.yaml`.
2. Find the relevant modality and change its `provider` field.
3. Ensure that the environment variable for the corresponding `api_key` is configured in `config/.env`.
4. Restart the MCP server by reloading the MCP configuration in Claude Code.

**Example: switch image generation from fal to OpenAI**

```yaml
generate:
  image:
    provider: openai    # ← Change this line (original value: fal)
```

---

## Recommended Configurations

### Start at Zero Cost (Immediately Available)

No payment is required. Register four free accounts:

```
FAL_API_KEY=         # fal.ai (image generation, US$10 free credit)
ELEVENLABS_API_KEY=  # ElevenLabs (sound effects, free tier)
HUGGINGFACE_API_KEY= # Hugging Face (music, free)
TRIPO_API_KEY=       # Tripo3D (3D, free registration credits)
```

TTS defaults to Edge TTS and requires no configuration. Document generation runs locally and also requires no configuration.

Available: image, sound-effect, music, TTS, 3D, and document generation  
Unavailable: video generation (requires `WAN_API_KEY`) and video understanding (requires `GEMINI_API_KEY`)

### Full Feature Set

Add the following to the zero-cost configuration:

```
WAN_API_KEY=      # Video generation (Wan2.7)
GEMINI_API_KEY=   # Preferred provider for video + audio understanding (free tier)
MISTRAL_API_KEY=  # Document OCR (free tier)
OPENAI_API_KEY=   # Speech recognition (Whisper), high-quality TTS (optional)
QWEN_API_KEY=     # Audio/music analysis (same platform as WAN_API_KEY; may use the same key)
SEARCH_API_KEY=   # Web search (free tier)
```
