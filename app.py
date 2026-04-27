from __future__ import annotations

import re
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import WORKSPACES_DIR  # noqa: E402
from pipeline import run_pipeline  # noqa: E402


def slugify(name: str) -> str:
    s = name.strip()
    s = re.sub(r"\.mbox$", "", s, flags=re.IGNORECASE)
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "run"


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)

    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{num_bytes} B"


def sync_selected_mbox_from_query_params() -> None:
    raw = st.query_params.get("mbox", "")

    if isinstance(raw, list):
        raw = raw[0] if raw else ""

    if not raw:
        return

    p = Path(raw)

    if p.exists():
        resolved = str(p.resolve())
        if st.session_state.mbox_path != resolved:
            st.session_state.mbox_path = resolved
            st.session_state.view = "main"


def render_dashboard_view() -> None:
    import dashboard

    out_dir = Path(st.session_state.dashboard_out_dir)

    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        st.title("Inbox Archeology Dashboard")
        st.caption(f"Output folder: {out_dir}")

    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.view = "main"
            st.rerun()

    st.markdown("---")
    dashboard.render_dashboard(out_dir)


def render_main_view() -> None:
    st.title("Inbox Archeology")
    st.caption("Analyze your Gmail Takeout. Nothing leaves your computer.")

    if not st.session_state.mbox_path:
        st.info("Choose MBOX File from the desktop app.")

        if st.session_state.last_out_dir:
            st.markdown("---")
            if st.button("Open Dashboard", use_container_width=True):
                st.session_state.dashboard_out_dir = st.session_state.last_out_dir
                st.session_state.view = "dashboard"
                st.rerun()
        return

    mbox_path = Path(st.session_state.mbox_path)

    if not mbox_path.exists():
        st.error("The selected MBOX file no longer exists.")
        st.session_state.mbox_path = None
        return

    try:
        size = human_size(mbox_path.stat().st_size)
    except Exception:
        size = "unknown size"

    st.subheader("Selected MBOX")
    st.success(f"{mbox_path.name} — {size}")
    st.caption(str(mbox_path))

    run_name = slugify(mbox_path.stem)
    workspace_dir = WORKSPACES_DIR / run_name
    workspace_dir.mkdir(parents=True, exist_ok=True)

    st.caption(f"Workspace: {workspace_dir}")

    st.header("Run Analysis")

    force_rerun = st.checkbox("Re-run completed steps", value=False)

    run_clicked = st.button(
        "Run Inbox Archeology",
        type="primary",
        use_container_width=True,
    )

    progress_bar = st.progress(0)
    status = st.empty()

    def progress_cb(pct: float, msg: str | None = None) -> None:
        progress_bar.progress(int(max(0, min(100, pct * 100))))
        if msg:
            status.write(msg)

    if run_clicked:
        with st.spinner("Running pipeline..."):
            try:
                outputs = run_pipeline(
                    mbox_path=mbox_path,
                    work_dir=workspace_dir,
                    progress_cb=progress_cb,
                    force=force_rerun,
                )
            except Exception as e:
                st.error("Pipeline failed")
                st.exception(e)
                return

        progress_bar.progress(100)
        status.success("Pipeline complete")

        out_dir = str(Path(outputs["out_dir"]).resolve())
        st.session_state.last_out_dir = out_dir
        st.session_state.dashboard_out_dir = out_dir

        st.success("Analysis complete")

    if st.session_state.last_out_dir:
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Open Dashboard", use_container_width=True):
                st.session_state.dashboard_out_dir = st.session_state.last_out_dir
                st.session_state.view = "dashboard"
                st.rerun()

        with col2:
            if st.button("Choose Another MBOX in Desktop App", use_container_width=True):
                st.info("Use File → Choose MBOX File in the desktop app window.")

    else:
        st.info("Click Run to start analysis.")


def main() -> None:
    st.set_page_config(page_title="Inbox Archeology", layout="wide")

    if "view" not in st.session_state:
        st.session_state.view = "main"

    if "dashboard_out_dir" not in st.session_state:
        st.session_state.dashboard_out_dir = ""

    if "last_out_dir" not in st.session_state:
        st.session_state.last_out_dir = ""

    if "mbox_path" not in st.session_state:
        st.session_state.mbox_path = None

    sync_selected_mbox_from_query_params()

    if st.session_state.view == "dashboard":
        if st.session_state.dashboard_out_dir:
            render_dashboard_view()
            return
        st.session_state.view = "main"

    render_main_view()


if __name__ == "__main__":
    main()