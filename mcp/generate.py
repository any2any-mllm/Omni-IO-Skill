"""
Generation-tool implementations with dual-provider support selected through provider fields in config/config.yaml.

To switch, change the modality's provider in config/config.yaml and restart the MCP server.
"""

import asyncio
import base64
import os
import uuid
from pathlib import Path
from typing import Optional

import httpx
import yaml


# ─── Configuration loading ─────────────────────────────────────────────────────

_CONFIG_CACHE: Optional[dict] = None


def _config() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        with open(config_path, encoding="utf-8") as f:
            _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE


def _resolve(value) -> str:
    """Resolve ${ENV_VAR} placeholders."""
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.environ.get(value[2:-1], "")
    return value or ""


def _provider_cfg(section: str, modality: str) -> dict:
    """Return the active provider config with env vars resolved."""
    modality_cfg = _config()[section][modality]
    provider = modality_cfg["provider"]
    cfg = {k: _resolve(v) for k, v in modality_cfg["providers"][provider].items()}
    cfg["provider"] = provider
    return cfg


def _require_key(cfg: dict, key: str = "api_key") -> str:
    val = cfg.get(key, "")
    if not val:
        provider = cfg.get("provider", "?")
        raise RuntimeError(
            f"API key is not configured (provider={provider}). "
            "Set the corresponding variable in config/.env; see setup/api_guide.md."
        )
    return val


def _out_dir() -> str:
    d = os.path.expanduser(os.environ.get("OMNI_OUTPUT_DIR", str(Path.home() / "Documents" / "OmniIO")))
    os.makedirs(d, exist_ok=True)
    return d


def _uid() -> str:
    return uuid.uuid4().hex[:8]


async def _download(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url)
        r.raise_for_status()
        return r.content


async def _save_remote(url: str, prefix: str, suffix: str = "") -> str:
    """Download a remote URL and save locally. Returns local file path."""
    if not suffix:
        suffix = Path(url.split("?")[0]).suffix or ".bin"
    content = await _download(url)
    out_path = os.path.join(_out_dir(), f"{prefix}_{_uid()}{suffix}")
    with open(out_path, "wb") as f:
        f.write(content)
    return out_path


async def _upload_to_public(local_path: str) -> str:
    """Upload a local file to Cloudinary and return a public HTTPS URL.
    Use only when a downstream API requires an HTTP URL, such as Meshy image-to-3D.
    """
    cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME", "")
    api_key_cld = os.environ.get("CLOUDINARY_API_KEY", "")
    api_secret = os.environ.get("CLOUDINARY_API_SECRET", "")

    if not all([cloud_name, api_key_cld, api_secret]):
        raise RuntimeError(
            "Cloudinary is not configured, so the local file cannot be converted to a public URL "
            "required by Meshy image-to-3D.\n"
            "Register for a free account at cloudinary.com, then set these values in config/.env:\n"
            "  CLOUDINARY_CLOUD_NAME / CLOUDINARY_API_KEY / CLOUDINARY_API_SECRET\n"
            "See setup/api_guide.md."
        )

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(cloud_name=cloud_name, api_key=api_key_cld, api_secret=api_secret)
    result = await asyncio.to_thread(
        cloudinary.uploader.upload, local_path, resource_type="auto"
    )
    return result["secure_url"]


async def _first_frame_data_uri(path_or_url: Optional[str]) -> Optional[str]:
    """Normalize a first frame for the API: pass HTTP URLs through and convert local paths to base64 data URIs.
    Wan and Kling through fal.ai both support data:{mime};base64,{b64}.
    """
    if not path_or_url:
        return None
    if path_or_url.startswith(("http://", "https://")):
        return path_or_url
    b64, mime = await _to_base64(path_or_url)
    return f"data:{mime};base64,{b64}"


async def _to_base64(url_or_path: str) -> tuple[str, str]:
    """Return (base64_str, mime_type) from a URL or local file path."""
    mime_map = {
        ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".gif": "image/gif",
    }
    if url_or_path.startswith(("http://", "https://")):
        content = await _download(url_or_path)
        suffix = Path(url_or_path.split("?")[0]).suffix.lower()
    else:
        with open(url_or_path, "rb") as f:
            content = f.read()
        suffix = Path(url_or_path).suffix.lower()
    mime = mime_map.get(suffix, "image/png")
    return base64.b64encode(content).decode(), mime


