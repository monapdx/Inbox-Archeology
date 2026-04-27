#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from typing import Callable

HERE = Path(__file__).resolve().parent
PY = sys.executable

# Help Windows behave better with Unicode in console output
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


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
            "Choose your real Gmail Takeout .mbox file and rerun."
        )

    if size < 1024 * 1024:
        print(f"Warning: MBOX is very small: {mbox} ({size} bytes)", flush=True)


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


def _emit_line_progress(
    line: str,
    step: str,
    progress_cb: Callable[[float, str | None], None] | None,
    step_progress_base: float | None,
    step_progress_span: float | None,
) -> None:
    if not progress_cb or step_progress_base is None or step_progress_span is None:
        return

    if line.startswith("PROGRESS_PCT:"):
        payload = line.split(":", 1)[1].strip()
        pct_text, _, msg = payload.partition("|")

        try:
            pct = float(pct_text)
        except ValueError:
            pct = 0.0

        pct = max(0.0, min(1.0, pct))
        overall_pct = step_progress_base + (step_progress_span * pct)

        progress_cb(
            min(0.99, overall_pct),
            f"{step}: {msg or f'{pct:.0%}'}",
        )
        return

    if line.startswith("PROGRESS:"):
        msg = line.split(":", 1)[1].strip()
        progress_cb(
            min(0.99, step_progress_base + (step_progress_span * 0.5)),
            f"{step}: {msg}",
        )


def _run_subprocess(
    step: str,
    cmd: list[str],
    cwd: Path,
    progress_cb: Callable[[float, str | None], None] | None = None,
    step_progress_base: float | None = None,
    step_progress_span: float | None = None,
) -> None:
    print(f"\n[STEP] {step}", flush=True)
    print("  CMD: " + " ".join(cmd), flush=True)

    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    assert process.stdout is not None

    for raw_line in process.stdout:
        line = raw_line.rstrip()
        if not line:
            continue

        print(line, flush=True)
        _emit_line_progress(
            line=line,
            step=step,
            progress_cb=progress_cb,
            step_progress_base=step_progress_base,
            step_progress_span=step_progress_span,
        )

    return_code = process.wait()

    if return_code != 0:
        raise RuntimeError(
            f"Pipeline stopped at step: {step} (exit code {return_code})"
        )


def run_pipeline(
    mbox_path: str | Path,
    work_dir: str | Path,
    progress_cb: Callable[[float, str | None], None] | None = None,
    force: bool = False,
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
    }

    steps: list[dict] = [
        {
            "name": "extract_headers",
            "cmd": [
                PY,
                str(_step_script("extract_headers")),
                "--mbox",
                str(mbox),
                "--out",
                str(files["inbox_metadata"]),
            ],
            "outputs": [files["inbox_metadata"]],
        },
        {
            "name": "extract_relationships",
            "cmd": [
                PY,
                str(_step_script("extract_relationships")),
                "--in",
                str(files["inbox_metadata"]),
                "--out",
                str(files["relationships_raw"]),
            ],
            "outputs": [files["relationships_raw"]],
        },
        {
            "name": "filter_relationships",
            "cmd": [
                PY,
                str(_step_script("filter_relationships")),
                "--in",
                str(files["relationships_raw"]),
                "--out",
                str(files["relationships_filtered"]),
            ],
            "outputs": [files["relationships_filtered"]],
        },
        {
            "name": "clean_relationships",
            "cmd": [
                PY,
                str(_step_script("clean_relationships")),
                "--in",
                str(files["relationships_filtered"]),
                "--out",
                str(files["relationships_clean"]),
            ],
            "outputs": [files["relationships_clean"]],
        },
        {
            "name": "analyze_relationships_filtered",
            "cmd": [
                PY,
                str(_step_script("analyze_relationships")),
                "--in",
                str(files["relationships_filtered"]),
            ],
            "outputs": [],
        },
        {
            "name": "reanalyze_clean_relationships",
            "cmd": [
                PY,
                str(_step_script("reanalyze_clean_relationships")),
                "--in",
                str(files["relationships_clean"]),
            ],
            "outputs": [],
        },
        {
            "name": "build_core_timeline",
            "cmd": [
                PY,
                str(_step_script("build_core_timeline")),
                "--in",
                str(files["relationships_clean"]),
                "--out",
                str(files["core_timeline"]),
            ],
            "outputs": [files["core_timeline"]],
        },
        {
            "name": "preview_core_timeline",
            "cmd": [
                PY,
                str(_step_script("preview_core_timeline")),
                "--in",
                str(files["core_timeline"]),
            ],
            "outputs": [],
        },
        {
            "name": "plot_core_timeline",
            "cmd": [
                PY,
                str(_step_script("plot_core_timeline")),
                "--in",
                str(files["core_timeline"]),
                "--save",
                str(files["core_timeline_png"]),
            ],
            "outputs": [files["core_timeline_png"]],
        },
    ]

    total = len(steps)

    if progress_cb:
        progress_cb(0.0, f"Using MBOX: {mbox.name}")

    for i, step in enumerate(steps, start=1):
        step_name = step["name"]
        cmd = step["cmd"]
        outputs = step["outputs"]

        step_base = (i - 1) / total
        step_span = 1 / total

        all_outputs_exist = bool(outputs) and all(p.exists() for p in outputs)

        if all_outputs_exist and not force:
            if progress_cb:
                progress_cb(
                    min(0.99, i / total),
                    f"Skipping: {step_name} (already done)",
                )
            continue

        if progress_cb:
            progress_cb(step_base, f"Running: {step_name}")

        _run_subprocess(
            step=step_name,
            cmd=cmd,
            cwd=HERE,
            progress_cb=progress_cb,
            step_progress_base=step_base,
            step_progress_span=step_span,
        )

        if progress_cb:
            progress_cb(min(0.99, i / total), f"Finished: {step_name}")

    if progress_cb:
        progress_cb(1.0, "Pipeline complete")

    return {
        "mbox": str(mbox),
        "workspace": str(work_dir),
        "out_dir": str(out_dir),
        **{k: str(v) for k, v in files.items()},
    }


def main() -> None:
    raise SystemExit(
        "Run this through app.py or import run_pipeline(); direct auto-pick mode was removed."
    )


if __name__ == "__main__":
    main()