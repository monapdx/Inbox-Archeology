# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from pathlib import Path

ROOT = Path.cwd()

streamlit_datas = collect_data_files("streamlit")
streamlit_hidden = collect_submodules("streamlit")

datas = streamlit_datas + [
    (str(ROOT / "app.py"), "."),
    (str(ROOT / "dashboard.py"), "."),
    (str(ROOT / "pipeline.py"), "."),
    (str(ROOT / "config.py"), "."),
    (str(ROOT / "workspace_utils.py"), "."),
    (str(ROOT / "run_app.py"), "."),
    (str(ROOT / "steps" / "extract_headers.py"), "steps"),
    (str(ROOT / "steps" / "extract_relationships.py"), "steps"),
    (str(ROOT / "steps" / "analyze_relationships.py"), "steps"),
    (str(ROOT / "steps" / "filter_relationships.py"), "steps"),
    (str(ROOT / "steps" / "clean_relationships.py"), "steps"),
    (str(ROOT / "steps" / "reanalyze_clean_relationships.py"), "steps"),
    (str(ROOT / "steps" / "build_core_timeline.py"), "steps"),
    (str(ROOT / "steps" / "preview_core_timeline.py"), "steps"),
    (str(ROOT / "steps" / "plot_core_timeline.py"), "steps"),
]

a = Analysis(
    ["run_app.py"],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=streamlit_hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="InboxArcheologyBackend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="InboxArcheologyBackend",
)