# ─── Image generation ──────────────────────────────────────────────────────────

_ASPECT_OPENAI = {
    "1:1": "1024x1024", "16:9": "1792x1024",
    "9:16": "1024x1792", "4:3": "1365x1024", "3:4": "1024x1365",
}
_ASPECT_FAL = {
    "1:1": "square", "16:9": "landscape_16_9",
    "9:16": "portrait_16_9", "4:3": "landscape_4_3", "3:4": "portrait_4_3",
}


async def generate_image(prompt: str, aspect_ratio: str = "1:1", quality: str = "standard") -> dict:
    cfg = _provider_cfg("generate", "image")
    if cfg["provider"] == "openai":
        return await _image_openai(cfg, prompt, aspect_ratio, quality)
    if cfg["provider"] == "fal":
        return await _image_fal(cfg, prompt, aspect_ratio)
    raise ValueError(f"Unknown image-generation provider: {cfg['provider']}. Options: openai, fal")


async def _image_openai(cfg: dict, prompt: str, aspect_ratio: str, quality: str) -> dict:
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=_require_key(cfg))
    size = _ASPECT_OPENAI.get(aspect_ratio, "1024x1024")
    # gpt-image-2 accepts only low, medium, high, or auto.
    quality_map = {"standard": "auto", "hd": "high"}
    api_quality = quality_map.get(quality, quality)

    response = await client.images.generate(
        model=cfg.get("model", "gpt-image-2"),
        prompt=prompt, size=size, quality=api_quality, n=1,
    )
    img_data = response.data[0]
    # gpt-image-2 always returns b64_json.
    out_path = os.path.join(_out_dir(), f"img_{_uid()}.png")
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(img_data.b64_json))
    local_path = out_path
    description = await _auto_describe_image(local_path)

    return {
        "type": "image", "url": local_path, "description": description,
        "params_used": {"aspect_ratio": aspect_ratio, "quality": quality, "provider": "openai"},
    }


async def _image_fal(cfg: dict, prompt: str, aspect_ratio: str) -> dict:
    import fal_client
    os.environ["FAL_KEY"] = _require_key(cfg)

    image_size = _ASPECT_FAL.get(aspect_ratio, "square")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: fal_client.run(
            cfg.get("model", "fal-ai/flux/schnell"),
            arguments={"prompt": prompt, "image_size": image_size, "num_images": 1},
        ),
    )
    remote_url = result["images"][0]["url"]
    local_path = await _save_remote(remote_url, "img", ".png")
    description = await _auto_describe_image(local_path)

    return {
        "type": "image", "url": local_path, "description": description,
        "params_used": {"aspect_ratio": aspect_ratio, "provider": "fal"},
    }


async def _auto_describe_image(image_path: str) -> str:
    """Generate a brief description of a local image using GPT-4o-mini (optional)."""
    try:
        from openai import AsyncOpenAI
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return f"Image generated: {image_path}"
        b64, mime = await _to_base64(image_path)
        client = AsyncOpenAI(api_key=api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": "Describe the image's subject, color palette, and atmosphere in English in at most 80 words."},
            ]}],
            max_tokens=120,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return f"Image generated: {image_path}"


# ─── Video generation ──────────────────────────────────────────────────────────

async def generate_video(
    prompt: str,
    duration_seconds: int = 10,
    aspect_ratio: str = "16:9",
    first_frame_url: Optional[str] = None,
) -> dict:
    cfg = _provider_cfg("generate", "video")
    if cfg["provider"] == "wan":
        return await _video_wan(cfg, prompt, duration_seconds, aspect_ratio, first_frame_url)
    if cfg["provider"] == "kling":
        return await _video_kling(cfg, prompt, duration_seconds, aspect_ratio, first_frame_url)
    raise ValueError(f"Unknown video-generation provider: {cfg['provider']}. Options: wan, kling")


