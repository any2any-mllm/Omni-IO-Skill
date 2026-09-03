"""Understanding tools: convert each modality to text and return dense captions."""

import asyncio
import base64
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import httpx
from openai import AsyncOpenAI


def _require_key(env_var: str) -> str:
    val = os.environ.get(env_var, "")
    if not val:
        raise RuntimeError(
            f"API key is not configured ({env_var}). Set this variable in config/.env; "
            "see setup/api_guide.md."
        )
    return val


# ─── Video understanding ───────────────────────────────────────────────────────

async def understand_video(video_url: str) -> dict:
    """Use Gemini to generate an overall video description and segmented timeline."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=_require_key("GEMINI_API_KEY"))

    # Read local video bytes directly or download an HTTP URL.
    if video_url.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=60) as http:
            r = await http.get(video_url)
            r.raise_for_status()
            content = r.content
        suffix = Path(video_url.split("?")[0]).suffix or ".mp4"
    else:
        with open(video_url, "rb") as f:
            content = f.read()
        suffix = Path(video_url).suffix or ".mp4"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content)
        tmp_path = f.name

    try:
        # Upload the file to the Gemini File API.
        video_file = await asyncio.to_thread(
            client.files.upload, file=tmp_path,
        )
        while video_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            video_file = await asyncio.to_thread(client.files.get, name=video_file.name)

        prompt = (
            "Analyze this video in English:\n"
            "1. Overall description in at most 100 words: main content, color/style, and emotional atmosphere.\n"
            "2. Segmented timeline in roughly 15-second intervals, formatted as [start-end] description.\n"
            "Return JSON: {\"description\": \"...\", \"timeline\": [{\"time\": \"00:00-00:15\", \"description\": \"...\"}]}"
        )
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[video_file, prompt],
        )
    finally:
        os.unlink(tmp_path)

    import json, re
    text = response.text.strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    return {"description": text, "timeline": []}


# ─── Audio understanding ───────────────────────────────────────────────────────

async def understand_audio(audio_url: str, subtype: str = "music") -> dict:
    """
    Priority: Gemini API (GEMINI_API_KEY; one call handles speech/music/SFX).
    If GEMINI_API_KEY is missing or the call fails, fall back by subtype:
    speech → Whisper transcription (OPENAI_API_KEY, paid cloud API)
    music/SFX → Qwen2-Audio analysis via DashScope (QWEN_API_KEY)
    """
    if os.environ.get("GEMINI_API_KEY", ""):
        try:
            return await _analyze_gemini_audio(audio_url, subtype)
        except Exception:
            pass  # Fall back to the specialized provider below.

    if subtype == "speech":
        return await _transcribe_speech(audio_url)
    else:
        return await _analyze_music(audio_url, subtype)


async def _transcribe_speech(audio_url: str) -> dict:
    """Transcribe speech with Whisper. Supports local paths and HTTP URLs."""
    client = AsyncOpenAI(api_key=_require_key("OPENAI_API_KEY"))

    if audio_url.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=60) as http:
            r = await http.get(audio_url)
            r.raise_for_status()
        suffix = Path(audio_url.split("?")[0]).suffix or ".mp3"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(r.content)
            tmp_path = f.name
        cleanup = True
    else:
        tmp_path = audio_url
        cleanup = False

    try:
        with open(tmp_path, "rb") as audio_file:
            transcription = await client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
    finally:
        if cleanup:
            os.unlink(tmp_path)

    segments = getattr(transcription, "segments", [])
    transcript_lines = [
        f"[{int(s.start//60):02d}:{int(s.start%60):02d}] {s.text.strip()}"
        for s in segments
    ]
    description = (
        f"Speech recording approximately {int(transcription.duration)} seconds long. "
        f"Content: {transcription.text[:80]}..."
    )

    return {
        "description": description,
        "subtype": "speech",
        "transcript": "\n".join(transcript_lines),
    }


def _music_sfx_prompt(subtype: str) -> str:
    """Return the shared Qwen/Gemini prompt and JSON schema for music/SFX analysis."""
    if subtype == "music":
        return (
            "Analyze this music and return these JSON fields:\n"
            "- genre: e.g. Pop, Electronic, Classical, Jazz, Folk\n"
            "- mood: e.g. cheerful, melancholy, calm, tense, uplifting\n"
            "- bpm: estimated integer BPM, or null if indeterminate\n"
            "- instruments: up to three principal instruments\n"
            "- has_vocals: true or false\n"
            "- description: one English sentence of at most 60 words\n"
            "Return JSON only, with no other content."
        )
    return (
        "Analyze this environmental sound or sound effect and return these JSON fields:\n"
        "- dominant_sound: e.g. rain, crowd, waves, machinery\n"
        "- mood: e.g. peaceful, noisy, oppressive, lively\n"
        "- spatial: indoor/outdoor and enclosed/open\n"
        "- description: one English sentence of at most 60 words\n"
        "Return JSON only, with no other content."
    )


def _format_music_sfx(data: dict, subtype: str) -> str:
    """Format the shared Qwen/Gemini music/SFX analysis JSON as an English summary."""
    if subtype == "music":
        instruments = data.get("instruments", [])
        instr_str = "/".join(instruments[:3]) if instruments else ""
        bpm = data.get("bpm")
        return (
            f"Music. Genre: {data.get('genre', '')}; mood: {data.get('mood', '')}; "
            + (f"approximately {bpm} BPM; " if bpm else "")
            + (f"principal instruments: {instr_str}; " if instr_str else "")
            + ("with vocals." if data.get("has_vocals") else "instrumental.")
        )
    return (
        f"Soundscape. Dominant sound: {data.get('dominant_sound', '')}; "
        f"atmosphere: {data.get('mood', '')}; space: {data.get('spatial', '')}."
    )


async def _analyze_music(audio_url: str, subtype: str) -> dict:
    """Analyze music/soundscapes with Qwen2-Audio through DashScope.
    QWEN_API_KEY uses the same Alibaba Cloud DashScope platform as WAN_API_KEY.
    """
    import json as _json

    api_key = _require_key("QWEN_API_KEY")

    # Convert a local path to base64; pass an HTTP URL directly.
    if audio_url.startswith(("http://", "https://")):
        audio_input = {"url": audio_url}
    else:
        suffix = Path(audio_url).suffix.lower() or ".mp3"
        mime_map = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".flac": "audio/flac"}
        mime = mime_map.get(suffix, "audio/mpeg")
        with open(audio_url, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        audio_input = {"url": f"data:{mime};base64,{b64}"}

    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    response = await client.chat.completions.create(
        model="qwen2-audio-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "audio_url", "audio_url": audio_input},
                    {"type": "text", "text": _music_sfx_prompt(subtype)},
                ],
            }
        ],
    )

    raw = response.choices[0].message.content.strip()
    # Extract JSON from the returned content.
    import re as _re
    match = _re.search(r"\{.*\}", raw, _re.DOTALL)
    if not match:
        return {"description": raw, "subtype": subtype}
    data = _json.loads(match.group())

    return {"description": _format_music_sfx(data, subtype), "subtype": subtype, "analysis": data}


async def _analyze_gemini_audio(audio_url: str, subtype: str) -> dict:
    """Understand speech, music, or SFX in one Gemini API call."""
    from google import genai
    import json as _json
    import re as _re

    client = genai.Client(api_key=_require_key("GEMINI_API_KEY"))

    if audio_url.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=60) as http:
            r = await http.get(audio_url)
            r.raise_for_status()
            content = r.content
        suffix = Path(audio_url.split("?")[0]).suffix or ".mp3"
    else:
        with open(audio_url, "rb") as f:
            content = f.read()
        suffix = Path(audio_url).suffix or ".mp3"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content)
        tmp_path = f.name

    try:
        audio_file = await asyncio.to_thread(client.files.upload, file=tmp_path)
        while audio_file.state.name == "PROCESSING":
            await asyncio.sleep(2)
            audio_file = await asyncio.to_thread(client.files.get, name=audio_file.name)

        if subtype == "speech":
            prompt = (
                "Transcribe this speech in its original language. Return JSON:\n"
                "{\"duration\": total duration in seconds, \"full_text\": \"complete transcript\", "
                "\"segments\": [{\"start\": start time in seconds, \"text\": \"segment text\"}]}\n"
                "Split segments at semantic boundaries or pauses, about 5–15 seconds each. "
                "Return JSON only, with no other content."
            )
        else:
            prompt = _music_sfx_prompt(subtype)

        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=[audio_file, prompt],
        )
    finally:
        os.unlink(tmp_path)

    text = response.text.strip()
    match = _re.search(r"\{.*\}", text, _re.DOTALL)
    if not match:
        return {"description": text, "subtype": subtype}
    data = _json.loads(match.group())

    if subtype == "speech":
        transcript_lines = [
            f"[{int(seg['start']//60):02d}:{int(seg['start']%60):02d}] {seg['text'].strip()}"
            for seg in data.get("segments", [])
        ]
        duration = data.get("duration")
        full_text = data.get("full_text", "")
        description = (
            (f"Speech recording approximately {int(duration)} seconds long. " if duration else "Speech recording. ")
            + f"Content: {full_text[:80]}..."
        )
        return {"description": description, "subtype": "speech", "transcript": "\n".join(transcript_lines)}

    return {"description": _format_music_sfx(data, subtype), "subtype": subtype, "analysis": data}


# ─── Document understanding ────────────────────────────────────────────────────

async def understand_document(document_url: str) -> dict:
    """Extract a document with Mistral OCR 3 and return description + Markdown content."""
    api_key = _require_key("MISTRAL_API_KEY")

    async with httpx.AsyncClient(timeout=120) as client:
        # Use the Mistral OCR API.
        r = await client.post(
            "https://api.mistral.ai/v1/ocr",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "mistral-ocr-latest",
                "document": {"type": "document_url", "document_url": document_url},
                "include_image_base64": False,
            },
        )
        r.raise_for_status()
        data = r.json()

    pages = data.get("pages", [])
    content = "\n\n".join(p.get("markdown", "") for p in pages)

    # Summarize with GPT-4o-mini when OPENAI_API_KEY is present; otherwise use the first sentence.
    oai_key = os.environ.get("OPENAI_API_KEY", "")
    if oai_key:
        try:
            oai = AsyncOpenAI(api_key=oai_key)
            summary_resp = await oai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"Summarize this document in one English sentence of at most 100 words:\n\n{content[:2000]}"}],
                max_tokens=150,
            )
            description = summary_resp.choices[0].message.content.strip()
        except Exception:
            description = content[:100].strip() + "…"
    else:
        description = content[:100].strip() + "…"

    return {
        "description": description,
        "content": content[:4000],
    }


# ─── 3D understanding ──────────────────────────────────────────────────────────

_BLENDER_PATH_CANDIDATES = ["/Applications/Blender.app/Contents/MacOS/Blender"]

# Blender 5.0 deprecated import_scene.obj; hasattr remains True but calls raise AttributeError.
# Use wm.obj_import instead.
_BLENDER_IMPORTERS = {
    ".glb": "bpy.ops.import_scene.gltf(filepath={path!r})",
    ".gltf": "bpy.ops.import_scene.gltf(filepath={path!r})",
    ".obj": "bpy.ops.wm.obj_import(filepath={path!r})",
    ".fbx": "bpy.ops.import_scene.fbx(filepath={path!r})",
}

_BLENDER_SCRIPT_TEMPLATE = """
import bpy, math, mathutils

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

