from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "InboxArcheology"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def app_base_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def app_data_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


BASE_DIR = app_base_dir()
APP_DATA_DIR = app_data_dir()

INPUT_DIR = APP_DATA_DIR / "input"
WORKSPACES_DIR = APP_DATA_DIR / "workspaces"
LOGS_DIR = APP_DATA_DIR / "logs"

for p in (INPUT_DIR, WORKSPACES_DIR, LOGS_DIR):
    p.mkdir(parents=True, exist_ok=True)