async def _video_wan(cfg: dict, prompt: str, duration_seconds: int, aspect_ratio: str, first_frame_url: Optional[str]) -> dict:
    api_key = _require_key(cfg)
    workspace_id = os.environ.get("WAN_WORKSPACE_ID", "")
    if not workspace_id:
        raise ValueError("WAN_WORKSPACE_ID is not configured. Enter the Model Studio Workspace ID in config/.env")
    base_url = f"https://{workspace_id}.ap-southeast-1.maas.aliyuncs.com"

    ratio_map = {"16:9": "16:9", "9:16": "9:16", "1:1": "1:1", "4:3": "4:3", "3:4": "3:4"}
    ratio = ratio_map.get(aspect_ratio, "16:9")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-DashScope-Async": "enable",
    }

    # Select the model and request format based on whether a first frame is present.
    if first_frame_url:
        model = "wan2.7-i2v-2026-04-25"
        first_frame = await _first_frame_data_uri(first_frame_url)
        inp: dict = {
            "prompt": prompt,
            "media": [{"type": "first_frame", "url": first_frame}],
        }
    else:
        model = "wan2.7-t2v"
        inp = {"prompt": prompt}

    body: dict = {
        "model": model,
        "input": inp,
        "parameters": {
            "resolution": "720P",
            "ratio": ratio,
            "duration": duration_seconds,
            "prompt_extend": True,
            "watermark": False,
        },
    }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{base_url}/api/v1/services/aigc/video-generation/video-synthesis",
            headers=headers, json=body,
        )
        r.raise_for_status()
        task_id = r.json()["output"]["task_id"]

    video_url = await _poll_dashscope(task_id, api_key, base_url, result_key="video_url")
    local_path = await _save_remote(video_url, "vid", ".mp4")
    description = (
        f"Generated {duration_seconds}-second video with Wan2.7 in {aspect_ratio}, "
        + ("using a reference image as the first frame. " if first_frame_url else "")
        + f"Content: {prompt[:60]}."
    )
    return {
        "type": "video", "url": local_path, "description": description,
        "params_used": {"duration_seconds": duration_seconds, "aspect_ratio": aspect_ratio, "provider": "wan"},
    }


async def _poll_dashscope(task_id: str, api_key: str, base_url: str, result_key: str, max_wait: int = 600) -> str:
    url = f"{base_url}/api/v1/tasks/{task_id}"
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(max_wait // 5):
            await asyncio.sleep(5)
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            output = r.json().get("output", {})
            status = output.get("task_status", "")
            if status == "SUCCEEDED":
                return output[result_key]
            if status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"DashScope task failed: {r.json()}")
    raise TimeoutError("DashScope task timed out")


async def _video_kling(cfg: dict, prompt: str, duration_seconds: int, aspect_ratio: str, first_frame_url: Optional[str]) -> dict:
    import fal_client
    os.environ["FAL_KEY"] = _require_key(cfg)

    # Kling accepts only 5/10 seconds and 16:9/9:16, silently rounding/coercing requests.
    duration_str = "10" if duration_seconds >= 8 else "5"
    actual_aspect_ratio = "16:9" if aspect_ratio == "16:9" else "9:16"
    kwargs: dict = {
        "prompt": prompt,
        "duration": duration_str,
        "aspect_ratio": actual_aspect_ratio,
    }
    first_frame = await _first_frame_data_uri(first_frame_url)
    if first_frame:
        kwargs["image_url"] = first_frame

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: fal_client.run(cfg.get("model", "fal-ai/kling-video/v1.6/standard/text-to-video"), arguments=kwargs),
    )
    remote_url = result["video"]["url"]
    local_path = await _save_remote(remote_url, "vid", ".mp4")
    description = (
        f"Generated {duration_str}-second video with Kling 1.6 in {actual_aspect_ratio}, "
        + ("using a reference image as the first frame. " if first_frame_url else "")
        + f"Content: {prompt[:60]}."
    )
    return {
        "type": "video", "url": local_path, "description": description,
        "params_used": {"duration_seconds": int(duration_str), "aspect_ratio": actual_aspect_ratio, "provider": "kling"},
    }


# ─── Music generation ──────────────────────────────────────────────────────────