{import_line}

for obj in bpy.data.objects:
    obj.hide_render = False

min_co = mathutils.Vector((float('inf'),)*3)
max_co = mathutils.Vector((float('-inf'),)*3)
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        for v in obj.bound_box:
            wv = obj.matrix_world @ mathutils.Vector(v)
            min_co = mathutils.Vector(map(min, zip(min_co, wv)))
            max_co = mathutils.Vector(map(max, zip(max_co, wv)))
center = (min_co + max_co) / 2
size = max((max_co - min_co).length, 0.01)

def add_sun(name, energy, loc):
    bpy.ops.object.light_add(type='SUN', location=loc)
    bpy.context.active_object.name = name
    bpy.context.active_object.data.energy = energy
add_sun("Key",  3.0, (size*2, -size*2,  size*2))
add_sun("Fill", 1.0, (-size*2, -size,   size))
add_sun("Back", 1.5, (0,       size*2, -size))

bpy.ops.object.camera_add()
cam = bpy.context.active_object
bpy.context.scene.camera = cam
phi, theta = math.radians(45), math.radians(45)
dist = size * 2.2
cam.location = (
    center.x + dist * math.sin(phi) * math.cos(theta),
    center.y + dist * math.sin(phi) * math.sin(theta),
    center.z + dist * math.cos(phi),
)
direction = mathutils.Vector(center) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 64
scene.render.resolution_x = scene.render.resolution_y = 800
scene.render.filepath = {out_path!r}
scene.render.image_settings.file_format = 'PNG'
bpy.data.worlds["World"].node_tree.nodes["Background"].inputs[0].default_value = (0.8, 0.8, 0.8, 1)
bpy.ops.render.render(write_still=True)
"""


def _find_blender() -> Optional[str]:
    for path in _BLENDER_PATH_CANDIDATES:
        if os.path.exists(path):
            return path
    return shutil.which("blender")


async def _render_blender(local_path: str, suffix: str) -> Optional[str]:
    """Render a textured isometric view with local headless Blender.
    Return None when Blender is missing, the format is unsupported, or rendering fails/times out,
    allowing the caller to use the trimesh fallback.
    """
    blender = _find_blender()
    importer = _BLENDER_IMPORTERS.get(suffix.lower())
    if not blender or not importer:
        return None

    out_path = str(Path(local_path).with_suffix("")) + f"_blender_{uuid.uuid4().hex[:6]}.png"
    script = _BLENDER_SCRIPT_TEMPLATE.format(
        import_line=importer.format(path=local_path),
        out_path=out_path,
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
        f.write(script)
        script_path = f.name

    try:
        proc = await asyncio.create_subprocess_exec(
            blender, "--background", "--python", script_path,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            await asyncio.wait_for(proc.communicate(), timeout=120)
        except asyncio.TimeoutError:
            proc.kill()
            return None
        if proc.returncode != 0 or not os.path.exists(out_path):
            return None
        return out_path
    finally:
        os.unlink(script_path)


async def understand_3d(file_url: str) -> dict:
    """Extract mesh metadata with trimesh and render an isometric view with local
    headless Blender/Cycles when available. Otherwise use matplotlib front/side/isometric
    views with geometry only, via the Agg backend without a GPU or display.
    Return mesh_info and local render paths for Claude to analyze visually.
    """
    import trimesh
    import numpy as np

    # Read a local path or download an HTTP URL.
    if file_url.startswith(("http://", "https://")):
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.get(file_url)
            r.raise_for_status()
            content = r.content
        suffix = Path(file_url.split("?")[0]).suffix or ".glb"
    else:
        with open(file_url, "rb") as f:
            content = f.read()
        suffix = Path(file_url).suffix or ".glb"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(content)
        tmp_path = f.name

    try:
        scene_or_mesh = await asyncio.to_thread(trimesh.load, tmp_path)

        if isinstance(scene_or_mesh, trimesh.Scene):
            geometries = list(scene_or_mesh.geometry.values())
            if not geometries:
                return {
                    "description": "Empty 3D scene with no geometry", "mesh_info": {},
                    "render_paths": [], "render_method": None,
                }
            mesh = trimesh.util.concatenate(geometries)
            n_materials = len(scene_or_mesh.geometry)
        else:
            mesh = scene_or_mesh
            n_materials = 1

        mesh_info = {
            "vertices": int(len(mesh.vertices)),
            "faces": int(len(mesh.faces)),
            "materials": n_materials,
            "file_format": suffix.lstrip("."),
            "dimensions": [round(v, 4) for v in (mesh.bounds[1] - mesh.bounds[0]).tolist()],
            "is_watertight": bool(mesh.is_watertight),
        }

        blender_render = await _render_blender(tmp_path, suffix)
        if blender_render:
            render_paths = [blender_render]
            render_method = "blender"
        else:
            render_paths = await asyncio.to_thread(
                _render_3d_views, np.array(mesh.vertices), np.array(mesh.faces), tmp_path
            )
            render_method = "trimesh_fallback"

    finally:
        os.unlink(tmp_path)

    if render_method == "blender":
        render_note = (
            "A textured and lit isometric view was rendered with local Blender in render_paths. "
            "Read it for semantic description."
        )
    else:
        render_note = (
            "Local Blender was not found or rendering failed/timed out. The trimesh fallback "
            "created solid-color front, side, and isometric views in render_paths. They show "
            "geometry only, not materials or semantic appearance; disclose this limitation."
        )

    description = (
        f"3D model in {suffix.lstrip('.')} format, "
        f"with {mesh_info['vertices']} vertices and {mesh_info['faces']} faces; "
        f"{'watertight' if mesh_info['is_watertight'] else 'not watertight'}. "
        f"{render_note}"
    )

    return {
        "description": description, "mesh_info": mesh_info,
        "render_paths": render_paths, "render_method": render_method,
    }


def _render_3d_views(vertices: "np.ndarray", faces: "np.ndarray", tmp_path: str) -> list:
    """Synchronously render three views with matplotlib Agg and return local paths."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    import numpy as np

    # Randomly sample large meshes to avoid excessive render time.
    max_faces = 3000
    if len(faces) > max_faces:
        idx = np.random.choice(len(faces), max_faces, replace=False)
        display_faces = faces[idx]
    else:
        display_faces = faces

    mins = vertices.min(axis=0)
    maxs = vertices.max(axis=0)
    center = (mins + maxs) / 2
    max_range = max((maxs - mins).max() * 0.6, 1e-6)

    views = [("front", 0, 15), ("side", 90, 15), ("iso", 45, 30)]
    base = str(Path(tmp_path).with_suffix(""))
    render_paths = []

    for name, azim, elev in views:
        fig = plt.figure(figsize=(4, 4), facecolor="white")
        ax = fig.add_subplot(111, projection="3d")

        col = Poly3DCollection(vertices[display_faces], alpha=0.8, linewidth=0)
        col.set_facecolor([0.55, 0.75, 0.92])
        ax.add_collection3d(col)

        ax.set_xlim(center[0] - max_range, center[0] + max_range)
        ax.set_ylim(center[1] - max_range, center[1] + max_range)
        ax.set_zlim(center[2] - max_range, center[2] + max_range)
        ax.view_init(elev=elev, azim=azim)
        ax.set_axis_off()

        out = f"{base}_render_{name}.png"
        plt.savefig(out, dpi=80, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        render_paths.append(out)

    return render_paths
