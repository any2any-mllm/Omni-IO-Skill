#!/usr/bin/env python3
"""
Omni-IO MCP Server
Unified tool service for an omni-modal input/output skill set, providing all understanding and generation capabilities.

Start with:
  python mcp/server.py

Alternatively, let the host agent start it automatically through `mcp_servers` in skill.yaml.
"""

import sys
from pathlib import Path
from typing import Optional

# Ensure mcp/ is on sys.path so generate, understand, and utility can be imported.
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load API keys from config/.env.
# override=True replaces empty placeholders passed by the host via skill.yaml env.
load_dotenv(Path(__file__).parent.parent / "config" / ".env", override=True)

import generate as g
import understand as u
import utility as ut
from registry import registry

mcp = FastMCP(
    "omni-io",
    instructions="Omni-modal skill set for understanding and generating images, video, audio, 3D content, and documents, with asset-registry management",
)


# ════════════════════════════════════════════════════════════════
# Understanding tools
# ════════════════════════════════════════════════════════════════

@mcp.tool()
async def understand_video(video_url: str) -> dict:
    """
    Understand video content with the Gemini API.
    Returns: { "description": "...", "timeline": [{"time": "00:00-00:15", "description": "..."}] }
    """
    return await u.understand_video(video_url)


@mcp.tool()
async def understand_audio(audio_url: str, subtype: str = "music") -> dict:
    """
    Understand audio content. Prefer the Gemini API when GEMINI_API_KEY is configured;
    one call handles every subtype. If it is unavailable or fails, fall back by subtype:
    "speech" → Whisper transcription (OPENAI_API_KEY, paid cloud API), returning transcript;
    "music" / "sfx" → Qwen2-Audio analysis (QWEN_API_KEY), returning analysis.
    """
    return await u.understand_audio(audio_url, subtype)


@mcp.tool()
async def understand_document(document_url: str) -> dict:
    """
    Extract document content with Mistral OCR 3.
    Returns: { "description": "summary", "content": "body as Markdown, ≤4,000 characters" }
    """
    return await u.understand_document(document_url)


@mcp.tool()
async def understand_3d(file_url: str) -> dict:
    """
    Analyze a 3D model. trimesh extracts geometry metadata. When Blender is installed,
    headless Blender with Cycles renders a textured and lit isometric view. If Blender
    is unavailable, fails, or times out, fall back to solid-color multi-angle matplotlib renders.
    Returns: { "description": "...", "mesh_info": {...}, "render_paths": [...], "render_method": "blender" | "trimesh_fallback" }
    Claude reads each render path for semantic description. For trimesh_fallback, tell
    the user honestly that the renders have no materials and show geometry only.
    """
    return await u.understand_3d(file_url)


# ════════════════════════════════════════════════════════════════
# Generation tools
# ════════════════════════════════════════════════════════════════