async def generate_music(prompt: str, duration_seconds: int = 30, instrumental: bool = True) -> dict:
    cfg = _provider_cfg("generate", "music")
    if cfg["provider"] == "elevenlabs":
        return await _music_elevenlabs(cfg, prompt, duration_seconds, instrumental)
    if cfg["provider"] == "replicate":
        return await _music_replicate(cfg, prompt, duration_seconds)
    if cfg["provider"] == "huggingface":
        return await _music_huggingface(cfg, prompt, duration_seconds)
    raise ValueError(f"Unknown music-generation provider: {cfg['provider']}. Options: elevenlabs, replicate, huggingface")


async def _music_elevenlabs(cfg: dict, prompt: str, duration_seconds: int, instrumental: bool) -> dict:
    """Eleven Music v2 through the ElevenLabs Music API.
    Requires a paid Music-enabled subscription and uses ELEVENLABS_API_KEY. Supports
    up to 10 minutes, vocals, multiple languages, and commercial licensing.
    """
    api_key = _require_key(cfg)
    model = cfg.get("model", "music_v2")
    duration_ms = min(max(duration_seconds * 1000, 3000), 600000)
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "prompt": prompt,
        "music_length_ms": duration_ms,
        "model_id": model,
        "force_instrumental": instrumental,
    }

    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post("https://api.elevenlabs.io/v1/music", headers=headers, json=body)
        if r.status_code in (401, 403):
            raise RuntimeError(
                "ElevenLabs Music API denied access (401/403). ELEVENLABS_API_KEY may be valid, "
                "but Music API access currently requires a paid subscription. Confirm that your "
                "plan includes Music, or switch the music provider in config.yaml to Hugging Face or Replicate."
            )
        r.raise_for_status()

    duration = duration_ms // 1000
    out_path = os.path.join(_out_dir(), f"mus_{_uid()}.mp3")
    with open(out_path, "wb") as f:
        f.write(r.content)

    description = f"Generated {duration}-second track with Eleven Music v2 from ElevenLabs. Style: {prompt[:60]}."
    return {
        "type": "audio", "subtype": "music", "url": out_path, "description": description,
        "params_used": {"duration_seconds": duration, "provider": "elevenlabs"},
    }


async def _music_replicate(cfg: dict, prompt: str, duration_seconds: int) -> dict:
    """MusicGen Large through Replicate: paid, high quality, no cold start, up to 60 seconds."""
    api_key = _require_key(cfg)
    model = cfg.get("model", "meta/musicgen")
    duration = min(duration_seconds, 60)

    import replicate as _replicate

    def _run_sync():
        client = _replicate.Client(api_token=api_key)
        return client.run(
            model,
            input={
                "prompt": prompt,
                "duration": duration,
                "model_version": "large",
                "output_format": "mp3",
                "normalization_strategy": "loudness",
            },
        )

    output = await asyncio.to_thread(_run_sync)
    audio_url = output.url if hasattr(output, "url") else str(output)
    local_path = await _save_remote(audio_url, "mus", ".mp3")
    description = f"Generated {duration}-second track with MusicGen Large through Replicate. Style: {prompt[:60]}."
    return {
        "type": "audio", "subtype": "music", "url": local_path, "description": description,
        "params_used": {"duration_seconds": duration, "provider": "replicate"},
    }


async def _music_huggingface(cfg: dict, prompt: str, duration_seconds: int) -> dict:
    """MusicGen through the Hugging Face Inference API: free allowance, up to 30 seconds."""
    api_key = _require_key(cfg)
    model = cfg.get("model", "facebook/musicgen-medium")
    headers = {"Authorization": f"Bearer {api_key}"}
    duration = min(duration_seconds, 30)

    async with httpx.AsyncClient(timeout=120) as client:
        for attempt in range(6):
            r = await client.post(
                f"https://api-inference.huggingface.co/models/{model}",
                headers=headers,
                json={"inputs": prompt, "parameters": {"duration": duration}},
            )
            if r.status_code == 503:
                # Model cold start — wait and retry (up to ~2.5 minutes total)
                await asyncio.sleep(30)
                continue
            r.raise_for_status()
            audio_content = r.content
            break
        else:
            raise RuntimeError(
                "The Hugging Face model timed out during cold start. Retry later or switch the music provider in config.yaml to Replicate."
            )

    out_path = os.path.join(_out_dir(), f"mus_{_uid()}.wav")
    with open(out_path, "wb") as f:
        f.write(audio_content)

    note = " Note: free Hugging Face inference is limited to 30 seconds." if duration_seconds > 30 else ""
    description = f"Generated {duration}-second track with MusicGen on Hugging Face.{note} Style: {prompt[:60]}."
    return {
        "type": "audio", "subtype": "music", "url": out_path, "description": description,
        "params_used": {"duration_seconds": duration, "provider": "huggingface"},
    }


