from __future__ import annotations

import sys
from pathlib import Path

from streamlit.web import bootstrap


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def main() -> None:
    base_dir = get_base_dir()
    app_path = base_dir / "app.py"

    if not app_path.exists():
        raise FileNotFoundError(f"Bundled app.py not found at: {app_path}")

    flag_options = {
        "server.headless": True,
        "server.port": 8501,
        "server.address": "127.0.0.1",
        "browser.gatherUsageStats": False,
    }

    bootstrap.run(str(app_path), False, [], flag_options)


if __name__ == "__main__":
    main()