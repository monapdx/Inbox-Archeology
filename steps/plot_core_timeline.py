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


def plot_core_timeline(core_timeline_csv: str, save_path: str | None = None):
    def _plot_with_plotly(rows: list[dict], save_path_local: str | None = None) -> None:
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(
            {
                "email": [r["email"] for r in rows],
                "start": [r["start"] for r in rows],
                "end": [r["end"] for r in rows],
            }
        )
        fig = px.timeline(
            df,
            x_start="start",
            x_end="end",
            y="email",
            title="CORE Relationship Timeline",
        )
        fig.update_yaxes(visible=False)
        fig.update_layout(xaxis_title="Year")

        if save_path_local:
            sp = Path(save_path_local)
            sp.parent.mkdir(parents=True, exist_ok=True)
            note_path = sp.parent / f"{sp.stem}_png_export_failed.txt"
            try:
                fig.write_image(str(sp), scale=2)
                print(f"Saved plot to: {sp}")
                if note_path.exists():
                    note_path.unlink()
            except Exception as e:
                msg = (
                    f"Plotly static PNG export failed ({type(e).__name__}: {e}). "
                    "Ensure compatible plotly and kaleido are installed, or rely on Matplotlib when available. "
                    "Timeline charts in the Streamlit dashboard still work without this PNG."
                )
                note_path.write_text(msg + "\n", encoding="utf-8")
                print(msg)
        else:
            fig.show()

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

    if not rows:
        print(f"No CORE rows found in {core_timeline_csv}; skipping plot.")
        return

    try:
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except Exception:
        print("Using Plotly fallback renderer for timeline plot.")
        _plot_with_plotly(rows, save_path)
        return

    y_positions = range(len(rows))
    starts = [r["start"] for r in rows]
    # Convert datetimes to Matplotlib's float-day axis to avoid type
    # incompatibilities between datetime left values and integer widths.
    start_nums = mdates.date2num(starts)
    durations = [(r["end"] - r["start"]).days for r in rows]

    plt.figure(figsize=(12, max(6, len(rows) * 0.25)))
    plt.barh(y_positions, durations, left=start_nums)
    plt.xlabel("Year")
    plt.ylabel("CORE relationships (ordered by start date)")
    plt.title("CORE Relationship Timeline")
    plt.yticks([])  # keeps it emotionally light
    plt.gca().xaxis_date()
    plt.gca().xaxis.set_major_locator(mdates.YearLocator(2))
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    plt.gcf().autofmt_xdate()
    plt.tight_layout()

    if save_path:
        sp = Path(save_path)
        sp.parent.mkdir(parents=True, exist_ok=True)
        note_path = sp.parent / f"{sp.stem}_png_export_failed.txt"
        plt.savefig(sp, dpi=200)
        plt.close()
        print(f"Saved plot to: {sp}")
        if note_path.exists():
            note_path.unlink()
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