# ─── Sound-effect generation ───────────────────────────────────────────────────

async def generate_sfx(prompt: str, duration_seconds: float = 15.0) -> dict:
    cfg = _provider_cfg("generate", "sfx")
    # Only elevenlabs supported; free tier available
    api_key = _require_key(cfg)
    # ElevenLabs Sound Effects accepts 0.5–30 seconds; out-of-range values return 422.
    duration_seconds = min(max(duration_seconds, 0.5), 30.0)
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    body = {"text": prompt, "duration_seconds": duration_seconds, "prompt_influence": 0.3}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("https://api.elevenlabs.io/v1/sound-generation", headers=headers, json=body)
        r.raise_for_status()

    out_path = os.path.join(_out_dir(), f"sfx_{_uid()}.mp3")
    with open(out_path, "wb") as f:
        f.write(r.content)

    description = f"Generated {duration_seconds}-second sound effect. Description: {prompt[:60]}."
    return {
        "type": "audio", "subtype": "sfx", "url": out_path, "description": description,
        "params_used": {"duration_seconds": duration_seconds, "provider": "elevenlabs"},
    }


# ─── Speech synthesis ──────────────────────────────────────────────────────────

async def generate_speech(text: str, voice: str = "neutral", language: str = "zh-CN", speed: float = 1.0) -> dict:
    cfg = _provider_cfg("generate", "speech")
    if cfg["provider"] == "edge_tts":
        return await _speech_edge_tts(cfg, text, voice, language, speed)
    if cfg["provider"] == "openai":
        return await _speech_openai(cfg, text, voice, speed)
    if cfg["provider"] == "elevenlabs":
        return await _speech_elevenlabs(cfg, text, voice, speed)
    raise ValueError(f"Unknown speech-synthesis provider: {cfg['provider']}. Options: edge_tts, openai, elevenlabs")


# Map semantic categories (neutral/male/female/warm/authoritative/cheerful) to
# Edge voice names by language. Uncovered languages fall back to the zh-CN map.
_EDGE_TTS_VOICE_MAP = {
    "zh-CN": {
        "neutral": "zh-CN-XiaoxiaoNeural",
        "male": "zh-CN-YunxiNeural",
        "female": "zh-CN-XiaoxiaoNeural",
        "warm": "zh-CN-XiaoxiaoNeural",
        "authoritative": "zh-CN-YunyangNeural",
        "cheerful": "zh-CN-XiaoyiNeural",
    },
    "en-US": {
        "neutral": "en-US-AriaNeural",
        "male": "en-US-GuyNeural",
        "female": "en-US-JennyNeural",
        "warm": "en-US-EmmaNeural",
        "authoritative": "en-US-ChristopherNeural",
        "cheerful": "en-US-AnaNeural",
    },
}


async def _speech_edge_tts(cfg: dict, text: str, voice: str, language: str, speed: float) -> dict:
    """Microsoft Edge TTS: completely free, with no API key."""
    import edge_tts

    locale_map = _EDGE_TTS_VOICE_MAP.get(language, _EDGE_TTS_VOICE_MAP["zh-CN"])
    if voice in locale_map:
        tts_voice = locale_map[voice]
    elif voice:
        tts_voice = voice  # Non-semantic value: use directly as an Edge voice name.
    else:
        tts_voice = cfg.get("voice", locale_map["neutral"])

    # edge-tts speed: "+10%" means 10% faster
    rate_str = f"{int((speed - 1.0) * 100):+d}%"
    out_path = os.path.join(_out_dir(), f"tts_{_uid()}.mp3")
    communicate = edge_tts.Communicate(text, tts_voice, rate=rate_str)
    await communicate.save(out_path)

    description = f"Synthesized speech with Edge TTS / {tts_voice}. Content: \"{text[:40]}...\""
    return {
        "type": "audio", "subtype": "speech", "url": out_path, "description": description,
        "params_used": {"voice": tts_voice, "speed": speed, "provider": "edge_tts"},
    }


