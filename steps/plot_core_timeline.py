"""
Plot a horizontal bar chart for CORE relationships (from core_timeline.csv).

Refactor notes:
- Removed hardcoded path (CLI arg).
- Added optional --save to write a PNG instead of only showing a window.
"""

import argparse
import csv
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt


def plot_core_timeline(core_timeline_csv: str, save_path: str | None = None):
    rows = []
    with open(core_timeline_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "email": r["email"],
                "start": datetime.fromisoformat(r["start"]),
                "end": datetime.fromisoformat(r["end"]),
                "total": int(r["total_messages"]),
            })

    rows.sort(key=lambda r: r["start"])

    y_positions = range(len(rows))
    starts = [r["start"] for r in rows]
    durations = [(r["end"] - r["start"]).days for r in rows]

    plt.figure(figsize=(12, max(6, len(rows) * 0.25)))
    plt.barh(y_positions, durations, left=starts)
    plt.xlabel("Year")
    plt.ylabel("CORE relationships (ordered by start date)")
    plt.title("CORE Relationship Timeline")
    plt.yticks([])  # keeps it emotionally light
    plt.tight_layout()

    if save_path:
        sp = Path(save_path)
        sp.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(sp, dpi=200)
        print(f"Saved plot to: {sp}")
    else:
        plt.show()


def main():
    parser = argparse.ArgumentParser(description="Plot CORE timeline from core_timeline.csv")
    parser.add_argument("--in", dest="in_csv", default=str(Path("output") / "core_timeline.csv"))
    parser.add_argument("--save", default="", help="Optional path to save PNG (if omitted, shows window).")
    args = parser.parse_args()
    plot_core_timeline(args.in_csv, args.save or None)


if __name__ == "__main__":
    main()
