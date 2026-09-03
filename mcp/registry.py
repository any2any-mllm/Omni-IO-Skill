"""Asset Registry — cross-session asset records persisted in a local JSON file.

registry.json is the single source of truth. Every read and write operates directly
on the file rather than a cached in-memory snapshot so multiple MCP server processes
from concurrent sessions can share it safely:
- Writes are atomic (temporary file + rename), preventing file corruption if a
  process crashes midway. This applies on every platform.
- register() serializes writes with an fcntl file lock on macOS/Linux so concurrent
  writers cannot overwrite freshly written records. Windows has no fcntl, so it
  skips locking while retaining atomic writes; concurrent processes may lose records.
"""

import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import fcntl
except ImportError:
    fcntl = None  # Windows has no fcntl; register() skips locking.


def _registry_path() -> Path:
    output_dir = os.environ.get("OMNI_OUTPUT_DIR", str(Path.home() / "Documents" / "OmniIO"))
    path = Path(output_dir).expanduser()
    path.mkdir(parents=True, exist_ok=True)
    return path / "registry.json"


class AssetRegistry:
    def __init__(self):
        self._current_turn: str = datetime.now().strftime("turn_%Y%m%d_%H%M")
        self._path = _registry_path()
        self._lock_path = self._path.with_suffix(".json.lock")

    def _load(self) -> dict[str, dict]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save(self, store: dict[str, dict]) -> None:
        """Write atomically via a temporary file and rename to preserve history on crashes."""
        tmp_path = self._path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(store, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp_path, self._path)

    def set_turn(self, turn_id: str) -> None:
        self._current_turn = turn_id

    def register(
        self,
        asset_type: str,
        url: str,
        description: str,
        params_used: dict,
        subtype: Optional[str] = None,
        depends_on: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> dict:
        prefix_map = {"image": "img", "video": "vid", "3d": "3d"}
        audio_prefix = {"music": "mus", "sfx": "sfx", "speech": "tts"}
        # Audio uses subtype prefixes (mus/sfx/tts); document types likewise use ppt/word/pdf.
        if asset_type == "audio":
            prefix = audio_prefix.get(subtype or "", "aud")
        else:
            prefix = prefix_map.get(asset_type) or subtype or "asset"

        asset_id = f"{prefix}_{uuid.uuid4().hex[:6]}"
        record: dict = {
            "asset_id": asset_id,
            "type": asset_type,
            "status": "completed",
            "url": url,
            "description": description,
            "params_used": params_used,
            "turn_id": self._current_turn,
            "completed_at": int(time.time()),
        }
        if subtype:
            record["subtype"] = subtype
        if depends_on:
            record["depends_on"] = depends_on
        if task_id:
            record["task_id"] = task_id

        # Exclusive lock plus reread inside the lock prevents concurrent register()
        # calls from overwriting one another. Windows skips the lock without fcntl.
        with open(self._lock_path, "w") as lock_file:
            if fcntl:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                store = self._load()
                store[asset_id] = record
                self._save(store)
            finally:
                if fcntl:
                    fcntl.flock(lock_file, fcntl.LOCK_UN)

        return record

    def get(self, asset_id: str) -> Optional[dict]:
        return self._load().get(asset_id)

    def list_all(self) -> list[dict]:
        return sorted(self._load().values(), key=lambda x: x["completed_at"], reverse=True)


# Global singleton shared throughout the MCP server process.
registry = AssetRegistry()