_OPENAI_VOICE_MAP = {
    "neutral": "alloy", "male": "echo", "female": "shimmer",
    "warm": "nova", "authoritative": "onyx", "cheerful": "fable",
}


async def _speech_openai(cfg: dict, text: str, voice: str, speed: float) -> dict:
    from openai import AsyncOpenAI
    oai_voice = _OPENAI_VOICE_MAP.get(voice, "alloy")
    client = AsyncOpenAI(api_key=_require_key(cfg))

    response = await client.audio.speech.create(
        model=cfg.get("model", "tts-1"), voice=oai_voice, input=text, speed=speed,
    )
    out_path = os.path.join(_out_dir(), f"tts_{_uid()}.mp3")
    response.stream_to_file(out_path)

    description = f"Synthesized speech with OpenAI TTS / {oai_voice}. Content: \"{text[:40]}...\""
    return {
        "type": "audio", "subtype": "speech", "url": out_path, "description": description,
        "params_used": {"voice": oai_voice, "speed": speed, "provider": "openai"},
    }


_ELEVENLABS_VOICE_MAP = {
    "neutral": "21m00Tcm4TlvDq8ikWAM",       # Rachel
    "male": "pNInz6obpgDQGcFmaJgB",          # Adam
    "female": "EXAVITQu4vr4xnSDxMaL",        # Bella
    "warm": "AZnzlk1XvdvUeBnXmlld",          # Domi
    "authoritative": "VR6AewLTigWG4xSOukaG", # Arnold
    "cheerful": "MF3mGyEYCl7XYWbV9V6O",      # Elli
}


async def _speech_elevenlabs(cfg: dict, text: str, voice: str, speed: float) -> dict:
    # Map semantic categories to preset voices. Use any other value directly as an
    # ElevenLabs voice_id for a custom or cloned voice.
    voice_id = _ELEVENLABS_VOICE_MAP.get(voice, voice) if voice else _ELEVENLABS_VOICE_MAP["neutral"]
    headers = {"xi-api-key": _require_key(cfg), "Content-Type": "application/json"}
    body = {"text": text, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}", headers=headers, json=body,
        )
        r.raise_for_status()

    out_path = os.path.join(_out_dir(), f"tts_{_uid()}.mp3")
    with open(out_path, "wb") as f:
        f.write(r.content)

    description = f"Synthesized speech with ElevenLabs. Content: \"{text[:40]}...\""
    return {
        "type": "audio", "subtype": "speech", "url": out_path, "description": description,
        "params_used": {"voice": voice_id, "speed": speed, "provider": "elevenlabs"},
    }


# ─── 3D generation ─────────────────────────────────────────────────────────────

async def generate_3d(
    prompt: str,
    reference_image_url: Optional[str] = None,
) -> dict:
    """Always output GLB; conversion to OBJ, FBX, or other formats is not supported."""
    cfg = _provider_cfg("generate", "3d")
    if cfg["provider"] == "tripo":
        return await _3d_tripo(cfg, prompt, reference_image_url)
    if cfg["provider"] == "meshy":
        return await _3d_meshy(cfg, prompt, reference_image_url)
    raise ValueError(f"Unknown 3D-generation provider: {cfg['provider']}. Options: tripo, meshy")


async def _3d_tripo(cfg: dict, prompt: str, reference_image_url: Optional[str]) -> dict:
    api_key = _require_key(cfg)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if reference_image_url:
        task_type = "image_to_model"
        if reference_image_url.startswith(("http://", "https://")):
            file_spec = {"type": "url", "url": reference_image_url}
        else:
            b64, _ = await _to_base64(reference_image_url)
            file_spec = {"type": "base64", "data": b64}
        body: dict = {
            "type": task_type,
            "file": file_spec,
            "model_version": cfg.get("model", "v2.0-20240919"),
            "texture": True, "pbr": True,
        }
    else:
        body = {
            "type": "text_to_model",
            "prompt": prompt,
            "model_version": cfg.get("model", "v2.0-20240919"),
            "texture": True, "pbr": True,
        }

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post("https://api.tripo3d.ai/v2/openapi/task", headers=headers, json=body)
        r.raise_for_status()
        task_id = r.json()["data"]["task_id"]

    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(60):
            await asyncio.sleep(5)
            r = await client.get(f"https://api.tripo3d.ai/v2/openapi/task/{task_id}", headers=headers)
            r.raise_for_status()
            data = r.json()["data"]
            if data["status"] == "success":
                model_url = data["output"].get("model") or data["output"].get("pbr_model")
                break
            if data["status"] == "failed":
                raise RuntimeError("Tripo 3D generation failed")
        else:
            raise TimeoutError("Tripo 3D generation timed out")

    local_path = await _save_remote(model_url, "3d", ".glb")
    description = (
        "Generated a GLB 3D model with Tripo. "
        + ("Based on a reference image. " if reference_image_url else "")
        + f"Description: {prompt[:60]}."
    )
    return {
        "type": "3d", "url": local_path, "description": description,
        "params_used": {"provider": "tripo"},
    }


