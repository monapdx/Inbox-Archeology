#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent


def _resolve_python_interpreter() -> str:
    """
    Prefer the project's local virtualenv interpreter when present.

    This avoids accidental use of a globally-installed Python that may have
    incompatible/broken binary wheels (for example matplotlib DLL issues).
    """
    venv_dir = HERE / ".venv"

    if sys.platform.startswith("win"):
        candidate = venv_dir / "Scripts" / "python.exe"
    else:
        candidate = venv_dir / "bin" / "python"

    if candidate.exists():
        return str(candidate)

    return sys.executable


PY = _resolve_python_interpreter()


def slugify(name: str) -> str:
    s = name.strip()
    s = s.replace(" ", "_")
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in s).strip("._-") or "run"


def assert_mbox_ok(mbox: Path) -> None:
    if not mbox.exists():
        raise FileNotFoundError(f"MBOX not found: {mbox}")

    size = mbox.stat().st_size
    if size == 0:
        raise ValueError(
            f"Your MBOX file is empty (0 bytes): {mbox}\n"
            "Copy your real Gmail Takeout .mbox file here."
        )

    if size < 1024 * 1024:
        print(f"Warning: MBOX is very small: {mbox} ({size} bytes)")


def pick_mbox(input_dir: Path | None = None) -> Path:
    base = input_dir or HERE
    preferred_names = ["All mail.mbox", "All Mail.mbox"]

    for name in preferred_names:
        preferred = base / name
        if preferred.exists():
            return preferred

    candidates = list(base.glob("*.mbox"))
    if not candidates:
        raise FileNotFoundError(
            f"No .mbox file found in: {base}\n"
            "Put your Gmail Takeout .mbox file there and rerun."
        )

    candidates.sort(key=lambda p: p.stat().st_size, reverse=True)
    return candidates[0]


def _step_script(step_name: str) -> Path:
    direct = HERE / f"{step_name}.py"
    nested = HERE / "steps" / f"{step_name}.py"

    if direct.exists():
        return direct
    if nested.exists():
        return nested

    raise FileNotFoundError(
        f"Could not find script for step '{step_name}' in {HERE} or {HERE / 'steps'}"
    )


def _run_subprocess(step: str, cmd: list[str], cwd: Path) -> None:
    print(f"\n→ {step}")
    print("  " + " ".join(cmd))

    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.stdout:
        sys.stdout.write(result.stdout)
        if not result.stdout.endswith("\n"):
            sys.stdout.write("\n")
    if result.stderr:
        sys.stderr.write(result.stderr)
        if not result.stderr.endswith("\n"):
            sys.stderr.write("\n")

    if result.returncode != 0:
        detail_parts: list[str] = []
        if result.stderr and result.stderr.strip():
            detail_parts.append(result.stderr.strip())
        if result.stdout and result.stdout.strip():
            tail = result.stdout.strip()
            if len(tail) > 4000:
                tail = "... (truncated)\n" + tail[-4000:]
            detail_parts.append(f"stdout:\n{tail}")
        detail = (
            "\n\n".join(detail_parts)
            if detail_parts
            else "(no subprocess output captured)"
        )
        raise RuntimeError(
            f"Pipeline stopped at step: {step} (exit code {result.returncode})\n{detail}"
        )


def run_pipeline(
    mbox_path: str | Path,
    work_dir: str | Path,
    progress_cb: Callable[[float, str | None], None] | None = None,
) -> dict[str, str]:
    mbox = Path(mbox_path).resolve()
    work_dir = Path(work_dir).resolve()
    out_dir = work_dir / "output"

    work_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    assert_mbox_ok(mbox)

    files = {
        "inbox_metadata": out_dir / "inbox_metadata.csv",
        "relationships_raw": out_dir / "relationships_raw.csv",
        "relationships_filtered": out_dir / "relationships_filtered.csv",
        "relationships_clean": out_dir / "relationships_clean.csv",
        "core_timeline": out_dir / "core_timeline.csv",
        "core_timeline_png": out_dir / "core_timeline.png",
        "insights": out_dir / "insights.json",
    }

    steps: list[tuple[str, list[str]]] = [
        (
            "extract_headers",
            [
                PY,
                str(_step_script("extract_headers")),
                "--mbox",
                str(mbox),
                "--out",
                str(files["inbox_metadata"]),
                "--progress-json",
                str(out_dir / "extract_headers_progress.json"),
            ],
        ),
        (
            "extract_relationships",
            [
                PY,
                str(_step_script("extract_relationships")),
                "--in",
                str(files["inbox_metadata"]),
                "--out",
                str(files["relationships_raw"]),
            ],
        ),
        (
            "filter_relationships",
            [
                PY,
                str(_step_script("filter_relationships")),
                "--in",
                str(files["relationships_raw"]),
                "--out",
                str(files["relationships_filtered"]),
            ],
        ),
        (
            "clean_relationships",
            [
                PY,
                str(_step_script("clean_relationships")),
                "--in",
                str(files["relationships_filtered"]),
                "--out",
                str(files["relationships_clean"]),
            ],
        ),
        (
            "analyze_relationships_filtered",
            [
                PY,
                str(_step_script("analyze_relationships")),
                "--in",
                str(files["relationships_filtered"]),
            ],
        ),
        (
            "reanalyze_clean_relationships",
            [
                PY,
                str(_step_script("reanalyze_clean_relationships")),
                "--in",
                str(files["relationships_clean"]),
            ],
        ),
        (
            "build_core_timeline",
            [
                PY,
                str(_step_script("build_core_timeline")),
                "--in",
                str(files["relationships_clean"]),
                "--out",
                str(files["core_timeline"]),
            ],
        ),
        (
            "generate_insights",
            [
                PY,
                str(_step_script("generate_insights")),
                "--relationships",
                str(files["relationships_clean"]),
                "--timeline",
                str(files["core_timeline"]),
                "--out",
                str(files["insights"]),
            ],
        ),
        (
            "preview_core_timeline",
            [
                PY,
                str(_step_script("preview_core_timeline")),
                "--in",
                str(files["core_timeline"]),
            ],
        ),
        (
            "plot_core_timeline",
            [
                PY,
                str(_step_script("plot_core_timeline")),
                "--in",
                str(files["core_timeline"]),
                "--save",
                str(files["core_timeline_png"]),
            ],
        ),
    ]

    total = len(steps)

    if progress_cb:
        progress_cb(0.0, f"Using MBOX: {mbox.name}")

    for i, (step_name, cmd) in enumerate(steps, start=1):
        if progress_cb:
            progress_cb((i - 1) / total, f"Running: {step_name}")
        _run_subprocess(step_name, cmd, cwd=HERE)

    if progress_cb:
        progress_cb(1.0, "Pipeline complete")

    outputs = {
        "mbox": str(mbox),
        "workspace": str(work_dir),
        "out_dir": str(out_dir),
        **{k: str(v) for k, v in files.items()},
    }

    return outputs


def main() -> None:
    input_dir = HERE / "input"
    workspaces_dir = HERE / "workspaces"

    input_dir.mkdir(parents=True, exist_ok=True)
    workspaces_dir.mkdir(parents=True, exist_ok=True)

    mbox = pick_mbox(input_dir)
    assert_mbox_ok(mbox)

    run_name = slugify(mbox.stem)
    workspace_dir = workspaces_dir / run_name

    print(f"Using MBOX: {mbox}")
    print(f"Workspace: {workspace_dir}")

    outputs = run_pipeline(mbox_path=mbox, work_dir=workspace_dir)

    print("\n✅ Gmail pipeline complete.")

    for key, value in outputs.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()