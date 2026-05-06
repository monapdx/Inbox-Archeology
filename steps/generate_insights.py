#!/usr/bin/env python3
"""
CLI step: build deterministic insights JSON from relationships_clean.csv (+ optional core_timeline.csv).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inbox_archeology.insight_engine import generate_insights  # noqa: E402


def main() -> None:
    p = argparse.ArgumentParser(description="Generate insights.json from pipeline CSV outputs.")
    p.add_argument("--relationships", required=True, help="Path to relationships_clean.csv")
    p.add_argument(
        "--timeline",
        default="",
        help="Path to core_timeline.csv (optional; used if file exists)",
    )
    p.add_argument("--out", required=True, help="Output path for insights.json")
    args = p.parse_args()

    tl = args.timeline.strip() or None
    generate_insights(args.relationships, tl, args.out)


if __name__ == "__main__":
    main()