async def _3d_meshy(cfg: dict, prompt: str, reference_image_url: Optional[str]) -> dict:
    api_key = _require_key(cfg)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    if reference_image_url:
        if reference_image_url.startswith(("http://", "https://")):
            img_url = reference_image_url
        else:
            img_url = await _upload_to_public(reference_image_url)
        body = {"image_url": img_url, "enable_pbr": True}
        endpoint = "https://api.meshy.ai/v1/image-to-3d"
        poll_base = "https://api.meshy.ai/v1/image-to-3d"
    else:
        body = {
            "mode": "preview",
            "prompt": prompt,
            "art_style": "realistic",
            "negative_prompt": "low quality, low resolution, ugly",
        }
        endpoint = "https://api.meshy.ai/v2/text-to-3d"
        poll_base = "https://api.meshy.ai/v2/text-to-3d"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(endpoint, headers=headers, json=body)
        r.raise_for_status()
        task_id = r.json()["result"]

    async with httpx.AsyncClient(timeout=30) as client:
        for _ in range(60):
            await asyncio.sleep(5)
            r = await client.get(f"{poll_base}/{task_id}", headers=headers)
            r.raise_for_status()
            data = r.json()
            if data["status"] == "SUCCEEDED":
                model_url = data["model_urls"].get("glb") or data["model_urls"].get("obj")
                break
            if data["status"] in ("FAILED", "EXPIRED"):
                raise RuntimeError("Meshy 3D generation failed")
        else:
            raise TimeoutError("Meshy 3D generation timed out")

    local_path = await _save_remote(model_url, "3d", ".glb")
    description = (
        "Generated a GLB 3D model with Meshy. "
        + ("Based on a reference image. " if reference_image_url else "")
        + f"Description: {prompt[:60]}."
    )
    return {
        "type": "3d", "url": local_path, "description": description,
        "params_used": {"provider": "meshy"},
    }


# ─── Document generation ───────────────────────────────────────────────────────
# The calling host agent (Claude, Codex, etc.) plans content and passes `structure`.
# These functions only render the planned structure and do not call an LLM or need OPENAI_API_KEY.

async def generate_ppt(structure: dict, style: str = "professional") -> dict:
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor

    if not structure.get("slides"):
        raise ValueError("structure.slides cannot be empty. Plan every slide title and its points before calling generate_ppt")

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)

    colors = {
        "professional": (RGBColor(0x1F, 0x39, 0x7A), RGBColor(0xFF, 0xFF, 0xFF)),
        "academic":     (RGBColor(0x1A, 0x5C, 0x3A), RGBColor(0xFF, 0xFF, 0xFF)),
        "creative":     (RGBColor(0x6C, 0x3B, 0xC1), RGBColor(0xFF, 0xFF, 0xFF)),
    }
    bg_color, text_color = colors.get(style, colors["professional"])

    for slide_data in structure["slides"]:
        layout = prs.slide_layouts[1]
        slide = prs.slides.add_slide(layout)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = bg_color

        title_shape = slide.shapes.title
        title_shape.text = slide_data["title"]
        run = title_shape.text_frame.paragraphs[0].runs[0]
        run.font.color.rgb = text_color
        run.font.size = Pt(32)

        if len(slide.placeholders) > 1:
            tf = slide.placeholders[1].text_frame
            tf.clear()
            for i, point in enumerate(slide_data.get("points", [])):
                para = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
                para.text = f"• {point}"
                para.runs[0].font.color.rgb = text_color
                para.runs[0].font.size = Pt(18)

    out_path = os.path.join(_out_dir(), f"ppt_{_uid()}.pptx")
    prs.save(out_path)
    n = len(structure["slides"])
    title = structure.get("title", "Untitled presentation")
    description = f"Generated presentation with {n} slides. Topic: {title}. Style: {style}."
    return {
        "type": "document", "subtype": "ppt", "url": out_path, "description": description,
        "params_used": {"style": style, "slides": n},
    }