@mcp.tool()
async def generate_image(
    prompt: str,
    aspect_ratio: str = "1:1",
    quality: str = "standard",
) -> dict:
    """
    Generate an image. The provider is selected in config.yaml: fal / openai.
    aspect_ratio: "1:1" / "16:9" / "9:16" / "4:3" / "3:4"
    quality: "standard" / "hd"
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_image(prompt, aspect_ratio, quality)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_video(
    prompt: str,
    duration_seconds: int = 10,
    aspect_ratio: str = "16:9",
    first_frame_url: Optional[str] = None,
) -> dict:
    """
    Generate video. The provider is selected in config.yaml: wan / kling.
    first_frame_url: When depending on an upstream image, Claude extracts and injects
    this value from the upstream result. Local paths are supported.
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_video(prompt, duration_seconds, aspect_ratio, first_frame_url)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_music(
    prompt: str,
    duration_seconds: int = 30,
    instrumental: bool = True,
) -> dict:
    """
    Generate music. The provider is selected in config.yaml: Hugging Face (default,
    free) or ElevenLabs (paid subscription, highest quality).
    instrumental: True requests an instrumental track with no vocals.
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_music(prompt, duration_seconds, instrumental)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_sfx(
    prompt: str,
    duration_seconds: float = 15.0,
) -> dict:
    """
    Generate a sound effect with ElevenLabs Sound Effects.
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_sfx(prompt, duration_seconds)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_speech(
    text: str,
    voice: str = "neutral",
    language: str = "zh-CN",
    speed: float = 1.0,
) -> dict:
    """
    Synthesize speech. The provider is selected in config.yaml: edge_tts (default,
    free), OpenAI, or ElevenLabs.
    voice: one of six semantic categories—neutral, male, female, warm, authoritative,
    cheerful—supported by all three providers, or a provider-native voice ID passed
    through unchanged. language affects Edge voice selection only. speed: 0.5–2.0.
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_speech(text, voice, language, speed)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_3d(
    prompt: str,
    reference_image_url: Optional[str] = None,
) -> dict:
    """
    Generate a 3D model. The provider is selected in config.yaml: Tripo / Meshy.
    reference_image_url: When depending on an upstream image, Claude extracts and
    injects this value from the upstream result.
    Always outputs GLB; conversion to OBJ, FBX, or other formats is not supported.
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_3d(prompt, reference_image_url)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_ppt(
    structure: dict,
    style: str = "professional",
) -> dict:
    """
    Generate a PowerPoint with python-pptx, rendered entirely locally without an API key.
    The calling agent—Claude, Codex, or another host—plans the content before the call.
    The MCP server does not call an LLM.
    structure: {"title": "Title", "slides": [{"title": "Slide title", "points": ["Point 1", "Point 2"]}, ...]}
    style: "professional" / "academic" / "creative"
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_ppt(structure, style)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_word(
    structure: dict,
    style: str = "professional",
) -> dict:
    """
    Generate a Word document with python-docx, rendered entirely locally without an API key.
    The calling agent plans the content before the call. The MCP server does not call an LLM.
    structure: {"title": "Title", "sections": [{"heading": "Section heading", "paragraphs": ["Paragraph 1", ...]}, ...]}
    style: "professional" / "academic" / "report" (recorded in params_used only;
    it does not currently affect rendering).
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_word(structure, style)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_pdf(
    structure: dict,
    style: str = "professional",
) -> dict:
    """
    Generate a PDF with ReportLab, rendered entirely locally without an API key.
    The calling agent plans the content before the call. The MCP server does not call an LLM.
    structure: {"title": "Title", "sections": [{"heading": "Section heading", "paragraphs": ["Paragraph 1", ...]}, ...]}
    style: "professional" / "academic" (recorded in params_used only; it does not
    currently affect rendering).
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_pdf(structure, style)
    return registry.register(**_to_registry_kwargs(result))


@mcp.tool()
async def generate_excel(
    structure: dict,
    style: str = "professional",
) -> dict:
    """
    Generate an Excel workbook with openpyxl, rendered entirely locally without an API key.
    The calling agent plans the content before the call. The MCP server does not call an LLM.
    structure: {"title": "Title", "sheets": [{"name": "Sheet name", "headers": ["Column 1", ...], "rows": [["Value 1", ...], ...]}, ...]}
    style: "professional" / "academic" / "creative" (sets the header background color).
    Returns an asset object already written to the asset registry.
    """
    result = await g.generate_excel(structure, style)
    return registry.register(**_to_registry_kwargs(result))


# ════════════════════════════════════════════════════════════════
# Utilities
# ════════════════════════════════════════════════════════════════

@mcp.tool()
async def search(query: str, count: int = 5) -> dict:
    """
    Search the web with Brave Search.
    Returns: { "query": "...", "results": [{"title": "...", "url": "...", "description": "..."}] }
    """
    return await ut.search(query, count)


@mcp.tool()
async def browse(url: str, max_chars: int = 6000) -> dict:
    """
    Browse a webpage with Playwright and extract the body. Waits for network idle to
    support asynchronous SPA rendering; if the first extraction is too short, possibly
    only navigation/loading UI, it scrolls and retries with backoff.
    max_chars: Maximum returned body length, 6,000 by default; increase for more content.
    Returns: { "url": "...", "content": "...", "truncated": bool,
               "warning": "message when content remains too short; otherwise null" }
    """
    return await ut.browse(url, max_chars)


# ════════════════════════════════════════════════════════════════
# Configuration check
# ════════════════════════════════════════════════════════════════

@mcp.tool()
def check_config() -> dict:
    """
    Check active provider configuration and API-key status for each modality.
    Call on the first multimodal task so the user can see ready and unconfigured features.
    Returns: { "active_providers": [...], "ready": [...], "missing": [...], "always_free": [...], "notes": [...] }
    """
    import os
    import yaml
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    try:
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception as e:
        return {"error": f"Unable to read config.yaml: {e}"}

    def _resolve(val):
        if isinstance(val, str) and val.startswith("${") and val.endswith("}"):
            return os.environ.get(val[2:-1], "")
        return val or ""

    # Map each modality to: display name, active provider name, env var(s), free note
    checks = [
        # (display, section, modality, free_modality=False)
        ("Image generation",   "generate", "image",   False),
        ("Video generation",   "generate", "video",   False),
        ("Music generation",   "generate", "music",   False),
        ("Sound-effect generation", "generate", "sfx", False),
        ("Speech synthesis",   "generate", "speech",  False),
        ("3D generation",      "generate", "3d",      False),
        ("Video understanding", "understand", "video", False),
        ("Audio analysis",     "understand", "audio_analysis", False),
        ("Document OCR",       "understand", "document", False),
        ("Speech recognition", "understand", "speech", False),
        ("Web search",         None,       None,      False),
    ]

    free_always = [
        {"modality": "Image understanding", "note": "Claude native vision; no key required"},
        {"modality": "3D understanding", "note": "Local trimesh; renders with Blender when installed, otherwise matplotlib; no key required"},
        {"modality": "Document generation (PPT/Word/PDF/Excel)", "note": "Local libraries; completely free"},
        {"modality": "Code/webpage generation", "note": "Claude native capability; no key required; call register_asset() afterward"},
        {"modality": "Markdown generation", "note": "Claude native capability; no key required; call register_asset() afterward"},
        {"modality": "Speech synthesis", "note": "Edge TTS by default; completely free; no key required"},
        {"modality": "Web browsing", "note": "Local Playwright; completely free"},
    ]

    ready = []
    missing = []
    active_providers = []

    for display, section, modality, _ in checks:
        if section is None:
            # Brave Search
            key = os.environ.get("SEARCH_API_KEY", "")
            entry = {"modality": "Web search", "provider": "Brave Search", "env_var": "SEARCH_API_KEY"}
            if key:
                ready.append({"modality": "Web search", "provider": "Brave Search"})
            else:
                entry["note"] = "2,000 free queries per month; see setup/api_guide.md"
                missing.append(entry)
            continue

        try:
            modality_cfg = cfg[section][modality]
            provider = modality_cfg["provider"]
            provider_cfg = modality_cfg["providers"][provider]
        except KeyError:
            continue

        active_providers.append({"modality": display, "provider": provider})

        # edge_tts needs no key
        if provider == "edge_tts":
            ready.append({"modality": display, "provider": "edge_tts (completely free; no key required)"})
            continue

        api_key_raw = provider_cfg.get("api_key", "")
        api_key = _resolve(api_key_raw)
        env_var = api_key_raw[2:-1] if str(api_key_raw).startswith("${") else "(unknown)"

        if api_key:
            ready.append({"modality": display, "provider": provider})
        else:
            alt_provider = [p for p in modality_cfg["providers"] if p != provider]
            entry = {
                "modality": display,
                "active_provider": provider,
                "env_var": env_var,
                "note": f"Set {env_var} to enable this feature",
            }
            if alt_provider:
                entry["alternative"] = f"Or switch the provider to {alt_provider[0]} in config.yaml; see setup/api_guide.md"
            missing.append(entry)

    notes = []
    if os.environ.get("GEMINI_API_KEY", ""):
        notes.append(
            "GEMINI_API_KEY is configured: audio understanding (speech recognition plus music/SFX analysis) "
            "will prefer one Gemini call. The Whisper/Qwen statuses below apply only as fallbacks."
        )

    return {
        "active_providers": active_providers,
        "ready": ready,
        "missing": missing,
        "always_free": free_always,
        "notes": notes,
        "config_files": {
            "api_keys": "config/.env (copy from config/.env.example, then enter keys)",
            "provider_switch": "config/config.yaml (change a provider field to switch services)",
            "guide": "setup/api_guide.md (detailed setup and switching instructions)",
        },
    }


# ════════════════════════════════════════════════════════════════
# Asset Registry tools
# ════════════════════════════════════════════════════════════════

@mcp.tool()
def get_asset(asset_id: str) -> dict:
    """
    Look up a completed asset in the asset registry.
    Returns its record, or { "error": "not found" }.
    """
    record = registry.get(asset_id)
    return record if record else {"error": f"asset_id '{asset_id}' does not exist"}


@mcp.tool()
def register_asset(
    asset_type: str,
    url: str,
    description: str,
    params_used: Optional[dict] = None,
    subtype: Optional[str] = None,
    depends_on: Optional[str] = None,
) -> dict:
    """
    Register a file produced natively by Claude without a generate_* MCP tool.
    This covers (1) modalities without a dedicated generator, currently code/webpages
    and Markdown, and (2) final deliverables assembled by an Expert, such as posters
    and fully edited videos. Expert outputs are created through a code task internally,
    but asset_type must describe the actual result (for example image or video), not code,
    because the registry records what a file is rather than how it was made.
    After writing a file with Write/Edit, call this tool to assign an asset_id so later
    turns can use asset_ref and get_asset/list_assets can find it.
    asset_type: broad type, e.g. code, document (Markdown), image (Expert poster),
                or video (Expert-produced video)
    subtype: e.g. webpage, markdown, poster, or produced_video
    url: absolute local file path
    depends_on: for a file based on one existing asset_id, records version lineage.
                This is not an in-place update; every call creates a new asset_id.
    Returns an asset object already written to the asset registry.
    """
    return registry.register(
        asset_type=asset_type, url=url, description=description,
        params_used=params_used or {}, subtype=subtype, depends_on=depends_on,
    )


@mcp.tool()
def list_assets() -> dict:
    """
    List every completed globally persisted asset shared across sessions, newest first.
    Returns: { "assets": [...] }
    """
    return {"assets": registry.list_all()}


@mcp.tool()
def set_turn(turn_id: str) -> dict:
    """
    Set the current turn ID. Newly registered assets record this turn.
    Claude calls it at the start of each turn to distinguish asset provenance.
    """
    registry.set_turn(turn_id)
    return {"turn_id": turn_id}


# ════════════════════════════════════════════════════════════════
# Helper functions
# ════════════════════════════════════════════════════════════════

def _to_registry_kwargs(result: dict) -> dict:
    """Convert a generation-function result into registry.register arguments."""
    return {
        "asset_type": result["type"],
        "url": result["url"],
        "description": result["description"],
        "params_used": result.get("params_used", {}),
        "subtype": result.get("subtype"),
        "depends_on": result.get("depends_on"),
    }


# ════════════════════════════════════════════════════════════════
# Entry point
# ════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    mcp.run()
