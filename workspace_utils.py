from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def metadata_path(workspace_dir: Path) -> Path:
    return workspace_dir / "metadata.json"


def read_metadata(workspace_dir: Path) -> dict:
    path = metadata_path(workspace_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_metadata(workspace_dir: Path, data: dict) -> None:
    path = metadata_path(workspace_dir)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def update_metadata(workspace_dir: Path, updates: dict) -> dict:
    data = read_metadata(workspace_dir)
    data.update(updates)
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_metadata(workspace_dir, data)
    return data