"""
Build core_timeline.csv from relationships_clean.csv (CORE relationships only).

Refactor notes:
- Removed hardcoded paths (CLI args).
- Logic unchanged.
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path

import _repo_root  # noqa: F401 — repo root on sys.path

from ia_constants import CORE_MESSAGE_THRESHOLD


def parse_dt(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def build_core_timeline_csv(in_path: str, out_path: str, core_min: int = CORE_MESSAGE_THRESHOLD):
    rows = []

    with open(in_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            total = int(r["total_messages"])
            if total < core_min:
                continue

            start = parse_dt(r.get("first_contact"))
            end = parse_dt(r.get("last_contact"))
            if not start or not end:
                continue

            duration_days = (end - start).days
            duration_years = round(duration_days / 365.25, 2)

            rows.append({
                "email": r["email"],
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
                "duration_days": duration_days,
                "duration_years": duration_years,
                "total_messages": total,
            })

    rows.sort(key=lambda r: r["start"])

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)

    with outp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "email",
                "start",
                "end",
                "duration_days",
                "duration_years",
                "total_messages",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"CORE timeline written to {outp}")
    print(f"CORE relationships: {len(rows)}")
    return str(outp)


def main():
    parser = argparse.ArgumentParser(description="Build CORE timeline CSV.")
    parser.add_argument("--in", dest="in_csv", default=str(Path("output") / "relationships_clean.csv"))
    parser.add_argument("--out", default=str(Path("output") / "core_timeline.csv"))
    parser.add_argument("--core-min", type=int, default=CORE_MESSAGE_THRESHOLD)
    args = parser.parse_args()
    build_core_timeline_csv(args.in_csv, args.out, args.core_min)


if __name__ == "__main__":
    main()
