from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).resolve().parent

if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config import INPUT_DIR, WORKSPACES_DIR  # noqa: E402
from pipeline import run_pipeline  # noqa: E402
from workspace_utils import read_metadata  # noqa: E402


STREAMLIT_UPLOAD_LIMIT_MB = 200


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


def save_uploaded_mbox(uploaded_file, input_dir: Path) -> Path:
    filename = Path(uploaded_file.name).name
    target = input_dir / filename

    fingerprint = f"{filename}:{uploaded_file.size}"

    if st.session_state.get("uploaded_mbox_fingerprint") == fingerprint and target.exists():
        return target

    target.write_bytes(uploaded_file.getbuffer())

    st.session_state.uploaded_mbox_fingerprint = fingerprint
    st.session_state.uploaded_mbox_saved_path = str(target)

    return target


def workspace_output_dir(workspace_dir: Path) -> Path:
    return workspace_dir / "output"


def workspace_has_results(workspace_dir: Path) -> bool:
    out_dir = workspace_output_dir(workspace_dir)
    return (
        out_dir.exists()
        and (out_dir / "relationships_clean.csv").exists()
        and (out_dir / "core_timeline.csv").exists()
    )


def list_workspaces(workspaces_dir: Path) -> list[Path]:
    if not workspaces_dir.exists():
        return []

    items = [p for p in workspaces_dir.iterdir() if p.is_dir()]
    items.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return items


def workspace_status_label(workspace_dir: Path) -> str:
    meta = read_metadata(workspace_dir)
    status = meta.get("status", "unknown")
    step = meta.get("last_completed_step") or meta.get("last_step") or ""

    if step:
        return f"{workspace_dir.name} — {status} — {step}"
    return f"{workspace_dir.name} — {status}"


def open_dashboard_for(out_dir: Path) -> None:
    st.session_state.dashboard_out_dir = str(out_dir.resolve())
    st.session_state.show_dashboard = True
    st.rerun()


def render_dashboard_view() -> None:
    import dashboard

    out_dir = Path(st.session_state.dashboard_out_dir)

    col1, col2 = st.columns([0.8, 0.2])

    with col1:
        st.title("Inbox Archeology Dashboard")
        st.caption(f"Output folder: {out_dir}")

    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.show_dashboard = False
            st.rerun()

    st.markdown("---")
    dashboard.render_dashboard(out_dir)