async def generate_word(structure: dict, style: str = "professional") -> dict:
    from docx import Document

    if not structure.get("sections"):
        raise ValueError("structure.sections cannot be empty. Plan all section headings and paragraphs before calling generate_word")

    doc = Document()
    title = structure.get("title", "Untitled document")
    doc.add_heading(title, level=0)
    for section in structure["sections"]:
        doc.add_heading(section["heading"], level=1)
        for para in section.get("paragraphs", []):
            doc.add_paragraph(para)

    out_path = os.path.join(_out_dir(), f"word_{_uid()}.docx")
    doc.save(out_path)
    n = len(structure["sections"])
    description = f"Generated Word document with {n} sections. Topic: {title}."
    return {
        "type": "document", "subtype": "word", "url": out_path, "description": description,
        "params_used": {"style": style},
    }


async def generate_pdf(structure: dict, style: str = "professional") -> dict:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    if not structure.get("sections"):
        raise ValueError("structure.sections cannot be empty. Plan all section headings and paragraphs before calling generate_pdf")

    out_path = os.path.join(_out_dir(), f"pdf_{_uid()}.pdf")
    doc = SimpleDocTemplate(out_path, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    styles = getSampleStyleSheet()
    title = structure.get("title", "Untitled document")
    story = [Paragraph(title, styles["Title"]), Spacer(1, 0.5 * cm)]
    for section in structure["sections"]:
        story.append(Paragraph(section["heading"], styles["Heading1"]))
        for para in section.get("paragraphs", []):
            story.append(Paragraph(para, styles["BodyText"]))
            story.append(Spacer(1, 0.3 * cm))
    doc.build(story)

    n = len(structure["sections"])
    description = f"Generated PDF with {n} sections. Topic: {title}."
    return {
        "type": "document", "subtype": "pdf", "url": out_path, "description": description,
        "params_used": {"style": style},
    }


async def generate_excel(structure: dict, style: str = "professional") -> dict:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    if not structure.get("sheets"):
        raise ValueError("structure.sheets cannot be empty. Plan each sheet's headers and rows before calling generate_excel")

    header_colors = {
        "professional": "1F397A",
        "academic":     "1A5C3A",
        "creative":     "6C3BC1",
    }
    header_fill = PatternFill(
        start_color=header_colors.get(style, header_colors["professional"]),
        end_color=header_colors.get(style, header_colors["professional"]),
        fill_type="solid",
    )
    header_font = Font(color="FFFFFF", bold=True)

    wb = Workbook()
    wb.remove(wb.active)  # Remove the default empty sheet and create sheets from structure.

    for sheet_data in structure["sheets"]:
        name = (sheet_data.get("name") or "Sheet")[:31]  # Excel sheet names are limited to 31 characters.
        ws = wb.create_sheet(title=name)

        headers = sheet_data.get("headers", [])
        if headers:
            ws.append(headers)
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal="center")

        for row in sheet_data.get("rows", []):
            ws.append(row)

        for col_cells in ws.columns:
            length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=8)
            ws.column_dimensions[col_cells[0].column_letter].width = min(length + 2, 40)

    out_path = os.path.join(_out_dir(), f"excel_{_uid()}.xlsx")
    wb.save(out_path)

    n_sheets = len(structure["sheets"])
    total_rows = sum(len(s.get("rows", [])) for s in structure["sheets"])
    title = structure.get("title", "Untitled workbook")
    description = f"Generated Excel workbook with {n_sheets} sheets and {total_rows} data rows. Topic: {title}."
    return {
        "type": "document", "subtype": "excel", "url": out_path, "description": description,
        "params_used": {"style": style, "sheets": n_sheets},
    }