def main() -> None:
    st.set_page_config(page_title="Inbox Archeology", layout="wide")

    input_dir = INPUT_DIR
    workspaces_dir = WORKSPACES_DIR

    if "show_dashboard" not in st.session_state:
        st.session_state.show_dashboard = False

    if "dashboard_out_dir" not in st.session_state:
        st.session_state.dashboard_out_dir = ""

    with st.sidebar:
        st.header("Run Settings")

        open_dashboard = st.toggle(
            "Open dashboard automatically",
            value=True
        )

        st.divider()

        st.markdown("### Input folder")
        st.code(str(input_dir))

        st.markdown("### Workspaces")
        st.code(str(workspaces_dir))

    if st.session_state.show_dashboard and st.session_state.dashboard_out_dir:
        render_dashboard_view()
        return

    st.title("Inbox Archeology")
    st.caption("Local-first Gmail Takeout analysis. Nothing leaves your computer.")

    # -------------------------
    # EXISTING WORKSPACES
    # -------------------------

    st.header("Open Existing Workspace")

    workspaces = list_workspaces(workspaces_dir)
    completed_workspaces = [w for w in workspaces if workspace_has_results(w)]

    if completed_workspaces:
        selected_workspace = st.selectbox(
            "Previously completed runs",
            options=completed_workspaces,
            format_func=workspace_status_label,
            key="existing_workspace_select",
        )

        col_open1, col_open2 = st.columns([1, 2])

        with col_open1:
            if st.button("Open selected workspace", use_container_width=True):
                open_dashboard_for(workspace_output_dir(selected_workspace))

        with col_open2:
            st.caption(f"Saved results: {workspace_output_dir(selected_workspace)}")
    else:
        st.info("No completed workspaces found yet.")

    st.markdown("---")

    # -------------------------
    # INPUT SECTION
    # -------------------------

    st.header("1) Add Gmail Takeout")

    st.info(
        "For real Gmail exports, click **Open input folder** and drag your `.mbox` file into it.\n\n"
        "Browser upload is limited (~200MB) and only meant for testing."
    )

    st.markdown("### Add your `.mbox` file")

    col_a, col_b = st.columns([1, 2])

    with col_a:
        if st.button("Open input folder", use_container_width=True):
            os.startfile(input_dir)

    with col_b:
        st.code(str(input_dir))

    st.markdown(
        """
1. Download your Gmail Takeout export  
2. Find **All Mail.mbox**  
3. Click **Open input folder**  
4. Drag the `.mbox` file into that folder  
5. Click **Refresh list**
"""
    )

    with st.expander("Optional: Upload small test file"):
        st.warning(f"Streamlit upload limit ≈ {STREAMLIT_UPLOAD_LIMIT_MB} MB")

        uploaded = st.file_uploader(
            "Upload a small .mbox",
            type=["mbox"]
        )

        if uploaded is not None:
            try:
                saved = save_uploaded_mbox(uploaded, input_dir)
                st.success(f"Saved to {saved}")
            except Exception as e:
                st.error("Upload failed")
                st.exception(e)

    col1, col2 = st.columns([1, 4])

    with col1:
        if st.button("Refresh list", use_container_width=True):
            st.rerun()

    mbox_files = sorted(
        input_dir.glob("*.mbox"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not mbox_files:
        st.warning("No `.mbox` files found yet.")
        st.stop()

    st.subheader("Available inbox files")

    for p in mbox_files:
        try:
            size = human_size(p.stat().st_size)
        except Exception:
            size = "unknown size"

        st.write(f"- `{p.name}` — {size}")

    selected_mbox = st.selectbox(
        "Select inbox to analyze",
        options=mbox_files,
        format_func=lambda p: p.name
    )

    mbox_path = selected_mbox.resolve()

    st.success(f"Selected: {mbox_path}")

    # -------------------------
    # WORKSPACE
    # -------------------------

    st.header("2) Workspace")

    default_run = slugify(mbox_path.stem)

    run_name = st.text_input(
        "Run name",
        value=default_run
    )

    run_name = slugify(run_name)

    workspace_dir = workspaces_dir / run_name
    workspace_dir.mkdir(parents=True, exist_ok=True)

    st.caption(f"Workspace: {workspace_dir}")

    meta = read_metadata(workspace_dir)
    if meta:
        status = meta.get("status", "unknown")
        last_step = meta.get("last_completed_step") or meta.get("last_step")

        if last_step:
            st.caption(f"Workspace status: {status} — {last_step}")
        else:
            st.caption(f"Workspace status: {status}")

    if workspace_has_results(workspace_dir):
        st.info("This workspace already contains saved results.")
        if st.button("Open this workspace now", use_container_width=True):
            open_dashboard_for(workspace_output_dir(workspace_dir))

    # -------------------------
    # RUN
    # -------------------------

    st.header("3) Run Analysis")

    force_rerun = st.checkbox("Re-run completed steps", value=False)

    run_clicked = st.button(
        "Run Inbox Archeology",
        type="primary",
        use_container_width=True
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
                st.stop()

        progress_bar.progress(100)
        status.success("Pipeline complete")

        out_dir = Path(outputs["out_dir"])

        st.header("Results")
        st.markdown(f"Outputs saved to `{out_dir}`")

        st.subheader("Generated files")
        for k, v in outputs.items():
            st.write(f"{k} → {v}")

        if open_dashboard:
            open_dashboard_for(out_dir)

        if st.button("Open dashboard", use_container_width=True):
            open_dashboard_for(out_dir)

    else:
        st.info("Click **Run Inbox Archeology** to start analysis.")


if __name__ == "__main__":
    main()